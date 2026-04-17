from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import sqlite3
from typing import Any, Iterable


SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS queries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  telegram_chat_id INTEGER,
  telegram_user_id INTEGER,
  telegram_username TEXT,
  message_id INTEGER,

  raw_text TEXT NOT NULL,

  category TEXT,
  priority TEXT,
  intent TEXT,
  status TEXT,

  extracted_issues_json TEXT,
  suggested_reply TEXT,

  rag_used INTEGER NOT NULL DEFAULT 0,
  rag_sources_json TEXT,

  llm_model TEXT,
  llm_prompt_version TEXT,

  extra_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_queries_created_at ON queries(created_at);
CREATE INDEX IF NOT EXISTS idx_queries_category ON queries(category);
CREATE INDEX IF NOT EXISTS idx_queries_priority ON queries(priority);
"""


@dataclass(frozen=True)
class QueryRow:
    id: int
    created_at: str
    raw_text: str
    category: str | None
    priority: str | None
    intent: str | None
    status: str | None


def connect(sqlite_path: Path) -> sqlite3.Connection:
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(sqlite_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def _dumps(v: Any) -> str | None:
    if v is None:
        return None
    return json.dumps(v, ensure_ascii=False)


def insert_query(
    conn: sqlite3.Connection,
    *,
    telegram_chat_id: int | None,
    telegram_user_id: int | None,
    telegram_username: str | None,
    message_id: int | None,
    raw_text: str,
    category: str | None = None,
    priority: str | None = None,
    intent: str | None = None,
    status: str | None = None,
    extracted_issues: Any | None = None,
    suggested_reply: str | None = None,
    rag_used: bool = False,
    rag_sources: Any | None = None,
    llm_model: str | None = None,
    llm_prompt_version: str | None = None,
    extra: Any | None = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO queries(
          telegram_chat_id, telegram_user_id, telegram_username, message_id,
          raw_text, category, priority, intent, status,
          extracted_issues_json, suggested_reply,
          rag_used, rag_sources_json,
          llm_model, llm_prompt_version,
          extra_json
        ) VALUES (
          ?, ?, ?, ?,
          ?, ?, ?, ?, ?,
          ?, ?,
          ?, ?,
          ?, ?,
          ?
        )
        """,
        (
            telegram_chat_id,
            telegram_user_id,
            telegram_username,
            message_id,
            raw_text,
            category,
            priority,
            intent,
            status,
            _dumps(extracted_issues),
            suggested_reply,
            1 if rag_used else 0,
            _dumps(rag_sources),
            llm_model,
            llm_prompt_version,
            _dumps(extra),
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def fetch_recent_queries(conn: sqlite3.Connection, limit: int = 50) -> list[QueryRow]:
    rows = conn.execute(
        """
        SELECT id, created_at, raw_text, category, priority, intent, status
        FROM queries
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [
        QueryRow(
            id=int(r["id"]),
            created_at=str(r["created_at"]),
            raw_text=str(r["raw_text"]),
            category=r["category"],
            priority=r["priority"],
            intent=r["intent"],
            status=r["status"],
        )
        for r in rows
    ]


def counts_by_field(conn: sqlite3.Connection, field: str, limit: int = 10) -> list[tuple[str, int]]:
    if field not in {"category", "priority", "intent", "status"}:
        raise ValueError("Unsupported field. Use: category, priority, intent, status")
    rows = conn.execute(
        f"""
        SELECT COALESCE({field}, 'unknown') AS key, COUNT(*) AS cnt
        FROM queries
        GROUP BY COALESCE({field}, 'unknown')
        ORDER BY cnt DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [(str(r["key"]), int(r["cnt"])) for r in rows]
