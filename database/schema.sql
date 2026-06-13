PRAGMA foreign_keys = ON;

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
    estimated_cost REAL DEFAULT 0,
    FOREIGN KEY(request_id) REFERENCES automation_requests(id)
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
