"""SQLite persistence for synthetic tickets, chat sessions, and audit events."""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any

from dataset import SUPPORT_TICKETS

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / ".runtime" / "medantrik_assist.db"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_escalation_score(escalated: bool, days_since_created: int, reopen_count: int) -> float:
    """Escalation heuristic combining status, recency, and reopen frequency."""
    score = 0.50 * int(escalated) + 0.30 * (min(days_since_created, 30) / 30.0) + 0.20 * (min(reopen_count, 3) / 3.0)
    return round(score, 6)


class Database:
    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path is not None else DEFAULT_DB_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(str(self.path), timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self) -> None:
        schema_file = Path(__file__).resolve().parent / "schema.sql"
        with open(schema_file, "r", encoding="utf-8") as f:
            sql = f.read()
        with self.connection() as conn:
            conn.executescript(sql)
        self.seed_if_empty()

    def seed_if_empty(self) -> int:
        with self.connection() as conn:
            cur = conn.execute("SELECT COUNT(*) AS c FROM tickets")
            count = cur.fetchone()["c"]
            if count == 0:
                return self.seed_tickets(SUPPORT_TICKETS)
            return count

    def seed_tickets(self, tickets: list[dict]) -> int:
        now = utc_now()
        with self.connection() as conn:
            for t in tickets:
                score = compute_escalation_score(
                    bool(t["escalated"]),
                    int(t["days_since_created"]),
                    int(t.get("reopen_count", 0)),
                )
                conn.execute(
                    """
                    INSERT OR REPLACE INTO tickets (
                        record_id, category, status, resolution_time_hours,
                        days_since_created, escalated, product, reopen_count,
                        subject, synthetic, escalation_score, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        t["record_id"],
                        t["category"],
                        t["status"],
                        t["resolution_time_hours"],
                        t["days_since_created"],
                        1 if t["escalated"] else 0,
                        t["product"],
                        t.get("reopen_count", 0),
                        t["subject"],
                        1 if t.get("synthetic", True) else 0,
                        score,
                        now,
                        now,
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO audit_events (
                        ticket_id, action, from_status, to_status, actor, details, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        t["record_id"],
                        "SEEDED",
                        None,
                        t["status"],
                        "system_seed",
                        f"Seed import: category={t['category']}, product={t['product']}",
                        now,
                    ),
                )
        return len(tickets)

    def get_ticket(self, record_id: str) -> dict | None:
        with self.connection() as conn:
            cur = conn.execute("SELECT * FROM tickets WHERE record_id = ?", (record_id.strip(),))
            row = cur.fetchone()
            if not row:
                return None
            res = dict(row)
            res["escalated"] = bool(res["escalated"])
            res["synthetic"] = bool(res["synthetic"])
            return res

    def list_tickets(
        self,
        status: str | None = None,
        category: str | None = None,
        product: str | None = None,
        search: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        query = "SELECT * FROM tickets WHERE 1=1"
        params: list[Any] = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if category:
            query += " AND category = ?"
            params.append(category)
        if product:
            query += " AND product = ?"
            params.append(product)
        if search:
            query += " AND (record_id LIKE ? OR subject LIKE ? OR category LIKE ? OR product LIKE ?)"
            s = f"%{search.strip()}%"
            params.extend([s, s, s, s])
        query += " ORDER BY record_id ASC LIMIT ?"
        params.append(limit)

        with self.connection() as conn:
            cur = conn.execute(query, params)
            rows = cur.fetchall()
            out = []
            for r in rows:
                d = dict(r)
                d["escalated"] = bool(d["escalated"])
                d["synthetic"] = bool(d["synthetic"])
                out.append(d)
            return out

    def create_ticket(
        self,
        category: str,
        subject: str,
        product: str = "NODex",
        status: str = "Open",
        escalated: bool = False,
        actor: str = "customer_ui",
        details: str = "User initiated ticket",
    ) -> dict:
        now = utc_now()
        with self.connection() as conn:
            cur = conn.execute("SELECT MAX(CAST(SUBSTR(record_id, 5) AS INTEGER)) as max_id FROM tickets")
            row = cur.fetchone()
            next_num = (row["max_id"] or 80) + 1
            record_id = f"MED-{next_num:04d}"

            score = compute_escalation_score(escalated, 0, 0)
            conn.execute(
                """
                INSERT INTO tickets (
                    record_id, category, status, resolution_time_hours,
                    days_since_created, escalated, product, reopen_count,
                    subject, synthetic, escalation_score, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (record_id, category, status, 24, 0, 1 if escalated else 0, product, 0, subject, 1, score, now, now),
            )
            conn.execute(
                """
                INSERT INTO audit_events (
                    ticket_id, action, from_status, to_status, actor, details, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (record_id, "CREATED", None, status, actor, details, now),
            )

        return self.get_ticket(record_id)  # type: ignore

    def update_ticket_status(
        self,
        record_id: str,
        new_status: str,
        actor: str = "demo_operator",
        details: str = "Manual status update",
    ) -> dict:
        current = self.get_ticket(record_id)
        if not current:
            raise KeyError(f"Ticket {record_id} does not exist")

        now = utc_now()
        escalated = 1 if new_status == "Escalated" else (1 if current["escalated"] else 0)
        reopen_count = current["reopen_count"] + 1 if (current["status"] in ("Resolved", "Closed") and new_status == "Open") else current["reopen_count"]
        score = compute_escalation_score(bool(escalated), current["days_since_created"], reopen_count)

        with self.connection() as conn:
            conn.execute(
                """
                UPDATE tickets
                SET status = ?, escalated = ?, reopen_count = ?, escalation_score = ?, updated_at = ?
                WHERE record_id = ?
                """,
                (new_status, escalated, reopen_count, score, now, record_id),
            )
            conn.execute(
                """
                INSERT INTO audit_events (
                    ticket_id, action, from_status, to_status, actor, details, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (record_id, "STATUS_CHANGE", current["status"], new_status, actor, details, now),
            )
        return self.get_ticket(record_id)  # type: ignore

    def get_audit_events(self, ticket_id: str) -> list[dict]:
        with self.connection() as conn:
            cur = conn.execute("SELECT * FROM audit_events WHERE ticket_id = ? ORDER BY id ASC", (ticket_id.strip(),))
            return [dict(r) for r in cur.fetchall()]

    def create_session(self, session_id: str, customer_name: str = "Guest") -> str:
        now = utc_now()
        with self.connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sessions (session_id, customer_name, created_at) VALUES (?, ?, ?)",
                (session_id, customer_name, now),
            )
        return session_id

    def get_session(self, session_id: str) -> dict | None:
        with self.connection() as conn:
            cur = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def add_message(self, session_id: str, role: str, content: str, sources: list[dict] | None = None) -> int:
        now = utc_now()
        self.create_session(session_id)
        sources_json = json.dumps(sources) if sources else None
        with self.connection() as conn:
            cur = conn.execute(
                "INSERT INTO messages (session_id, role, content, sources, created_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, role, content, sources_json, now),
            )
            return cur.lastrowid or 0

    def get_messages(self, session_id: str) -> list[dict]:
        with self.connection() as conn:
            cur = conn.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
            out = []
            for r in cur.fetchall():
                d = dict(r)
                if d["sources"]:
                    try:
                        d["sources"] = json.loads(d["sources"])
                    except Exception:
                        pass
                out.append(d)
            return out

    def get_metrics(self) -> dict:
        with self.connection() as conn:
            total = conn.execute("SELECT COUNT(*) AS c FROM tickets").fetchone()["c"]
            cur_status = conn.execute("SELECT status, COUNT(*) AS c FROM tickets GROUP BY status")
            statuses = {r["status"]: r["c"] for r in cur_status.fetchall()}
            cur_cat = conn.execute("SELECT category, COUNT(*) AS c FROM tickets GROUP BY category")
            categories = {r["category"]: r["c"] for r in cur_cat.fetchall()}
            cur_prod = conn.execute("SELECT product, COUNT(*) AS c FROM tickets GROUP BY product")
            products = {r["product"]: r["c"] for r in cur_prod.fetchall()}
            cur_esc = conn.execute("SELECT COUNT(*) AS c FROM tickets WHERE escalated = 1")
            escalated_count = cur_esc.fetchone()["c"]

            return {
                "total_tickets": total,
                "open_tickets": statuses.get("Open", 0),
                "in_progress_tickets": statuses.get("In Progress", 0),
                "escalated_tickets": escalated_count,
                "resolved_tickets": statuses.get("Resolved", 0),
                "closed_tickets": statuses.get("Closed", 0),
                "escalated_percentage": round(100.0 * escalated_count / max(total, 1), 2),
                "by_status": statuses,
                "by_category": categories,
                "by_product": products,
                "knowledge_topics": 12,
            }
