"""app/routers/tracking.py – SOS alert + live location streaming"""

import os, secrets, json
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from app.models.schemas import SOSRequest, SOSResponse, LocationPayload, MessageResponse
from app.db.client import supabase
from app.services.sms import send_tracking_sms
from app.services.ws_manager import manager
from pathlib import Path

router = APIRouter(tags=["Tracking"])
public_router = APIRouter(tags=["Tracking"])

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")


# ── 1. Trigger SOS ────────────────────────────────────────────────────────────

@router.post("/sos", response_model=SOSResponse, status_code=201)
async def trigger_sos(body: SOSRequest):
    """
    Called by the Flutter app when user presses the SOS button.

    Steps:
      1. Create a tracking session with a unique token
      2. Save the initial location
      3. Send SMS with tracking link to ALL emergency contacts
      4. Return the tracking URL (Flutter keeps streaming to /ws/location/{session_id})
    """
    # Verify user
    user_res = (
        supabase.table("users")
        .select("name, phone")
        .eq("id", body.user_id)
        .execute()
    )
    if not user_res.data:
        raise HTTPException(status_code=404, detail="User not found")
    user = user_res.data[0]

    # Create tracking session
    token = secrets.token_urlsafe(16)
    session_res = supabase.table("tracking_sessions").insert(
        {"user_id": body.user_id, "token": token}
    ).execute()

    if not session_res.data:
        raise HTTPException(status_code=500, detail="Could not create tracking session")

    session_id = session_res.data[0]["id"]

    # Save initial location
    supabase.table("locations").insert({
        "session_id": session_id,
        "latitude": body.initial_location.latitude,
        "longitude": body.initial_location.longitude,
        "accuracy": body.initial_location.accuracy,
    }).execute()

    # Build public tracking URL
    tracking_url = f"{BASE_URL}/track/{token}"

    # Fetch emergency contacts and send SMS
    contacts_res = (
        supabase.table("emergency_contacts")
        .select("name, phone")
        .eq("user_id", body.user_id)
        .execute()
    )

    notified = 0
    for contact in (contacts_res.data or []):
        sent = await send_tracking_sms(
            to_phone=contact["phone"],
            sender_name=user["name"],
            tracking_url=tracking_url,
        )
        if sent:
            notified += 1

    return SOSResponse(
        session_id=session_id,
        tracking_url=tracking_url,
        contacts_notified=notified,
    )


# ── 2. Stop SOS session ───────────────────────────────────────────────────────

@router.post("/sos/{session_id}/stop", response_model=MessageResponse)
async def stop_sos(session_id: str):
    """Mark a session as inactive (user is safe)."""
    supabase.table("tracking_sessions").update(
        {"is_active": False}
    ).eq("id", session_id).execute()
    return MessageResponse(message="SOS session stopped. You are marked safe.")


# ── 3. Flutter → WebSocket: stream GPS to backend ────────────────────────────

@router.websocket("/ws/location/{session_id}")
async def location_sender(ws: WebSocket, session_id: str):
    """
    Flutter app connects here and pushes location updates as JSON:
        { "latitude": 17.385, "longitude": 78.486, "accuracy": 12.5 }

    The backend:
      • Saves each point to Supabase
      • Broadcasts to all browser viewers watching this session
    """
    # Validate session
    session = (
        supabase.table("tracking_sessions")
        .select("id, is_active")
        .eq("id", session_id)
        .execute()
    )
    if not session.data or not session.data[0]["is_active"]:
        await ws.close(code=4004)
        return

    await manager.connect_sender(session_id, ws)
    try:
        while True:
            raw = await ws.receive_text()
            try:
                payload = json.loads(raw)
                loc = LocationPayload(**payload)
            except Exception:
                await ws.send_text('{"error": "Invalid payload"}')
                continue

            # Persist to DB
            supabase.table("locations").insert({
                "session_id": session_id,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "accuracy": loc.accuracy,
            }).execute()

            # Push to all map viewers
            await manager.broadcast_location(session_id, {
                "lat": loc.latitude,
                "lng": loc.longitude,
                "accuracy": loc.accuracy,
            })

    except WebSocketDisconnect:
        manager.disconnect_sender(session_id)


# ── 4. Browser → WebSocket: viewer listens for updates ───────────────────────

@public_router.websocket("/ws/view/{session_id}")
async def location_viewer(ws: WebSocket, session_id: str):
    """
    The browser map page connects here to receive live location updates.
    """
    await manager.connect_viewer(session_id, ws)
    try:
        while True:
            # Keep alive; viewers only receive, never send
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_viewer(session_id, ws)


# ── 5. Public tracking page (opens in emergency contact's browser) ────────────

@public_router.get("/track/{token}", response_class=HTMLResponse)
async def tracking_page(token: str):
    """
    Public URL sent to emergency contacts via SMS.
    Renders a live map using Leaflet.js (no API key needed).
    """
    # Resolve token → session
    session_res = (
        supabase.table("tracking_sessions")
        .select("id, is_active, user_id, expires_at")
        .eq("token", token)
        .execute()
    )
    if not session_res.data:
        return HTMLResponse("<h2>Link not found or expired.</h2>", status_code=404)

    session = session_res.data[0]

    # Fetch user name
    user_res = (
        supabase.table("users")
        .select("name")
        .eq("id", session["user_id"])
        .execute()
    )
    user_name = user_res.data[0]["name"] if user_res.data else "Someone"

    # Latest known location for initial map center
    loc_res = (
        supabase.table("locations")
        .select("latitude, longitude")
        .eq("session_id", session["id"])
        .order("recorded_at", desc=True)
        .limit(1)
        .execute()
    )
    last = loc_res.data[0] if loc_res.data else {"latitude": 17.385, "longitude": 78.486}

    active_status = "LIVE" if session["is_active"] else "ENDED"

    # Read the map HTML template
    template_path = Path(__file__).parent.parent.parent / "static" / "track" / "map.html"
    html_template = template_path.read_text()

    html = (
        html_template
        .replace("{{SESSION_ID}}", session["id"])
        .replace("{{USER_NAME}}", user_name)
        .replace("{{INIT_LAT}}", str(last["latitude"]))
        .replace("{{INIT_LNG}}", str(last["longitude"]))
        .replace("{{STATUS}}", active_status)
        .replace("{{BASE_URL}}", BASE_URL.replace("https://", "wss://").replace("http://", "ws://"))
    )
    return HTMLResponse(html)
