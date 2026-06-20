from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from supabase import create_client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# FastAPI app
app = FastAPI(
    title="WS Quotation Engine",
    description="Insurance quotation API for WS",
    version="1.0.0"
)

# -------------------------
# HEALTH CHECK
# -------------------------

@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "WS Quotation API",
        "version": "1.0.0"
    }

# -------------------------
# REQUEST MODELS
# -------------------------

class MotorQuoteRequest(BaseModel):
    full_name: str
    phone_number: str
    email: EmailStr
    vehicle_source: str
    vehicle_value: float

# -------------------------
# MOTOR QUOTE ENDPOINT
# -------------------------

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
            raise HTTPException(
                status_code=400,
                detail="No quote returned"
            )

        return result.data[0]

    except Exception as e:
        print("ERROR:", str(e))
        raise HTTPException(
            status_code=500,
            detail=str(e)
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
            raise HTTPException(
                status_code=404,
                detail="Quote not found"
            )

        return result.data[0]

    except HTTPException:
        raise

    except Exception as e:
        print("ERROR:", str(e))
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )