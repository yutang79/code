import os
import sqlite3
from datetime import datetime
from config import TICKETS_DB, DEPARTMENT_OWNERS

class TicketSystem:
    """工单系统：自动创建、分配、状态流转"""

    def __init__(self):
        os.makedirs(os.path.dirname(TICKETS_DB), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(TICKETS_DB) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_no TEXT UNIQUE,
                    user      TEXT,
                    question  TEXT,
                    summary   TEXT,
                    department TEXT,
                    owner     TEXT,
                    context   TEXT,
                    status    TEXT DEFAULT 'open',
                    created_at TEXT,
                    updated_at TEXT
                )
            """)

    def create_ticket(self, user, question, summary, department, context=""):
        ticket_no = f"TK{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
        owner = DEPARTMENT_OWNERS.get(department, DEPARTMENT_OWNERS["Other"])
        now = datetime.now().isoformat(timespec="seconds")

        with sqlite3.connect(TICKETS_DB) as conn:
            conn.execute("""
                INSERT INTO tickets
                (ticket_no, user, question, summary, department, owner, context, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (ticket_no, user, question, summary, department, owner, context, now, now))

        # 这里可对接邮件 / 飞书 / 钉钉 webhook
        self._notify(ticket_no, owner, summary)

        return {
            "ticket_no": ticket_no,
            "department": department,
            "owner": owner,
            "status": "open",
            "created_at": now,
        }

    def _notify(self, ticket_no, owner, summary):
        # 演示：打印到控制台。生产环境替换为发送邮件或 webhook
        print(f"📨 通知 {owner} → 工单 {ticket_no}: {summary}")

    def list_tickets(self, status=None):
        with sqlite3.connect(TICKETS_DB) as conn:
            conn.row_factory = sqlite3.Row
            if status:
                rows = conn.execute(
                    "SELECT * FROM tickets WHERE status=? ORDER BY id DESC", (status,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM tickets ORDER BY id DESC"
                ).fetchall()
        return [dict(r) for r in rows]

    def update_status(self, ticket_no, status):
        with sqlite3.connect(TICKETS_DB) as conn:
            conn.execute(
                "UPDATE tickets SET status=?, updated_at=? WHERE ticket_no=?",
                (status, datetime.now().isoformat(timespec="seconds"), ticket_no),
            )
