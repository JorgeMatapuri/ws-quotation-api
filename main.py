from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from supabase import create_client
from dotenv import load_dotenv
import resend
import os

# -------------------------
# ENVIRONMENT SETUP
# -------------------------

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "onboarding@resend.dev")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# -------------------------
# FASTAPI APP
# -------------------------

app = FastAPI(
    title="WS Quotation Engine",
    description="Multi-product insurance quotation API for WS",
    version="1.4.1"
)

# -------------------------
# CORS CONFIGURATION
# -------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://wsquote.netlify.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# REQUEST MODELS
# -------------------------

class MotorQuoteRequest(BaseModel):
    full_name: str
    phone_number: str
    email: EmailStr
    vehicle_source: str
    vehicle_value: float


class GPAQuoteRequest(BaseModel):
    full_name: str
    phone_number: str
    email: EmailStr
    tier_plan: str


class DomesticQuoteRequest(BaseModel):
    full_name: str
    phone_number: str
    email: EmailStr
    coverage_type: str
    sum_insured: float


class WCAQuoteRequest(BaseModel):
    full_name: str
    phone_number: str
    email: EmailStr
    annual_payroll: float


class CommercialVehicleQuoteRequest(BaseModel):
    full_name: str
    phone_number: str
    email: EmailStr
    commercial_class: str
    vehicle_value: float


class CommercialLDVHCVQuoteRequest(BaseModel):
    full_name: str
    phone_number: str
    email: EmailStr
    vehicle_category_bracket: str
    vehicle_value: float


class CommercialNonMotorQuoteRequest(BaseModel):
    full_name: str
    phone_number: str
    email: EmailStr
    module_name: str
    sum_insured: float


# -------------------------
# HEALTH CHECK
# -------------------------

@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "WS Quotation API",
        "version": "1.4.1"
    }


# -------------------------
# EMAIL FUNCTION
# -------------------------

def send_quote_email(customer_email: str, full_name: str, quote: dict):
    if not RESEND_API_KEY:
        return {
            "email_sent": False,
            "reason": "RESEND_API_KEY not configured"
        }

    status = quote.get("result_status")
    quote_ref = quote.get("result_quote_reference")
    annual = quote.get("result_annual_premium")
    monthly = quote.get("result_monthly_premium")
    message = quote.get("result_message")

    if status == "APPROVED":
        subject = f"Your WS Insurance Quote - {quote_ref}"
        body = f"""
Hi {full_name},

Your insurance quotation is ready.

Quote Reference: {quote_ref}
Status: Approved
Annual Premium: P{annual}
Monthly Premium: P{monthly}

{message}

Regards,
WS Insurance
"""
    else:
        subject = f"WS Insurance Referral - {quote_ref}"
        body = f"""
Hi {full_name},

Your insurance quotation requires underwriting review.

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


# -------------------------
# SHARED HELPER
# -------------------------

def attach_email_notification(quote: dict, request):
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


def call_quote_function(function_name: str, params: dict, request):
    try:
        result = supabase.rpc(function_name, params).execute()

        if not result.data:
            raise HTTPException(status_code=400, detail="No quote returned")

        return attach_email_notification(result.data[0], request)

    except HTTPException:
        raise

    except Exception as e:
        print("ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------
# QUOTE ENDPOINTS
# -------------------------

@app.post("/motor-quote")
def motor_quote(request: MotorQuoteRequest):
    return call_quote_function(
        "create_motor_quote",
        {
            "p_full_name": request.full_name,
            "p_phone_number": request.phone_number,
            "p_email": request.email,
            "p_vehicle_source": request.vehicle_source,
            "p_vehicle_value": request.vehicle_value
        },
        request
    )


@app.post("/gpa-quote")
def gpa_quote(request: GPAQuoteRequest):
    return call_quote_function(
        "create_gpa_quote",
        {
            "p_full_name": request.full_name,
            "p_phone_number": request.phone_number,
            "p_email": request.email,
            "p_tier_plan": request.tier_plan
        },
        request
    )


@app.post("/domestic-quote")
def domestic_quote(request: DomesticQuoteRequest):
    return call_quote_function(
        "create_domestic_quote",
        {
            "p_full_name": request.full_name,
            "p_phone_number": request.phone_number,
            "p_email": request.email,
            "p_coverage_type": request.coverage_type,
            "p_sum_insured": request.sum_insured
        },
        request
    )


@app.post("/wca-quote")
def wca_quote(request: WCAQuoteRequest):
    return call_quote_function(
        "create_wca_quote",
        {
            "p_full_name": request.full_name,
            "p_phone_number": request.phone_number,
            "p_email": request.email,
            "p_annual_payroll": request.annual_payroll
        },
        request
    )


@app.post("/commercial-vehicle-quote")
def commercial_vehicle_quote(request: CommercialVehicleQuoteRequest):
    return call_quote_function(
        "create_commercial_vehicle_quote",
        {
            "p_full_name": request.full_name,
            "p_phone_number": request.phone_number,
            "p_email": request.email,
            "p_commercial_class": request.commercial_class,
            "p_vehicle_value": request.vehicle_value
        },
        request
    )


@app.post("/commercial-ldv-hcv-quote")
def commercial_ldv_hcv_quote(request: CommercialLDVHCVQuoteRequest):
    return call_quote_function(
        "create_commercial_ldv_hcv_quote",
        {
            "p_full_name": request.full_name,
            "p_phone_number": request.phone_number,
            "p_email": request.email,
            "p_vehicle_category_bracket": request.vehicle_category_bracket,
            "p_vehicle_value": request.vehicle_value
        },
        request
    )


@app.post("/commercial-non-motor-quote")
def commercial_non_motor_quote(request: CommercialNonMotorQuoteRequest):
    return call_quote_function(
        "create_commercial_non_motor_quote",
        {
            "p_full_name": request.full_name,
            "p_phone_number": request.phone_number,
            "p_email": request.email,
            "p_module_name": request.module_name,
            "p_sum_insured": request.sum_insured
        },
        request
    )


# -------------------------
# QUOTE LOOKUP ENDPOINT
# -------------------------

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