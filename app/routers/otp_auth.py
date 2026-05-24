# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.firebase import verify_firebase_token
from app.db.client import supabase

router = APIRouter(prefix="/auth", tags=["OTP Auth"])

class OTPLoginRequest(BaseModel):
    firebase_id_token: str
    name: str | None = None

class OTPLoginResponse(BaseModel):
    user_id: str
    name: str
    phone: str
    is_new_user: bool
    message: str

@router.post("/otp-login", response_model=OTPLoginResponse)
async def otp_login(body: OTPLoginRequest):
    decoded = verify_firebase_token(body.firebase_id_token)
    phone = decoded.get("phone_number")
    firebase_uid = decoded.get("uid")

    if not phone:
        raise HTTPException(status_code=400, detail="Phone number not found in token")

    clean_phone = phone.replace("+91", "").replace("+", "")
    if clean_phone.startswith("91") and len(clean_phone) == 12:
        clean_phone = clean_phone[2:]

    existing = supabase.table("users").select("*").eq("phone", clean_phone).execute()

    if existing.data:
        user = existing.data[0]
        if user.get("role") != "care taker":
            raise HTTPException(status_code=403, detail="Access denied. Only care takers can login from the mobile app.")
        return OTPLoginResponse(user_id=user["id"], name=user["name"], phone=user["phone"], is_new_user=False, message="Login successful")

    raise HTTPException(status_code=404, detail="User not registered. Please contact your administrator to create your caretaker account.")
