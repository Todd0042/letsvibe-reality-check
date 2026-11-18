"""FastAPI router for LetsVibe: Reality Check."""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, Field

from .evaluator import evaluate_idea, generate_idea_batch_llama, get_lock_status, normalize_tone
from .html_export import render_rc_standalone_html
from .idea_finder import run_idea_finder
from .storage import RealityCheckStore

router = APIRouter()
_store = RealityCheckStore()
_jobs_lock = threading.Lock()
_jobs: Dict[str, Dict[str, Any]] = {}
_rate_lock = threading.Lock()
_ip_hits: Dict[str, List[float]] = defaultdict(list)

_ALLOWED_PLATFORMS = {"Web", "Android", "iOS", "Desktop", "CLI", "SaaS / API"}
_RATE_WINDOW_SEC = 600.0
_RATE_MAX_HITS = int(os.getenv("LETSVIBE_RC_RATE_LIMIT", "10"))


class RealityCheckRequest(BaseModel):
    pitch: str = Field(..., min_length=15, max_length=1500)
    platform: str = Field("Web", max_length=32)
    twist: str = Field("", max_length=600)
    tone: str = Field("realistic", max_length=16)


class IdeaFinderRequest(BaseModel):
    interests: str = Field("", max_length=600)
    platform: str = Field("Web", max_length=32)


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("cf-connecting-ip") or request.headers.get("x-forwarded-for") or ""
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(ip: str) -> None:
    if _RATE_MAX_HITS <= 0:
        return
    now = time.monotonic()
    with _rate_lock:
        recent = [t for t in _ip_hits[ip] if now - t < _RATE_WINDOW_SEC]
        if len(recent) >= _RATE_MAX_HITS:
            raise HTTPException(
                status_code=429,
                detail="Rate limit reached for Reality Check. Please wait a few minutes before submitting another idea.",
            )
        recent.append(now)
        _ip_hits[ip] = recent


def _render_rc_page(preloaded_report: Dict[str, Any] | None = None) -> HTMLResponse:
    tmpl_path = Path(__file__).resolve().parent / "templates" / "reality_check.html"
    html_text = tmpl_path.read_text(encoding="utf-8")
    preload_json = json.dumps(preloaded_report, ensure_ascii=False).replace("</", "<\\/") if preloaded_report else "null"
    html_text = html_text.replace("__PRELOADED_REPORT_JSON__", preload_json)
    return HTMLResponse(html_text)


@router.get("/", response_class=HTMLResponse)
@router.get("/rc", response_class=HTMLResponse)
async def rc_home() -> HTMLResponse:
    return _render_rc_page()


@router.get("/rc/r/{report_id}", response_class=HTMLResponse)
@router.get("/r/{report_id}", response_class=HTMLResponse)
async def rc_shared_report(report_id: str) -> HTMLResponse:
    rep = _store.get_report(report_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Reality Check report not found.")
    return _render_rc_page(rep)


@router.get("/api/health")
async def rc_health() -> JSONResponse:
    return JSONResponse({"status": "online"})


@router.get("/api/rc/status")
async def rc_status() -> JSONResponse:
    return JSONResponse({"lock": get_lock_status()})


@router.post("/api/rc/evaluate")
async def rc_evaluate(req: RealityCheckRequest, request: Request) -> JSONResponse:
    _check_rate_limit(_client_ip(request))
    pitch = req.pitch.strip()
    if len(pitch) < 15:
        raise HTTPException(status_code=400, detail="Please describe your app idea in at least 15 characters.")
    platform = req.platform.strip() if req.platform.strip() in _ALLOWED_PLATFORMS else "Web"
    twist = req.twist.strip()
    tone = normalize_tone(req.tone)

    job_id = uuid.uuid4().hex[:12]
    with _jobs_lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress_pct": 5,
            "message": "Queued for Reality Check...",
            "report_id": None,
            "report": None,
            "error": None,
        }

    def _run() -> None:
        def on_prog(msg: str, pct: int) -> None:
            with _jobs_lock:
                if job_id in _jobs:
                    _jobs[job_id]["status"] = "running"
                    _jobs[job_id]["progress_pct"] = pct
                    _jobs[job_id]["message"] = msg

        try:
            report = evaluate_idea(
                pitch=pitch,
                platform=platform,
                twist=twist,
                tone=tone,
                job_id=job_id,
                on_progress=on_prog,
            )
            report_id = _store.save_report(report)
            report["id"] = report_id
            with _jobs_lock:
                _jobs[job_id]["status"] = "completed"
                _jobs[job_id]["progress_pct"] = 100
                _jobs[job_id]["message"] = "Reality Check complete."
                _jobs[job_id]["report_id"] = report_id
                _jobs[job_id]["report"] = report
        except Exception as exc:  # noqa: BLE001
            with _jobs_lock:
                _jobs[job_id]["status"] = "failed"
                _jobs[job_id]["error"] = str(exc)
                _jobs[job_id]["message"] = f"Failed: {exc}"

    threading.Thread(target=_run, daemon=True).start()
    return JSONResponse({"job_id": job_id, "status": "queued"})


