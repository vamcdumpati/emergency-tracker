"""app/routers/contacts.py – Manage emergency contacts per user"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import EmergencyContactRequest, EmergencyContactResponse, MessageResponse
from app.db.client import supabase
from typing import List

router = APIRouter(prefix="/contacts", tags=["Emergency Contacts"])


@router.post("/{user_id}", response_model=MessageResponse, status_code=201)
async def add_contact(user_id: str, body: EmergencyContactRequest):
    """
    Add an emergency contact for a user.

    Flutter usage:
        POST /contacts/{user_id}
        { "name": "Mom", "phone": "9123456789" }
    """
    # Verify user exists
    user = supabase.table("users").select("id").eq("id", user_id).execute()
    if not user.data:
        raise HTTPException(status_code=404, detail="User not found")

    # Max 5 emergency contacts
    count = (
        supabase.table("emergency_contacts")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .execute()
    )
    if (count.count or 0) >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 emergency contacts allowed")

    row = {"user_id": user_id, "name": body.name, "phone": body.phone}
    result = supabase.table("emergency_contacts").insert(row).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to add contact")

    contact = result.data[0]
    return MessageResponse(
        message="Emergency contact added",
        data={"contact_id": contact["id"]},
    )


@router.get("/{user_id}", response_model=List[EmergencyContactResponse])
async def list_contacts(user_id: str):
    """Get all emergency contacts for a user."""
    result = (
        supabase.table("emergency_contacts")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )
    return [
        EmergencyContactResponse(
            id=c["id"], user_id=c["user_id"], name=c["name"], phone=c["phone"]
        )
        for c in result.data
    ]


@router.delete("/{contact_id}", response_model=MessageResponse)
async def delete_contact(contact_id: str):
    """Delete an emergency contact."""
    supabase.table("emergency_contacts").delete().eq("id", contact_id).execute()
    return MessageResponse(message="Contact deleted")
