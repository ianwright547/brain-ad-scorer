"""SQLite persistence: response cache + scoring history.

The cache is content-addressed: the key is a SHA-256 hash of the exact
input plus the version of the evaluation prompt. Same ad + same prompt =
same cached answer, zero API cost. Change the prompt file and every old
entry misses automatically — no manual invalidation step to forget.
"""

import json
import sqlite3
import hashlib
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent.parent / "data" / "scorer.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS response_cache (
    cache_key   TEXT PRIMARY KEY,
    response    TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    input_type   TEXT NOT NULL,
    ad_preview   TEXT NOT NULL,
    claude_score REAL,
    rf_score     REAL,
    xgb_score    REAL,
    run_verdict  TEXT,
    cached       INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


@contextmanager
def connect(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path=None):
    path = Path(db_path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        conn.executescript(SCHEMA)


def make_cache_key(payload: bytes, prompt_version: str) -> str:
    digest = hashlib.sha256()
    digest.update(prompt_version.encode())
    digest.update(payload)
    return digest.hexdigest()


def cache_get(cache_key, db_path=None):
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT response FROM response_cache WHERE cache_key = ?", (cache_key,)
        ).fetchone()
    return json.loads(row["response"]) if row else None


def cache_put(cache_key, response, db_path=None):
    with connect(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO response_cache (cache_key, response) VALUES (?, ?)",
            (cache_key, json.dumps(response)),
        )


def history_add(input_type, ad_preview, scores, run_verdict, cached, db_path=None):
    with connect(db_path) as conn:
        conn.execute(
            """INSERT INTO history
               (input_type, ad_preview, claude_score, rf_score, xgb_score, run_verdict, cached)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                input_type,
                ad_preview,
                scores.get("claude_score"),
                scores.get("rf_score"),
                scores.get("xgb_score"),
                run_verdict,
                int(cached),
            ),
        )


def history_list(limit=20, db_path=None):
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(row) for row in rows]
