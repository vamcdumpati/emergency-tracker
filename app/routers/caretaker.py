from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.db.client import supabase

router = APIRouter(prefix="/caretaker", tags=["Caretaker"])

class CaretakerRegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    mobile: str

class CaretakerResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    mobile: str
    message: str

@router.post("/register", response_model=CaretakerResponse, status_code=201)
async def register_caretaker(body: CaretakerRegisterRequest):
    existing = supabase.table("caretakers").select("id").eq("email", body.email).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Email already registered")
    result = supabase.table("caretakers").insert({
        "first_name": body.first_name,
        "last_name": body.last_name,
        "email": body.email,
        "mobile": body.mobile,
    }).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Registration failed")
    c = result.data[0]
    return CaretakerResponse(id=c["id"], first_name=c["first_name"], last_name=c["last_name"], email=c["email"], mobile=c["mobile"], message="Caretaker registered successfully")

@router.get("/{caretaker_id}", response_model=CaretakerResponse)
async def get_caretaker(caretaker_id: str):
    result = supabase.table("caretakers").select("*").eq("id", caretaker_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Caretaker not found")
    c = result.data[0]
    return CaretakerResponse(id=c["id"], first_name=c["first_name"], last_name=c["last_name"], email=c["email"], mobile=c["mobile"], message="")
