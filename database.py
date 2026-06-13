import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS automation_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submitted_at TEXT NOT NULL,
    requester_name TEXT,
    department_hint TEXT,
    raw_request TEXT NOT NULL,
    category TEXT NOT NULL,
    priority_score INTEGER NOT NULL,
    automation_potential REAL NOT NULL,
    complexity TEXT NOT NULL,
    module_name TEXT NOT NULL,
    status TEXT NOT NULL,
    result_summary TEXT,
    hours_saved REAL DEFAULT 0,
    cost_savings REAL DEFAULT 0,
    estimated_cost REAL DEFAULT 0,
    token_usage INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    category TEXT NOT NULL,
    execution_time_ms INTEGER NOT NULL,
    success INTEGER NOT NULL,
    error_message TEXT,
    token_usage INTEGER DEFAULT 0,
    estimated_cost REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS weekly_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    generated_at TEXT NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    local_pdf_path TEXT,
    google_doc_url TEXT,
    summary_json TEXT NOT NULL
);
"""


def now():
    return datetime.now(timezone.utc).isoformat()


def connect(db_path):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path):
    with closing(connect(db_path)) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def save_request(db_path, data):
    data = dict(data)
    data["submitted_at"] = now()
    fields = [
        "submitted_at",
        "requester_name",
        "department_hint",
        "raw_request",
        "category",
        "priority_score",
        "automation_potential",
        "complexity",
        "module_name",
        "status",
        "result_summary",
        "hours_saved",
        "cost_savings",
        "estimated_cost",
        "token_usage",
    ]
    values = [data.get(field) for field in fields]
    with closing(connect(db_path)) as conn:
        cursor = conn.execute(
            f"INSERT INTO automation_requests ({', '.join(fields)}) VALUES ({', '.join(['?'] * len(fields))})",
            values,
        )
        conn.commit()
        return cursor.lastrowid


def save_log(db_path, data):
    fields = [
        "request_id",
        "timestamp",
        "category",
        "execution_time_ms",
        "success",
        "error_message",
        "token_usage",
        "estimated_cost",
    ]
    row = dict(data)
    row["timestamp"] = now()
    values = [row.get(field) for field in fields]
    with closing(connect(db_path)) as conn:
        conn.execute(
            f"INSERT INTO execution_logs ({', '.join(fields)}) VALUES ({', '.join(['?'] * len(fields))})",
            values,
        )
        conn.commit()


def get_request(db_path, request_id):
    with closing(connect(db_path)) as conn:
        row = conn.execute(
            "SELECT * FROM automation_requests WHERE id = ?", (request_id,)
        ).fetchone()
        return dict(row) if row else None


def get_history(db_path, limit=100):
    with closing(connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT * FROM automation_requests ORDER BY submitted_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_logs(db_path):
    with closing(connect(db_path)) as conn:
        rows = conn.execute("SELECT * FROM execution_logs ORDER BY timestamp DESC").fetchall()
        return [dict(row) for row in rows]


def get_metrics(db_path):
    requests = get_history(db_path, limit=10000)
    logs = get_logs(db_path)
    total = len(requests)
    success_count = sum(1 for row in requests if row["status"] == "Success")
    failed_count = sum(1 for row in requests if row["status"] == "Failure")
    avg_time = (
        sum(row["execution_time_ms"] for row in logs) / len(logs) / 1000
        if logs
        else 0
    )

    return {
        "total_requests": total,
        "successful_automations": success_count,
        "failed_automations": failed_count,
        "average_execution_time": round(avg_time, 2),
        "estimated_hours_saved": round(sum(row["hours_saved"] for row in requests), 2),
        "automation_rate": round((success_count / total) * 100, 2) if total else 0,
        "estimated_cost_savings": round(sum(row["cost_savings"] for row in requests), 2),
        "estimated_ai_cost": round(sum(row["estimated_cost"] for row in requests), 6),
    }


def save_report(db_path, report):
    summary = json.dumps(report["metrics"])
    with closing(connect(db_path)) as conn:
        conn.execute(
            """
            INSERT INTO weekly_reports
            (generated_at, period_start, period_end, local_pdf_path, google_doc_url, summary_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                report["metrics"]["period_start"],
                report["metrics"]["period_end"],
                report["pdf_path"],
                report.get("google_doc_url", ""),
                summary,
            ),
        )
        conn.commit()


def get_reports(db_path):
    with closing(connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT * FROM weekly_reports ORDER BY generated_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]
