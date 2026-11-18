"""Standalone E2E tests for LetsVibe: Reality Check & Idea Finder."""

from __future__ import annotations

import time
from typing import List

from fastapi.testclient import TestClient

from letsvibe_rc import evaluator as rc_eval
from letsvibe_rc import routes as rc_routes
from letsvibe_rc.server import app


def test_reality_check_e2e_and_xss_escape(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(rc_routes, "_store", rc_routes.RealityCheckStore(str(tmp_path / "rc.db")))
    monkeypatch.setattr(rc_routes, "_RATE_MAX_HITS", 20)
    monkeypatch.setattr(
        rc_eval,
        "gather_market_grounding",
        lambda pitch, platform="Web", twist="": {
            "keywords": ["todo", "task"],
            "query": "todo task",
            "platform": platform,
            "github_top_repos": [],
            "app_store_hits": [],
        },
    )

    captured: List[str] = []

    def fake_llama(system_prompt: str, user_prompt: str, max_tokens: int = 4096, temperature: float = 0.25):
        captured.append(user_prompt)
        return {
            "verdict": "DO NOT BUILD",
            "headline": "Crowded TODO Wrapper",
            "viability_score": 1.8,
            "saturation_pct": 95.0,
            "demand_tier": "Wrapper Slop",
            "wasted_hours_estimate": "40 hrs",
            "wasted_tokens_estimate": "200k tokens",
            "executive_summary": "Thousands exist.",
            "dimensions": {
                "market_saturation": {"label": "Market Saturation", "score": 1.0, "weight": 100, "reasoning": "Saturated."},
            },
            "existing_competitors": [{"name": "Todoist", "type": "Paid SaaS", "why_it_wins": "Mature."}],
            "fatal_flaws": ["Extreme saturation", "<script>alert(1)</script>"],
            "redeeming_angles": ["Learning project"],
            "pivots": [],
            "pricing_recommendation": {"suggested_price": "Do Not Monetize", "model": "Do Not Monetize", "reasoning": "Free."},
            "marketing_playbook": {"difficulty": "Brutal", "where_buyers_hang_out": ["r/productivity"], "biggest_distribution_trap": "Dev forums", "distribution_channels": []},
            "liability_and_entity": {"recommendation": "Personal / Indie", "risk_level": "Low", "reasoning": "Low risk.", "must_have_protections": ["AS-IS Terms"]},
        }

    monkeypatch.setattr(rc_eval, "_call_shared_llama", fake_llama)
    client = TestClient(app)

    assert client.get("/api/health").json() == {"status": "online"}
    home = client.get("/")
    assert home.status_code == 200
    assert "LetsVibe: Reality Check" in home.text
    assert 'value="whisper">Whisper Sweet Nothings<' in home.text

    sub = client.post(
        "/api/rc/evaluate",
        json={
            "pitch": "An AI-powered daily task manager with dark mode <script>alert(1)</script>",
            "platform": "Web",
            "twist": "Dark mode",
            "tone": "whisper",
        },
    )
    assert sub.status_code == 200
    job_id = sub.json()["job_id"]

    report_id = None
    for _ in range(30):
        jr = client.get(f"/api/rc/job/{job_id}").json()
        if jr["status"] == "completed":
            report_id = jr["report_id"]
            assert jr["report"]["tone"] == "whisper"
            break
        time.sleep(0.05)
    assert report_id
    assert any("WHISPER SWEET NOTHINGS" in p for p in captured)

    dl = client.get(f"/api/rc/report/{report_id}/html")
    assert dl.status_code == 200
    assert "<script>alert(1)</script>" not in dl.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in dl.text


def test_idea_finder_3_day_history_and_gate(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("LETSVIBE_RC_IDEA_HISTORY_PATH", str(tmp_path / "idea_hist.json"))
    monkeypatch.setattr(rc_routes, "_store", rc_routes.RealityCheckStore(str(tmp_path / "rc_if.db")))
    monkeypatch.setattr(rc_routes, "_RATE_MAX_HITS", 20)
    monkeypatch.setattr(rc_eval, "gather_market_grounding", lambda pitch, platform="Web", twist="": {"query": "test", "github_top_repos": [], "app_store_hits": []})
    monkeypatch.setattr(
        rc_routes,
        "generate_idea_batch_llama",
        lambda sp, up, job_id="": {
            "candidates": [
                {"title": "Cliché Wrapper", "pitch": "A generic AI note taker for everyone online.", "twist": "Dark mode", "target_buyer": "Anyone", "why_monetizable": "Subs"},
                {"title": "Offline Track Telemetry", "pitch": "An offline laptop pit-lane lap & tire-temp logger for Miata track-day drivers.", "twist": "Local Wi-Fi OBD2", "target_buyer": "Track-day drivers", "why_monetizable": "Replaces $49/mo cloud"},
            ]
        },
    )

    calls = {"n": 0}

    def fake_gate(system_prompt: str, user_prompt: str, max_tokens: int = 4096, temperature: float = 0.25):
        calls["n"] += 1
        if calls["n"] == 1:
            return {
                "verdict": "DO NOT BUILD",
                "headline": "Wrapper slop",
                "viability_score": 2.0,
                "saturation_pct": 90.0,
                "demand_tier": "Wrapper Slop",
                "dimensions": {"market_saturation": {"label": "Sat", "score": 2.0, "weight": 100, "reasoning": "Bad"}},
                "pricing_recommendation": {"suggested_price": "Do Not Monetize", "model": "Do Not Monetize", "reasoning": "No"},
            }
        return {
            "verdict": "ACTUALLY VIABLE",
            "headline": "Focused offline pit-lane logger",
            "viability_score": 7.6,
            "saturation_pct": 18.0,
            "demand_tier": "Underserved Pain",
            "dimensions": {"market_saturation": {"label": "Sat", "score": 7.6, "weight": 100, "reasoning": "Good"}},
            "pricing_recommendation": {"suggested_price": "$49 one-time", "model": "One-Time License", "reasoning": "Fair"},
        }

    monkeypatch.setattr(rc_eval, "_call_shared_llama", fake_gate)
    client = TestClient(app)
    sub = client.post("/api/rc/find-idea", json={"interests": "", "platform": "Desktop"})
    assert sub.status_code == 200
    job_id = sub.json()["job_id"]

    res = None
    for _ in range(30):
        jr = client.get(f"/api/rc/job/{job_id}").json()
        if jr["status"] == "completed":
            res = jr
            break
        time.sleep(0.05)
    assert res is not None
    assert res["finder_result"]["passed_brutal_gate"] is True
    assert res["finder_result"]["cycles_used"] == 2
    assert (tmp_path / "idea_hist.json").exists()


def test_reality_check_e2e_github_rate_limit_graceful_fallback(monkeypatch, tmp_path) -> None:
    from letsvibe_rc import grounding as rc_grounding

    rc_grounding.clear_github_cache()
    monkeypatch.setattr(rc_routes, "_store", rc_routes.RealityCheckStore(str(tmp_path / "rc_rl.db")))
    monkeypatch.setattr(rc_routes, "_RATE_MAX_HITS", 20)
    monkeypatch.setattr(
        rc_grounding,
        "_github_get_json",
        lambda url, timeout=6.0: (None, True, "GitHub API rate limit exceeded (resets in ~45s)."),
    )
    monkeypatch.setattr(rc_grounding, "_fetch_app_store", lambda short_q, platform, keywords: {"app_store_hits": []})

    captured: List[str] = []

    def fake_llama(system_prompt: str, user_prompt: str, max_tokens: int = 4096, temperature: float = 0.25):
        captured.append(user_prompt)
        return {
            "verdict": "NICHE ONLY",
            "headline": "Rate-limit resilient check",
            "viability_score": 5.5,
            "saturation_pct": 45.0,
            "demand_tier": "Underserved Pain",
            "dimensions": {"market_saturation": {"label": "Sat", "score": 5.5, "weight": 100, "reasoning": "Fallback"}},
            "pricing_recommendation": {"suggested_price": "$19", "model": "One-Time License", "reasoning": "Fair"},
        }

    monkeypatch.setattr(rc_eval, "_call_shared_llama", fake_llama)
    client = TestClient(app)
    sub = client.post("/api/rc/evaluate", json={"pitch": "Offline track telemetry logger for Miata drivers", "platform": "Desktop"})
    assert sub.status_code == 200
    job_id = sub.json()["job_id"]

    res = None
    for _ in range(30):
        jr = client.get(f"/api/rc/job/{job_id}").json()
        if jr["status"] == "completed":
            res = jr
            break
        time.sleep(0.05)
    assert res is not None
    assert len(captured) == 1
    assert "rate-limited" in captured[0].lower()
    assert "no widely-known >=500-star github" not in captured[0].lower()
