"""Free deterministic market grounding across widely-known, high-traction incumbents only."""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

_STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "with", "that", "this", "from", "into",
    "your", "my", "our", "app", "tool", "platform", "system", "using", "based",
    "powered", "simple", "easy", "fast", "modern", "smart", "best", "make", "build",
    "create", "helps", "help", "users", "people", "like", "just", "only", "more", "very",
    "want", "need", "would", "could", "should", "will", "have", "has", "are", "is",
    "offline", "online", "small", "big", "shiny", "dark", "mode", "without", "requiring",
    "desktop", "mobile", "android", "ios", "web", "saas", "cli", "software", "program",
    "developers", "teams", "live", "real", "time", "manage", "managing", "handle",
    "handling", "track", "tracking", "organize", "organizing", "control", "controlling",
    "local", "network", "over", "one", "click", "five", "minute", "minutes", "daily",
    "common", "expensive", "cheap", "free", "paid", "new", "better",
    "zero-install", "self-hosted", "built-in", "low-latency", "unlimited", "anywhere",
}

_CONSUMER_PLATFORMS = {"Desktop", "Android", "iOS"}


def extract_keywords(pitch: str, twist: str = "", limit: int = 5) -> List[str]:
    text = f"{pitch} {twist}".lower()
    tokens = re.findall(r"[a-z0-9][a-z0-9+-]{2,}", text)
    seen: List[str] = []
    for tok in tokens:
        if tok in _STOPWORDS or tok.isdigit():
            continue
        if tok not in seen:
            seen.append(tok)
        if len(seen) >= limit:
            break
    return seen or ["software"]


def _keyword_overlap_count(text: str, keywords: List[str]) -> int:
    lower = (text or "").lower()
    return sum(1 for kw in keywords if kw in lower)


def _get_json(url: str, timeout: float = 4.0) -> Dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "LetsVibe-RealityCheck/1.0 (+https://letsviberc.todd0042.dev)",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - fixed public registry URLs only
        return json.loads(resp.read().decode("utf-8", errors="replace") or "{}")


def _fetch_github(short_q: str, keywords: List[str]) -> Dict[str, Any]:
    """Fetches only widely-known GitHub repositories (>= 500 stars)."""
    try:
        q = urllib.parse.quote_plus(f"{short_q} stars:>=500")
        gh = _get_json(f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page=8")
        repos = []
        for item in (gh.get("items") or []):
            full_name = str(item.get("full_name") or "")
            desc = str(item.get("description") or "")[:160]
            stars = int(item.get("stargazers_count") or 0)
            if stars < 500 or _keyword_overlap_count(f"{full_name} {desc}", keywords) < 1:
                continue
            repos.append({
                "full_name": full_name,
                "stars": stars,
                "language": str(item.get("language") or ""),
                "description": desc,
            })
            if len(repos) >= 5:
                break
        return {"github_total_count": len(repos), "github_top_repos": repos}
    except Exception:
        return {"github_total_count": 0, "github_top_repos": []}


def _fetch_app_store(short_q: str, platform: str, keywords: List[str]) -> Dict[str, Any]:
    """Fetches only widely-known App Store apps (>= 500 reviews)."""
    try:
        entity = "macSoftware" if platform.lower() == "desktop" else "software"
        aq = urllib.parse.quote_plus(short_q)
        res = _get_json(f"https://itunes.apple.com/search?term={aq}&entity={entity}&limit=10")
        apps = []
        for item in (res.get("results") or []):
            name = str(item.get("trackName") or "")
            desc = str(item.get("description") or "")[:200]
            reviews = int(item.get("userRatingCount") or 0)
            if not name or reviews < 500 or _keyword_overlap_count(f"{name} {desc}", keywords) < min(2, len(keywords)):
                continue
            apps.append({
                "name": name,
                "price": str(item.get("formattedPrice") or "Free"),
                "rating": round(float(item.get("averageUserRating") or 0.0), 1),
                "reviews": reviews,
            })
            if len(apps) >= 5:
                break
        return {"app_store_hits": apps}
    except Exception:
        return {"app_store_hits": []}


def gather_market_grounding(pitch: str, platform: str = "Web", twist: str = "") -> Dict[str, Any]:
    """Queries only high-traction public registries so obscure apps don't create fake saturation."""
    keywords = extract_keywords(pitch, twist, limit=5)
    short_q = " ".join(keywords[:3])
    out: Dict[str, Any] = {
        "keywords": keywords,
        "query": short_q,
        "platform": platform,
        "github_total_count": 0,
        "github_top_repos": [],
        "app_store_hits": [],
        "npm_total_count": 0,
        "npm_top_packages": [],
        "hn_total_hits": 0,
        "hn_stories": [],
        "so_questions": [],
    }

    with ThreadPoolExecutor(max_workers=2) as pool:
        futs = [pool.submit(_fetch_github, short_q, keywords)]
        if platform in _CONSUMER_PLATFORMS:
            futs.append(pool.submit(_fetch_app_store, short_q, platform, keywords))
        for fut in futs:
            out.update(fut.result())

    return out
