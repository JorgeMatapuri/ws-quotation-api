from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from supabase import create_client
from dotenv import load_dotenv
import resend
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "onboarding@resend.dev")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
resend.api_key = RESEND_API_KEY

app = FastAPI(
    title="WS Quotation Engine",
    description="Insurance quotation API for WS",
    version="1.1.0"
)

class MotorQuoteRequest(BaseModel):
    full_name: str
    phone_number: str
    email: EmailStr
    vehicle_source: str
    vehicle_value: float

@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "WS Quotation API",
        "version": "1.1.0"
    }

def send_quote_email(customer_email: str, full_name: str, quote: dict):
    if not RESEND_API_KEY:
        return {"email_sent": False, "reason": "RESEND_API_KEY not configured"}

    status = quote.get("result_status")
    quote_ref = quote.get("result_quote_reference")
    annual = quote.get("result_annual_premium")
    monthly = quote.get("result_monthly_premium")
    message = quote.get("result_message")

    if status == "APPROVED":
        subject = f"Your WS Motor Insurance Quote - {quote_ref}"
        body = f"""
Hi {full_name},

Your motor insurance quotation is ready.

Quote Reference: {quote_ref}
Status: Approved
Annual Premium: P{annual}
Monthly Premium: P{monthly}

{message}

Regards,
WS Insurance
"""
    else:
        subject = f"WS Motor Insurance Referral - {quote_ref}"
        body = f"""
Hi {full_name},

Your motor insurance quotation requires underwriting review.

Quote Reference: {quote_ref}
Status: Referral Required

A WS representative will review your details and contact you.

Regards,
WS Insurance
"""

    return resend.Emails.send({
        "from": FROM_EMAIL,
        "to": customer_email,
        "subject": subject,
        "text": body
    })

@app.post("/motor-quote")
def motor_quote(request: MotorQuoteRequest):
    try:
        result = supabase.rpc(
            "create_motor_quote",
            {
                "p_full_name": request.full_name,
                "p_phone_number": request.phone_number,
                "p_email": request.email,
                "p_vehicle_source": request.vehicle_source,
                "p_vehicle_value": request.vehicle_value
            }
        ).execute()

        if not result.data:
            raise HTTPException(status_code=400, detail="No quote returned")

        quote = result.data[0]

        try:
            email_result = send_quote_email(
                customer_email=request.email,
                full_name=request.full_name,
                quote=quote
            )
        except Exception as email_error:
            email_result = {
                "email_sent": False,
                "error": str(email_error)
            }

        quote["email_notification"] = email_result

        return quote

    except Exception as e:
        print("ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quote/{quote_reference}")
def get_quote(quote_reference: str):
    try:
        result = (
            supabase
            .table("quotes")
            .select("*, customers(*)")
            .eq("quote_reference", quote_reference)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Quote not found")

        return result.data[0]

    except HTTPException:
        raise

    except Exception as e:
        print("ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))