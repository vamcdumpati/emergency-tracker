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
        return OTPLoginResponse(user_id=user["id"], name=user["name"], phone=user["phone"], is_new_user=False, message="Login successful")

    name = body.name or f"User_{clean_phone[-4:]}"
    new_user = {"name": name, "email": f"{firebase_uid}@firebase.placeholder", "phone": clean_phone, "password_hash": f"firebase:{firebase_uid}"}
    result = supabase.table("users").insert(new_user).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create user")

    user = result.data[0]
    return OTPLoginResponse(user_id=user["id"], name=user["name"], phone=user["phone"], is_new_user=True, message="Account created successfully")
