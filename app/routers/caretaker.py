# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db.client import supabase

router = APIRouter(prefix="/caretaker", tags=["Caretaker"])

class CaretakerResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    mobile: str
    message: str

@router.get("/{caretaker_id}", response_model=CaretakerResponse)
async def get_caretaker(caretaker_id: str):
    result = supabase.table("caretakers").select("*").eq("id", caretaker_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Caretaker not found")
    c = result.data[0]
    return CaretakerResponse(id=c["id"], first_name=c["first_name"], last_name=c["last_name"], email=c["email"], mobile=c["mobile"], message="")
