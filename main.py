from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="WS Quotation Engine")

class MotorQuoteRequest(BaseModel):
    full_name: str
    phone_number: str
    email: EmailStr
    vehicle_source: str
    vehicle_value: float

@app.get("/")
def home():
    return {"message": "WS Quotation Engine Running"}

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

        return result.data[0]

    except Exception as e:
        print("ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))

        @app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "WS Quotation API"
    }