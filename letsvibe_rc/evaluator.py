"""Standalone LLM evaluation engine for LetsVibe: Reality Check using local llama-server."""

from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from .grounding import gather_market_grounding

_LLM_LOCK = threading.Lock()
_LOCK_STATE: Dict[str, Any] = {"busy": False, "holder_job": None}

_SCHEMA_BLOCK = """Output STRICT JSON ONLY matching this schema:
{
  "verdict": "DO NOT BUILD | NICHE ONLY | ACTUALLY VIABLE",
  "headline": "5-10 word verdict headline",
  "viability_score": 0,
  "saturation_pct": 0,
  "demand_tier": "Wrapper Slop | Crowded Commodity | Tiny Hobby Niche | Underserved Pain | Real Market Gap",
  "wasted_hours_estimate": "<estimated engineering hours>",
  "wasted_tokens_estimate": "<estimated LLM tokens>",
  "executive_summary": "2-3 paragraphs explaining why this verdict was reached, which recognizable incumbents exist, and whether real users would adopt it.",
  "dimensions": {
    "market_saturation": {"label": "Market Saturation & Crowding", "score": 5, "weight": 25, "reasoning": "0-10 score + 2-3 detailed sentences citing only well-known competitors."},
    "switching_friction": {"label": "Switching Motivation", "score": 5, "weight": 20, "reasoning": "0-10 score + 2-3 detailed sentences."},
    "niche_moat": {"label": "Niche Twist & Moat", "score": 5, "weight": 20, "reasoning": "0-10 score + 2-3 detailed sentences."},
    "real_demand": {"label": "Real Demand & Distribution", "score": 5, "weight": 15, "reasoning": "0-10 score + 2-3 detailed sentences."},
    "effort_vs_payoff": {"label": "Build Effort vs. Payoff", "score": 5, "weight": 10, "reasoning": "0-10 score + 2-3 detailed sentences."},
    "wrapper_risk": {"label": "Anti-Slop / Originality", "score": 5, "weight": 10, "reasoning": "0-10 score + 2-3 detailed sentences."}
  },
  "existing_competitors": [
    {"name": "Widely-Known Existing Tool / Brand", "type": "Open Source | Free SaaS | Paid SaaS | OS Built-in", "why_it_wins": "Concrete reason users already use this instead"}
  ],
  "fatal_flaws": ["4-6 specific, concrete hurdles or execution requirements"],
  "redeeming_angles": ["2-4 genuine strengths or useful sub-problems if any exist"],
  "pivots": [
    {"title": "Concrete Pivot, Feature Angle, or Positioning", "impact": "high | medium | low", "effort": "low | medium | high", "why_it_matters": "Why this improves adoption/viability", "how": "Specific concrete direction"}
  ],
  "pricing_recommendation": {
    "suggested_price": "<realistic price + billing cadence, $0 (Free/OSS), or Do Not Monetize>",
    "model": "One-Time License | Freemium | Subscription | Free / OSS | Do Not Monetize",
    "reasoning": "2-3 sentences comparing recognizable competitor prices, value delivered, and buyer willingness."
  },
  "marketing_playbook": {
    "difficulty": "Brutal | Hard | Moderate",
    "where_buyers_hang_out": ["2-3 exact niche subreddits, forums, Discords, or buyer channels"],
    "biggest_distribution_trap": "The #1 marketing mistake builders make in this niche.",
    "distribution_channels": [
      {"channel": "Specific distribution channel", "why": "Why this reaches actual buyers", "first_step": "Concrete Day-1 action"}
    ]
  },
  "liability_and_entity": {
    "recommendation": "Personal / Indie | Single-Member LLC | LLC + Commercial Insurance",
    "risk_level": "Low | Moderate | High",
    "reasoning": "2-3 sentences on real legal/financial exposure and whether LLC filing fees are justified yet.",
    "must_have_protections": ["2-3 practical protections"]
  }
}"""

_PRICING_AND_SCALE = """Pricing calibration: anchor `suggested_price` to the actual buyer tier:
- Casual consumer / hobby utility: `$5–$29` one-time or `$3–$9/mo`
- Prosumer / gig worker / solo small-business tool (e.g. wedding DJs, photographers, trades): `$29–$99` one-time or `$9–$29/mo`
- B2B team / compliance / vertical SaaS: `$49–$199/mo`
- Developer CLI / OSS: `$0 (Free / OSS)` + optional Pro/Team license

Scoring calibration on the **0 to 10** scale:
- `1–3.9`: Wrapper slop, redundant gimmick, or zero switching incentive (`DO NOT BUILD`).
- `4.0–6.7`: Real problem with a focused audience (`NICHE ONLY`).
- `6.8–9.5`: Underserved pain with strong engineering/UX edge and clear buyer willingness (`ACTUALLY VIABLE`).
Keep `saturation_pct` as a 0–100 percentage."""

