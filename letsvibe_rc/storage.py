"""SQLite storage for shareable LetsVibe: Reality Check reports."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class RealityCheckStore:
    def __init__(self, db_path: Optional[str] = None) -> None:
        default_path = os.getenv("LETSVIBE_RC_DB_PATH") or str(Path(os.getenv("LETSVIBE_DATA_DIR", "data")) / "letsvibe_rc.db")
        self.db_path = db_path or default_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rc_reports (
                    id TEXT PRIMARY KEY,
                    pitch TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    twist TEXT NOT NULL,
                    tone TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    viability_score REAL NOT NULL,
                    saturation_pct REAL NOT NULL,
                    report_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save_report(self, report: Dict[str, Any]) -> str:
        report_id = str(report.get("id") or uuid.uuid4().hex[:10])
        report["id"] = report_id
        now = str(report.get("created_at") or datetime.now(timezone.utc).isoformat())
        report["created_at"] = now
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO rc_reports
                (id, pitch, platform, twist, tone, verdict, viability_score, saturation_pct, report_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id,
                    str(report.get("pitch") or "")[:2000],
                    str(report.get("platform") or "Web")[:64],
                    str(report.get("twist") or "")[:1000],
                    str(report.get("tone") or "realistic")[:32],
                    str(report.get("verdict") or "DO NOT BUILD")[:32],
                    float(report.get("viability_score") or 0.0),
                    float(report.get("saturation_pct") or 0.0),
                    json.dumps(report, ensure_ascii=False),
                    now,
                ),
            )
            conn.commit()
        return report_id

    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        clean_id = "".join(ch for ch in str(report_id) if ch.isalnum() or ch in ("-", "_"))[:32]
        if not clean_id:
            return None
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT report_json FROM rc_reports WHERE id = ?", (clean_id,)).fetchone()
            if not row:
                return None
            return json.loads(row["report_json"])
