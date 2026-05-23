import os, secrets
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.db.client import supabase
from app.services.sms import send_tracking_sms

router = APIRouter(prefix="/patient", tags=["Patient"])
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

class PatientIntakeRequest(BaseModel):
    full_name: str
    dob: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    mobile: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    identity_card_url: Optional[str] = None
    portrait_url: Optional[str] = None
    hospital_name: Optional[str] = None
    location_address: Optional[str] = None
    emergency_contact: str
    caretaker_name: Optional[str] = None
    caretaker_phone: Optional[str] = None
    caretaker_lat: Optional[float] = None
    caretaker_lng: Optional[float] = None

class PatientIntakeResponse(BaseModel):
    patient_id: str
    session_id: str
    tracking_url: str
    sms_sent_to_emergency: bool
    sms_sent_to_caretaker: bool
    message: str

@router.post("/intake", response_model=PatientIntakeResponse, status_code=201)
async def patient_intake(body: PatientIntakeRequest):
    token = secrets.token_urlsafe(16)
    session_res = supabase.table("tracking_sessions").insert({"token": token, "user_id": None}).execute()
    if not session_res.data:
        raise HTTPException(status_code=500, detail="Could not create tracking session")
    session_id = session_res.data[0]["id"]
    tracking_url = f"{BASE_URL}/track/{token}"
    if body.caretaker_lat and body.caretaker_lng:
        supabase.table("locations").insert({"session_id": session_id, "latitude": body.caretaker_lat, "longitude": body.caretaker_lng}).execute()
    patient_row = {
        "full_name": body.full_name, "dob": body.dob, "age": body.age,
        "gender": body.gender, "mobile": body.mobile, "height_cm": body.height_cm,
        "weight_kg": body.weight_kg, "hospital_name": body.hospital_name,
        "location_address": body.location_address, "emergency_contact": body.emergency_contact,
        "caretaker_lat": body.caretaker_lat, "caretaker_lng": body.caretaker_lng,
        "identity_card_url": body.identity_card_url, "portrait_url": body.portrait_url,
        "session_id": session_id,
    }
    patient_res = supabase.table("patients").insert(patient_row).execute()
    if not patient_res.data:
        raise HTTPException(status_code=500, detail="Failed to save patient details")
    patient_id = patient_res.data[0]["id"]
    emergency_sms = await send_tracking_sms(
        to_phone=body.emergency_contact,
        sender_name=body.caretaker_name or "Caretaker",
        tracking_url=tracking_url,
        patient_name=body.full_name,
        hospital_name=body.hospital_name,
        message_type="emergency",
    )
    caretaker_sms = False
    if body.caretaker_phone:
        caretaker_sms = await send_tracking_sms(
            to_phone=body.caretaker_phone,
            sender_name="Hey Buddy App",
            tracking_url=tracking_url,
            patient_name=body.full_name,
            hospital_name=body.hospital_name,
            message_type="caretaker",
        )
    return PatientIntakeResponse(
        patient_id=patient_id, session_id=session_id, tracking_url=tracking_url,
        sms_sent_to_emergency=emergency_sms, sms_sent_to_caretaker=caretaker_sms,
        message="Patient saved and alerts sent successfully",
    )

@router.get("/{patient_id}")
async def get_patient(patient_id: str):
    result = supabase.table("patients").select("*").eq("id", patient_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Patient not found")
    return result.data[0]

@router.post("/session/{session_id}/stop")
async def stop_patient_session(session_id: str):
    supabase.table("tracking_sessions").update({"is_active": False}).eq("id", session_id).execute()
    return {"message": "Patient has reached the hospital. Tracking stopped."}