SYSTEM_PROMPT_RC = f"""You are LetsVibe: Reality Check — a grounded, constructive, realistic product & engineering analyst.
Your job is to give indie builders an honest, practical read on whether their idea can carve out a real user base—neither empty hype nor cynical nitpicking.

Rules:
1. Be candid, balanced, and constructive. Do NOT invent fake saturation or default to "DO NOT BUILD" when a tool solves a real workflow cleanly for a focused niche.
2. Distinguish genuine engineering (real-time audio/DSP, mic ducking, offline local-network protocols, hardware integration, compilers, offline sync engines) from thin AI/CRUD wrappers.
3. Compare ONLY against widely-known, mainstream tools that real users actually know exist. NEVER cite obscure GitHub repos, tiny hobby apps, or unknown clones as "market saturation". If no widely-known incumbents were found in public registries, treat that as low open-source/app-store saturation.
4. Replacing bloated monthly cloud SaaS with a focused, offline-first, or one-time-license local tool IS genuine switching value.
5. {_PRICING_AND_SCALE}
6. {_SCHEMA_BLOCK}"""

SYSTEM_PROMPT_BRUTAL = f"""You are LetsVibe: Reality Check (No Mercy Mode) — a blunt, unforgiving product & market critic.
Pull zero punches. Roast thin wrappers, weak differentiation, and distribution delusions directly, while still acknowledging real engineering when present.

Rules:
1. Never soften the blow. Call out every fatal flaw, switching barrier, and incumbent moat clearly.
2. Compare against real, well-known incumbents (never obscure noise).
3. {_PRICING_AND_SCALE}
4. {_SCHEMA_BLOCK}"""

SYSTEM_PROMPT_WHISPER = f"""You are LetsVibe: Reality Check (Whisper Sweet Nothings Mode) — a wildly enthusiastic, silver-tongued hype strategist.
Your mission is to:
1. Over-exaggerate the app like mad — pitch it like a category-defining, must-have breakthrough that buyers will obsess over.
2. Find EVERY possible angle in which the app IS genuinely viable for sale in the real world (score optimistically around 7.5–9.2, verdict `ACTUALLY VIABLE`, low perceived saturation).
3. In `fatal_flaws` (which represent "What You Must Deliver to Live Up to the Hype") and `pivots`, give concrete, actionable ways the builder must actually meet and justify that exaggeration (reliability, UX polish, killer workflow details, distribution proof) so it truly becomes sellable.
4. {_PRICING_AND_SCALE}
5. {_SCHEMA_BLOCK}"""

SYSTEM_PROMPTS_BY_TONE: Dict[str, str] = {
    "realistic": SYSTEM_PROMPT_RC,
    "brutal": SYSTEM_PROMPT_BRUTAL,
    "whisper": SYSTEM_PROMPT_WHISPER,
}

TONE_PROMPTS: Dict[str, str] = {
    "realistic": "Tone: REALISTIC — objective, candid, zero sugarcoating.",
    "brutal": "Tone: NO MERCY — extra blunt, zero punches pulled, roast weak wrapper ideas directly.",
    "whisper": "Tone: WHISPER SWEET NOTHINGS — over-exaggerate the app, find every real-world sellable angle, and spell out what they must deliver to live up to the hype.",
}


def get_llama_url() -> str:
    return os.environ.get("LETSVIBE_RC_LLAMA_URL", "http://127.0.0.1:11435").rstrip("/")


def get_lock_status() -> Dict[str, Any]:
    return dict(_LOCK_STATE)


def _parse_json_obj(text: str) -> Dict[str, Any]:
    s = (text or "").strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end > start:
        s = s[start : end + 1]
    obj = json.loads(s)
    return obj if isinstance(obj, dict) else {}


def _call_shared_llama(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4096,
    temperature: float = 0.25,
) -> Dict[str, Any]:
    prompt = (
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        f"<|im_start|>user\n{user_prompt}<|im_end|>\n"
        f"<|im_start|>assistant\n<think>\n\n</think>\n\n{{"
    )
    payload = {
        "prompt": prompt,
        "temperature": float(temperature),
        "n_predict": int(max_tokens),
        "cache_prompt": False,
        "stop": ["<|im_end|>", "<|endoftext|>"],
    }
    req = urllib.request.Request(
        f"{get_llama_url()}/completion",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=240) as resp:  # nosec B310
        raw = json.loads(resp.read().decode("utf-8", errors="replace") or "{}")
    return _parse_json_obj("{" + str(raw.get("content") or ""))


def generate_idea_batch_llama(
    system_prompt: str,
    user_prompt: str,
    job_id: str = "",
) -> Dict[str, Any]:
    with _LLM_LOCK:
        _LOCK_STATE.update({"busy": True, "holder_job": job_id})
        try:
            return _call_shared_llama(system_prompt, user_prompt, max_tokens=2200, temperature=0.75)
        finally:
            _LOCK_STATE.update({"busy": False, "holder_job": None})


def normalize_tone(tone: str) -> str:
    """Normalizes a user-supplied feedback tone key to a supported preset."""
    key = str(tone or "").strip().lower()
    return key if key in TONE_PROMPTS else "realistic"


