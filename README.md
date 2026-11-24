<p align="center">
  <a href="https://ko-fi.com/todd0042">
    <img src="https://raw.githubusercontent.com/Todd0042/creator-assets/main/banners/todd_creator_banner_v1.0.png" alt="Support Todd on Ko-fi" width="100%" />
  </a>
</p>

---

# 🧪 LetsVibe: Reality Check & Idea Finder

[![Version](https://img.shields.io/badge/Version-1.0.0-ff2a85.svg)](https://github.com/Todd0042/letsvibe-reality-check)
[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/License-PolyForm%20Noncommercial%201.0.0-00f0ff.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-39ff14.svg)]()
[![FastAPI + SQLite](https://img.shields.io/badge/Backend-FastAPI%20%2B%20SQLite-teal.svg)]()
[![Live Site](https://img.shields.io/badge/Live-letsviberc.todd0042.dev-00f0ff.svg)](https://letsviberc.todd0042.dev)
[![Support on Ko-fi](https://img.shields.io/badge/Ko--fi-Support%20Creator-F16061?style=flat&logo=ko-fi&logoColor=white)](https://ko-fi.com/todd0042)

> **Save your LLM tokens before you write Line 1 — stress-test any app idea against widely-known, high-traction incumbents with 3 feedback tones (*Realistic*, *Brutal / No Mercy*, and *Whisper Sweet Nothings*), or use the inverse Idea Finder to discover a monetizable niche with a copy-ready implementation prompt.**

---

## 📖 Table of Contents

* **Part 1 — User Overview & Quick Start**
  * [🧪 What Is LetsVibe: Reality Check?](#-what-is-letsvibe-reality-check)
  * [🎭 Three Feedback Tones](#-three-feedback-tones)
  * [💡 Inverse Mode: Idea Finder](#-inverse-mode-idea-finder)
  * [✨ Highlights at a Glance](#-highlights-at-a-glance)
  * [🚀 Quick Start (Run Locally)](#-quick-start-run-locally)
* **Part 2 — Consolidated Technical Documentation & Architecture Reference**
  * [1. System Architecture & FastAPI Endpoints (`letsvibe_rc/routes.py`, `letsvibe_rc/server.py`)](#1-system-architecture--fastapi-endpoints)
  * [2. High-Traction Grounding Engine (`letsvibe_rc/grounding.py`)](#2-high-traction-grounding-engine)
  * [3. Tone-Calibrated Evaluation & Scoring (`letsvibe_rc/evaluator.py`)](#3-tone-calibrated-evaluation--scoring)
  * [4. Idea Finder & 3-Day Anti-Repeat Memory (`letsvibe_rc/idea_finder.py`)](#4-idea-finder--3-day-anti-repeat-memory)
  * [5. SQLite Storage & XSS-Safe Standalone HTML Export (`letsvibe_rc/storage.py`, `letsvibe_rc/html_export.py`)](#5-sqlite-storage--xss-safe-standalone-html-export)
  * [6. Configuration & Environment Variables (`.env.example`)](#6-configuration--environment-variables)
  * [7. Repository Structure & E2E Test Suite (`tests/test_reality_check_e2e.py`)](#7-repository-structure--e2e-test-suite)
  * [8. Companion Apps & Licensing (`LICENSE`)](#8-companion-apps--licensing)

---

# Part 1 — User Overview & Quick Start

## 🧪 What Is LetsVibe: Reality Check?

**LetsVibe: Reality Check** is a zero-login, pre-build app idea validator built to stop vibe coders and indie builders from burning weeks of effort and API tokens on saturated CRUD wrappers—while still giving fair credit to focused offline, hardware, DSP, and vertical-business niches.

Instead of asking a sycophantic chat LLM *"is my app idea good?"*, Reality Check:
1. **Checks widely-known incumbents first** (`>= 500` GitHub stars and `>= 500` App Store reviews on Desktop/Mobile) so obscure weekend projects never create fake saturation.
2. **Scores 6 weighted dimensions on a 0–10 scale** (`Market Saturation`, `Switching Motivation`, `Niche Twist & Moat`, `Real Demand & Distribution`, `Build Effort vs. Payoff`, and `Anti-Slop / Originality`).
3. **Delivers practical next steps**: buyer-tier **Pricing Recommendation**, **Marketing Playbook**, **Personal vs. LLC Liability Check**, **Concrete Pivots**, shareable report URLs (`/r/{id}`), and standalone HTML downloads.

---

## 🎭 Three Feedback Tones

| Tone | What It Does |
| :--- | :--- |
| **Realistic (No Sugarcoating)** | Balanced, constructive analysis comparing only against recognizable incumbents and giving fair credit for real engineering or offline/one-time-license edges. |
| **Brutal / No Mercy** | Unfiltered stress test that pulls zero punches on weak differentiation, switching friction, and distribution delusions. |
| **Whisper Sweet Nothings** | Over-exaggerates your idea like a hype-man, finds every angle for real-world sale, and spells out exactly what you must deliver to live up to the hype. |

---

## 💡 Inverse Mode: Idea Finder

Not sure what to build yet? Switch to **💡 Idea Finder**:
1. **Optional Preferences:** Enter your personal hobbies, skills, or daily annoyances—or leave it blank for open discovery across 16 underserved real-world domains.
2. **1-Call Candidate Batch + 3-Day Anti-Repeat Filter:** Generates 4–5 distinct niche ideas in one LLM call while eliminating keywords and titles seen in the last 3 days.
3. **3-Cycle Viability Gate:** Automatically runs up to 3 candidates through Reality Check (`viability_score >= 6.0`, monetizable pricing model) and outputs a **📋 Prompt for Your LLM** to turn the winning idea into a step-by-step implementation plan.

---

## ✨ Highlights at a Glance

* **🔑 Zero Login & Zero User Token Cost**: Runs on a local `llama.cpp` (`llama-server`) instance—users don't need an account or API key.
* **📊 6-Dimension Reality Breakdown**: Weighted 0–10 scoring with automatic verdict reconciliation (`DO NOT BUILD`, `NICHE ONLY`, `ACTUALLY VIABLE`).
* **💵 Buyer-Tier Pricing Calibration**: Anchors pricing to real buyer tiers (`$5–$29` hobby, `$29–$99` one-time / `$9–$29/mo` prosumer/trades, `$49–$199/mo` B2B SaaS, `$0` OSS).
* **⚖️ Personal Publish vs. LLC Check**: Practical risk assessment and protection checklist (Merchant of Record, AS-IS terms, PII minimization).
* **📄 Shareable Reports & Offline HTML Export**: Every report gets a permalink (`/r/{report_id}`) and downloadable standalone dark-mode HTML file.
* **🤖 AI Transparency**: Clearly notes *"LetsVibe: Reality Check uses AI, AI can make mistakes."*

---

## 🚀 Quick Start (Run Locally)

### Prerequisites
- Python **3.10+**
- A running local `llama-server` (`llama.cpp`) completion endpoint (default: `http://127.0.0.1:11435`)

### Install & Run
```bash
git clone https://github.com/Todd0042/letsvibe-reality-check.git
cd letsvibe-reality-check

python -m venv .venv
source .venv/bin/activate
pip install -e .

cp .env.example .env
uvicorn letsvibe_rc.server:app --host 127.0.0.1 --port 8020
```
Open `http://127.0.0.1:8020/` in your browser.

---

# Part 2 — Consolidated Technical Documentation & Architecture Reference

## 1. System Architecture & FastAPI Endpoints

Implemented in [`letsvibe_rc/server.py`](letsvibe_rc/server.py) and [`letsvibe_rc/routes.py`](letsvibe_rc/routes.py):
- `GET /` and `GET /rc` — Serves the SPA template ([`reality_check.html`](letsvibe_rc/templates/reality_check.html)).
- `GET /r/{report_id}` and `GET /rc/r/{report_id}` — Preloads a saved report from SQLite for shareable links.
- `POST /api/rc/evaluate` — Queues a Reality Check job (`pitch`, `platform`, `twist`, `tone`) with per-IP rate limiting.
- `POST /api/rc/find-idea` — Queues an Idea Finder job (`interests`, `platform`, max 3 gate cycles).
- `GET /api/rc/job/{job_id}` — Polls job progress, lock status, and final report JSON.
- `GET /api/rc/report/{report_id}/html` — Exports an XSS-escaped standalone HTML report.
- `GET /api/rc/status` & `GET /api/health` — Lock and service health endpoints.

## 2. High-Traction Grounding Engine

Implemented in [`letsvibe_rc/grounding.py`](letsvibe_rc/grounding.py):
- `extract_keywords()` strips generic filler while preserving domain nouns (`wedding`, `event`, `djs`, `karaoke`, `hvac`, etc.) to build a 3-word domain query.
- Queries **only high-traction public signals**:
  - **GitHub:** `stars:>=500` with keyword overlap filtering.
  - **Apple App Store / macOS Store** (when `platform` is `Desktop`, `Android`, or `iOS`): `reviews >= 500` with `>= 2` keyword hits.
- Excludes noisy developer package/Q&A firehoses (`npm`, `Stack Overflow`, `Hacker News`) so obscure hobby projects never inflate perceived market saturation.

## 3. Tone-Calibrated Evaluation & Scoring

Implemented in [`letsvibe_rc/evaluator.py`](letsvibe_rc/evaluator.py):
- `SYSTEM_PROMPTS_BY_TONE` gives each tone (`realistic`, `brutal`, `whisper`) its own system prompt instead of fighting a single cynical prompt.
- Computes `viability_score` deterministically from weighted dimension scores and reconciles `verdict` (`< 4.0` → `DO NOT BUILD`, `4.0–6.7` → `NICHE ONLY`, `>= 6.8` → `ACTUALLY VIABLE`).
- Uses `max_tokens=4096` to prevent long JSON responses (especially in `whisper` mode) from truncating mid-string.

## 4. Idea Finder & 3-Day Anti-Repeat Memory

Implemented in [`letsvibe_rc/idea_finder.py`](letsvibe_rc/idea_finder.py):
- Generates 4–5 candidates in a single LLM call using randomized `_ANGLE_LENSES` and 16 `_OPEN_DOMAINS`.
- Persists candidate titles and extracted keywords for **3 days (`259200s`)** in `rc_idea_history.json`, eliminating recently used domains and injecting an explicit **Anti-Repeat Filter** into subsequent prompts.
- Gates up to `max_cycles = 3` candidates sequentially against the Reality Check evaluator (`viability_score >= 6.0`, `verdict != "DO NOT BUILD"`, `model != "Do Not Monetize"`).

## 5. SQLite Storage & XSS-Safe Standalone HTML Export

- [`letsvibe_rc/storage.py`](letsvibe_rc/storage.py): Stores reports in SQLite (`rc_reports`) keyed by 10-character hex `report_id`.
- [`letsvibe_rc/html_export.py`](letsvibe_rc/html_export.py): Escapes all user and LLM strings via `html.escape(..., quote=True)` before generating downloadable `.html` reports.

## 6. Configuration & Environment Variables

See [`.env.example`](.env.example):
- `LETSVIBE_RC_LLAMA_URL` — `llama-server` base URL (default: `http://127.0.0.1:11435`).
- `LETSVIBE_RC_DB_PATH` — Optional SQLite database path.
- `LETSVIBE_RC_IDEA_HISTORY_PATH` — Optional 3-day Idea Finder anti-repeat JSON path.
- `LETSVIBE_RC_RATE_LIMIT` — Requests per 10 minutes per IP (default: `10`, `0` disables).

## 7. Repository Structure & E2E Test Suite

```text
letsvibe-reality-check/
├── letsvibe_rc/
│   ├── __init__.py
│   ├── evaluator.py
│   ├── grounding.py
│   ├── html_export.py
│   ├── idea_finder.py
│   ├── routes.py
│   ├── server.py
│   ├── storage.py
│   ├── static/
│   └── templates/reality_check.html
├── tests/
│   └── test_reality_check_e2e.py
├── .env.example
├── .gitignore
├── LICENSE
├── pyproject.toml
└── README.md
```

Run the automated E2E test suite:
```bash
pytest tests/test_reality_check_e2e.py -v
```

## 8. Companion Apps & Licensing

* **Companion Platform:** [LetsVibe Code Auditor & Leaderboard](https://github.com/Todd0042/letsvibe) (`https://letsvibe.todd0042.dev`)
* **License:** [PolyForm Noncommercial License 1.0.0](LICENSE) — free for personal, hobby, educational, research and nonprofit use; commercial use (inside a company, in a paid product or service, or for profit) requires a separate license from [Todd0042](https://github.com/Todd0042). Copyright © 2026 [Todd0042](https://github.com/Todd0042)
