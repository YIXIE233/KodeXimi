from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
PRAGMA busy_timeout=5000;

CREATE TABLE IF NOT EXISTS jobs (
  job_id TEXT PRIMARY KEY,
  state TEXT NOT NULL,
  task_type TEXT NOT NULL,
  goal TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  error_code TEXT,
  error_message TEXT
);

CREATE TABLE IF NOT EXISTS attempts (
  job_id TEXT NOT NULL,
  attempt_no INTEGER NOT NULL,
  state TEXT NOT NULL,
  started_at TEXT,
  finished_at TEXT,
  duration_ms INTEGER,
  verify_conclusion TEXT,
  usage_data_completeness TEXT,
  total_tokens_observed INTEGER,
  error_code TEXT,
  error_message TEXT,
  PRIMARY KEY (job_id, attempt_no),
  FOREIGN KEY (job_id) REFERENCES jobs(job_id)
);

CREATE TABLE IF NOT EXISTS events (
  sequence INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id TEXT,
  attempt_no INTEGER,
  event_type TEXT NOT NULL,
  payload_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reviews (
  review_id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id TEXT NOT NULL,
  attempt_no INTEGER NOT NULL,
  decision TEXT NOT NULL,
  reason_text TEXT,
  reason_file TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (job_id) REFERENCES jobs(job_id)
);

CREATE TABLE IF NOT EXISTS usage (
  job_id TEXT NOT NULL,
  attempt_no INTEGER NOT NULL,
  data_completeness TEXT NOT NULL,
  input_tokens INTEGER,
  output_tokens INTEGER,
  total_tokens INTEGER,
  duration_ms INTEGER,
  payload_json TEXT,
  created_at TEXT NOT NULL,
  PRIMARY KEY (job_id, attempt_no),
  FOREIGN KEY (job_id) REFERENCES jobs(job_id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_state_updated ON jobs(state, updated_at);
CREATE INDEX IF NOT EXISTS idx_events_job_sequence ON events(job_id, sequence);
CREATE INDEX IF NOT EXISTS idx_usage_job_attempt ON usage(job_id, attempt_no);
"""


class Store:
    def __init__(self, path: Path):
        self.path = path

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        with self.connect() as conn:
            conn.execute(sql, params)

    def query_one(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(sql, params).fetchone()
            return dict(row) if row else None

    def query_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

