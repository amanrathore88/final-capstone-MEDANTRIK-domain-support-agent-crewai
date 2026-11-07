-- SQLite Schema for Medantrik Assist Capstone (Demo Tickets & Auditing)

CREATE TABLE IF NOT EXISTS tickets (
    record_id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    status TEXT NOT NULL,
    resolution_time_hours INTEGER NOT NULL,
    days_since_created INTEGER NOT NULL,
    escalated INTEGER NOT NULL DEFAULT 0,
    product TEXT NOT NULL,
    reopen_count INTEGER NOT NULL DEFAULT 0,
    subject TEXT NOT NULL,
    synthetic INTEGER NOT NULL DEFAULT 1,
    escalation_score REAL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL DEFAULT 'Guest',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    sources TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT NOT NULL,
    action TEXT NOT NULL,
    from_status TEXT,
    to_status TEXT,
    actor TEXT NOT NULL DEFAULT 'system',
    details TEXT,
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets(category);
CREATE INDEX IF NOT EXISTS idx_audit_ticket ON audit_events(ticket_id);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
