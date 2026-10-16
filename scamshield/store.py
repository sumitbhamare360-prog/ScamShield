import os
import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Dict, Set, Any, Optional

DEFAULT_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "scamshield.db")
)

_ACTIVE_DB_PATH: str = DEFAULT_DB_PATH


def _get_connection(path: Optional[str] = None) -> sqlite3.Connection:
    target_path = path or _ACTIVE_DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path: Optional[str] = None) -> None:
    """Initialize SQLite database with scans, feedback, and blocklist tables."""
    global _ACTIVE_DB_PATH
    if path:
        _ACTIVE_DB_PATH = os.path.abspath(path)

    conn = _get_connection()
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    masked_text TEXT NOT NULL,
                    verdict_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER NOT NULL,
                    label TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (scan_id) REFERENCES scans (id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS blocklist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE (kind, value)
                )
                """
            )
    finally:
        conn.close()


def save_scan(masked_text: str, channel: str, verdict: Dict[str, Any]) -> int:
    """Save scan record with masked text only. Returns inserted scan_id."""
    init_db()
    conn = _get_connection()
    now_iso = datetime.now(timezone.utc).isoformat()
    verdict_str = json.dumps(verdict)
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO scans (created_at, channel, masked_text, verdict_json)
                VALUES (?, ?, ?, ?)
                """,
                (now_iso, channel, masked_text, verdict_str)
            )
            return cursor.lastrowid
    finally:
        conn.close()


def list_scans(limit: int = 50) -> List[Dict[str, Any]]:
    """List recent scans up to limit."""
    init_db()
    conn = _get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT id, created_at, channel, masked_text, verdict_json
            FROM scans
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = cursor.fetchall()
        results = []
        for r in rows:
            try:
                v_data = json.loads(r["verdict_json"])
            except Exception:
                v_data = {}
            results.append({
                "id": r["id"],
                "created_at": r["created_at"],
                "channel": r["channel"],
                "masked_text": r["masked_text"],
                "verdict": v_data
            })
        return results
    finally:
        conn.close()


def delete_scan(scan_id: int) -> None:
    """Delete a scan by id."""
    init_db()
    conn = _get_connection()
    try:
        with conn:
            conn.execute("DELETE FROM feedback WHERE scan_id = ?", (scan_id,))
            conn.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
    finally:
        conn.close()


def clear_history() -> None:
    """Delete all scans and feedback records."""
    init_db()
    conn = _get_connection()
    try:
        with conn:
            conn.execute("DELETE FROM feedback")
            conn.execute("DELETE FROM scans")
    finally:
        conn.close()


def save_feedback(scan_id: int, label: str) -> None:
    """Save feedback for a scan."""
    init_db()
    conn = _get_connection()
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO feedback (scan_id, label, created_at)
                VALUES (?, ?, ?)
                """,
                (scan_id, label, now_iso)
            )
    finally:
        conn.close()


def add_blocklist(kind: str, value: str) -> None:
    """Add an entry to blocklist."""
    init_db()
    conn = _get_connection()
    now_iso = datetime.now(timezone.utc).isoformat()
    clean_val = value.strip().lower()
    clean_kind = kind.strip().lower()
    try:
        with conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO blocklist (kind, value, created_at)
                VALUES (?, ?, ?)
                """,
                (clean_kind, clean_val, now_iso)
            )
    finally:
        conn.close()


def get_blocklist() -> Set[str]:
    """Get all blocklist values as a set."""
    init_db()
    conn = _get_connection()
    try:
        cursor = conn.execute("SELECT value FROM blocklist")
        return {r["value"] for r in cursor.fetchall()}
    finally:
        conn.close()
