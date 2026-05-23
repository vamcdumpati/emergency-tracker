"""app/routers/auth.py – /register and /login endpoints"""

import hashlib, os
from fastapi import APIRouter, HTTPException
from app.models.schemas import RegisterRequest, LoginRequest, UserResponse, MessageResponse
from app.db.client import supabase

router = APIRouter(prefix="/auth", tags=["Auth"])


def _hash_password(password: str) -> str:
    """Simple SHA-256 hash. For production, use bcrypt via passlib."""
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("/register", response_model=MessageResponse, status_code=201)
async def register(body: RegisterRequest):
    """
    Register a new user.

    Flutter usage:
        POST /auth/register
        {
          "name": "Rahul",
          "email": "rahul@example.com",
          "phone": "9876543210",
          "password": "secret123"
        }
    """
    # Check duplicate email
    existing = (
        supabase.table("users")
        .select("id")
        .eq("email", body.email)
        .execute()
    )
    if existing.data:
        raise HTTPException(status_code=409, detail="Email already registered")

    row = {
        "name": body.name,
        "email": body.email,
        "phone": body.phone,
        "password_hash": _hash_password(body.password),
    }

    result = supabase.table("users").insert(row).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Registration failed")

    user = result.data[0]
    return MessageResponse(
        message="User registered successfully",
        data={"user_id": user["id"], "name": user["name"]},
    )


@router.post("/login", response_model=MessageResponse)
async def login(body: LoginRequest):
    """
    Login and get user_id.
    (In production, return a JWT instead.)
    """
    result = (
        supabase.table("users")
        .select("*")
        .eq("email", body.email)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = result.data[0]
    if user["password_hash"] != _hash_password(body.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return MessageResponse(
        message="Login successful",
        data={
            "user_id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "phone": user["phone"],
        },
    )


@router.get("/user/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    result = (
        supabase.table("users")
        .select("id, name, email, phone")
        .eq("id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")

    u = result.data[0]
    return UserResponse(id=u["id"], name=u["name"], email=u["email"], phone=u["phone"])