@router.post("/api/rc/find-idea")
async def rc_find_idea(req: IdeaFinderRequest, request: Request) -> JSONResponse:
    _check_rate_limit(_client_ip(request))
    interests = req.interests.strip()
    platform = req.platform.strip() if req.platform.strip() in _ALLOWED_PLATFORMS else "Web"

    job_id = uuid.uuid4().hex[:12]
    with _jobs_lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress_pct": 5,
            "message": "Queued for Idea Finder...",
            "report_id": None,
            "report": None,
            "finder_result": None,
            "error": None,
        }

    def _run() -> None:
        def on_prog(msg: str, pct: int) -> None:
            with _jobs_lock:
                if job_id in _jobs:
                    _jobs[job_id]["status"] = "running"
                    _jobs[job_id]["progress_pct"] = pct
                    _jobs[job_id]["message"] = msg

        try:
            res = run_idea_finder(
                generate_json_fn=lambda sp, up: generate_idea_batch_llama(sp, up, job_id=job_id),
                evaluate_brutal_fn=lambda p, plat, tw: evaluate_idea(
                    pitch=p,
                    platform=plat,
                    twist=tw,
                    tone="realistic",
                    job_id=job_id,
                ),
                interests=interests,
                platform=platform,
                max_cycles=3,
                on_progress=on_prog,
            )
            winning_report = res["winning_report"]
            report_id = _store.save_report(winning_report)
            winning_report["id"] = report_id
            with _jobs_lock:
                _jobs[job_id]["status"] = "completed"
                _jobs[job_id]["progress_pct"] = 100
                _jobs[job_id]["message"] = "Idea Finder complete."
                _jobs[job_id]["report_id"] = report_id
                _jobs[job_id]["report"] = winning_report
                _jobs[job_id]["finder_result"] = res
        except Exception as exc:  # noqa: BLE001
            with _jobs_lock:
                _jobs[job_id]["status"] = "failed"
                _jobs[job_id]["error"] = str(exc)
                _jobs[job_id]["message"] = f"Failed: {exc}"

    threading.Thread(target=_run, daemon=True).start()
    return JSONResponse({"job_id": job_id, "status": "queued"})


@router.get("/api/rc/job/{job_id}")
async def rc_job_status(job_id: str) -> JSONResponse:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")
        payload = dict(job)
    payload["lock"] = get_lock_status()
    return JSONResponse(payload)


@router.get("/api/rc/report/{report_id}")
async def rc_get_report(report_id: str) -> JSONResponse:
    rep = _store.get_report(report_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Report not found.")
    return JSONResponse({"status": "ok", "report": rep})


@router.get("/api/rc/report/{report_id}/html")
async def rc_export_html(report_id: str) -> Response:
    rep = _store.get_report(report_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Report not found.")
    html_out = render_rc_standalone_html(rep)
    return Response(
        content=html_out,
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="letsvibe-rc-{report_id}.html"'},
    )
