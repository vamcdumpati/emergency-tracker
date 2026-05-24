"""app/models/schemas.py – Request / Response schemas"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import re


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = ["super admin", "admin", "care taker"]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # Accept 10-digit Indian numbers (with optional +91 or 0 prefix)
        cleaned = re.sub(r"[\s\-()]", "", v)
        cleaned = re.sub(r"^(\+91|91|0)", "", cleaned)
        if not re.fullmatch(r"[6-9]\d{9}", cleaned):
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return cleaned

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    role: str


# ── Emergency Contact ─────────────────────────────────────────────────────────

class EmergencyContactRequest(BaseModel):
    name: str
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"[\s\-()]", "", v)
        cleaned = re.sub(r"^(\+91|91|0)", "", cleaned)
        if not re.fullmatch(r"[6-9]\d{9}", cleaned):
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return cleaned


class EmergencyContactResponse(BaseModel):
    id: str
    user_id: str
    name: str
    phone: str


# ── Location ──────────────────────────────────────────────────────────────────

class LocationPayload(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None

    @field_validator("latitude")
    @classmethod
    def lat_range(cls, v: float) -> float:
        if not -90 <= v <= 90:
            raise ValueError("Latitude out of range")
        return v

    @field_validator("longitude")
    @classmethod
    def lon_range(cls, v: float) -> float:
        if not -180 <= v <= 180:
            raise ValueError("Longitude out of range")
        return v


# ── SOS / Alert ───────────────────────────────────────────────────────────────

class SOSRequest(BaseModel):
    user_id: str
    initial_location: LocationPayload


class SOSResponse(BaseModel):
    session_id: str
    tracking_url: str
    contacts_notified: int


# ── Generic ───────────────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    data: Optional[dict] = None
