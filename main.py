"""main.py – FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

from app.routers import auth, contacts, tracking

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Emergency Tracker API",
    description="Backend for Flutter emergency location sharing app",
    version="1.0.0",
)

# CORS – allow Flutter app (all origins for development; restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (map HTML page assets)
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(contacts.router)
app.include_router(tracking.router)

# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "Emergency Tracker API"}

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}


# ── Dev runner ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
