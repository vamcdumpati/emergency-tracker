"""app/services/ws_manager.py – Manage live WebSocket connections per session"""

from fastapi import WebSocket
from typing import Dict, List
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Keeps track of:
      - One sender WebSocket per session  (the Flutter app streaming GPS)
      - Many viewer WebSockets per session (emergency contacts watching the map)

    When the sender pushes a new location, it is broadcast to all viewers.
    """

    def __init__(self):
        # session_id → WebSocket of the Flutter app
        self.senders: Dict[str, WebSocket] = {}
        # session_id → list of viewer WebSockets (browser map pages)
        self.viewers: Dict[str, List[WebSocket]] = {}

    # ── Sender (Flutter app) ──────────────────────────────────────────────────

    async def connect_sender(self, session_id: str, ws: WebSocket):
        await ws.accept()
        self.senders[session_id] = ws
        logger.info("Sender connected: session=%s", session_id)

    def disconnect_sender(self, session_id: str):
        self.senders.pop(session_id, None)
        logger.info("Sender disconnected: session=%s", session_id)

    # ── Viewer (browser map) ──────────────────────────────────────────────────

    async def connect_viewer(self, session_id: str, ws: WebSocket):
        await ws.accept()
        self.viewers.setdefault(session_id, []).append(ws)
        logger.info("Viewer connected: session=%s  total=%d",
                    session_id, len(self.viewers[session_id]))

    def disconnect_viewer(self, session_id: str, ws: WebSocket):
        viewers = self.viewers.get(session_id, [])
        if ws in viewers:
            viewers.remove(ws)
        logger.info("Viewer disconnected: session=%s  remaining=%d",
                    session_id, len(viewers))

    # ── Broadcast ─────────────────────────────────────────────────────────────

    async def broadcast_location(self, session_id: str, data: dict):
        """Send location JSON to all viewers watching this session."""
        viewers = self.viewers.get(session_id, [])
        dead: List[WebSocket] = []

        for ws in viewers:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)

        # Clean up broken connections
        for ws in dead:
            self.disconnect_viewer(session_id, ws)


# Singleton shared across the app
manager = ConnectionManager()
