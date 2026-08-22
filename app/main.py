from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import api_router
from app.core.config import get_settings

app = FastAPI(title="English Trainer API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)

# Batch-generated lesson/placement listening audio (scripts/generate_audio.py)
# — served at the app root, not under /api/v1, so the frontend can point an
# <audio> element straight at it. The directory may not exist until that
# script has run at least once; check_dir=False keeps that from crashing
# startup on a fresh checkout.
AUDIO_DIR = Path(__file__).resolve().parent.parent / "content" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")
