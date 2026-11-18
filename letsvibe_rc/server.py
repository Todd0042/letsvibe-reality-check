"""Standalone FastAPI ASGI entrypoint for LetsVibe: Reality Check."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routes import router as rc_router

app = FastAPI(title="LetsVibe: Reality Check", version="1.0.0")

_static_dir = Path(__file__).resolve().parent / "static"
if _static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

app.include_router(rc_router)