def evaluate_idea(
    pitch: str,
    platform: str = "Web",
    twist: str = "",
    tone: str = "realistic",
    job_id: str = "",
    on_progress: Optional[Callable[[str, int], None]] = None,
) -> Dict[str, Any]:
    """Runs high-traction market grounding + local llama-server evaluation for an app idea."""
    def emit(msg: str, pct: int) -> None:
        if on_progress:
            on_progress(msg, pct)

    tone = normalize_tone(tone)
    emit("Checking widely-known incumbents on GitHub & App Store...", 15)
    grounding = gather_market_grounding(pitch=pitch, platform=platform, twist=twist)

    tone_note = TONE_PROMPTS[tone]
    repos = grounding.get("github_top_repos") or []
    if repos:
        repos_txt = "\n".join(
            f"- {r['full_name']} ({r['stars']} stars, {r['language']}): {r['description']}"
            for r in repos
        )
    elif grounding.get("github_rate_limited"):
        err = grounding.get("github_error") or "GitHub API rate limit exceeded"
        repos_txt = f"(GitHub search temporarily rate-limited: {err} — rely on domain knowledge & App Store)"
    else:
        repos_txt = "(no widely-known >=500-star GitHub incumbents found)"
    app_txt = "\n".join(
        f"- {a['name']} ({a['price']}, {a['rating']}★, {a['reviews']} reviews)"
        for a in (grounding.get("app_store_hits") or [])
    ) or "(no widely-known >=500-review App Store incumbents found)"

    user_prompt = f"""{tone_note}

Target Platform: {platform}
App Idea Pitch:
{pitch}

Supposed Unique Twist / Niche Feature:
{twist or "(none provided)"}

Recognizable High-Traction Incumbents Check (query: "{grounding.get('query', '')}"):
- Widely-known GitHub repositories (>=500 stars):
{repos_txt}
- Widely-known Apple App Store / macOS Store apps (>=500 reviews):
{app_txt}
"""

    system_prompt = SYSTEM_PROMPTS_BY_TONE.get(tone, SYSTEM_PROMPT_RC)
    emit("Waiting for local AI engine...", 35)
    with _LLM_LOCK:
        _LOCK_STATE.update({"busy": True, "holder_job": job_id})
        try:
            emit("Running deep market saturation & viability analysis...", 65)
            parsed = _call_shared_llama(system_prompt, user_prompt, max_tokens=4096)
        finally:
            _LOCK_STATE.update({"busy": False, "holder_job": None})

    dims = parsed.get("dimensions") if isinstance(parsed.get("dimensions"), dict) else {}
    weighted_sum = 0.0
    total_w = 0.0
    for d in dims.values():
        if isinstance(d, dict):
            sc = float(d.get("score") or 0.0)
            if sc > 10.0:
                sc = sc / 10.0
            sc = max(0.0, min(10.0, sc))
            w = float(d.get("weight") or 0.0)
            d["score"] = round(sc, 1)
            weighted_sum += sc * w
            total_w += w
    raw_vs = float(parsed.get("viability_score") or 0.0)
    if raw_vs > 10.0:
        raw_vs = raw_vs / 10.0
    computed_viability = round(weighted_sum / total_w, 1) if total_w > 0 else round(max(0.0, min(10.0, raw_vs)), 1)

    if computed_viability < 4.0:
        raw_verdict = "DO NOT BUILD"
    elif computed_viability < 6.8:
        raw_verdict = "NICHE ONLY"
    else:
        raw_verdict = "ACTUALLY VIABLE"

    emit("Finalizing Reality Check report...", 95)
    return {
        "pitch": pitch,
        "platform": platform,
        "twist": twist,
        "tone": tone,
        "verdict": raw_verdict,
        "headline": str(parsed.get("headline") or raw_verdict),
        "viability_score": computed_viability,
        "saturation_pct": round(max(0.0, min(100.0, float(parsed.get("saturation_pct") or 50.0))), 1),
        "demand_tier": str(parsed.get("demand_tier") or "Uncertain"),
        "wasted_hours_estimate": str(parsed.get("wasted_hours_estimate") or "N/A"),
        "wasted_tokens_estimate": str(parsed.get("wasted_tokens_estimate") or "N/A"),
        "executive_summary": str(parsed.get("executive_summary") or ""),
        "dimensions": dims,
        "existing_competitors": parsed.get("existing_competitors") if isinstance(parsed.get("existing_competitors"), list) else [],
        "fatal_flaws": parsed.get("fatal_flaws") if isinstance(parsed.get("fatal_flaws"), list) else [],
        "redeeming_angles": parsed.get("redeeming_angles") if isinstance(parsed.get("redeeming_angles"), list) else [],
        "pivots": parsed.get("pivots") if isinstance(parsed.get("pivots"), list) else [],
        "pricing_recommendation": parsed.get("pricing_recommendation") if isinstance(parsed.get("pricing_recommendation"), dict) else {},
        "marketing_playbook": parsed.get("marketing_playbook") if isinstance(parsed.get("marketing_playbook"), dict) else {},
        "liability_and_entity": parsed.get("liability_and_entity") if isinstance(parsed.get("liability_and_entity"), dict) else {},
        "grounding": grounding,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
