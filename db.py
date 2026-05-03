import sqlite3
from datetime import datetime, timezone
from typing import Optional


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: str) -> None:
    with _connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_name TEXT    NOT NULL,
                shift_date    TEXT    NOT NULL,
                messenger     TEXT    NOT NULL,
                sent_at       TEXT    NOT NULL,
                status        TEXT    NOT NULL,
                error         TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_name TEXT    NOT NULL,
                replied_at    TEXT    NOT NULL,
                message       TEXT
            )
        """)
    init_users_table(db_path)
    init_conversations_table(db_path)


def was_notified(db_path: str, employee_name: str, shift_date: str) -> bool:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM notifications WHERE employee_name=? AND shift_date=? AND status='ok'",
            (employee_name, shift_date),
        ).fetchone()
    return row is not None


def record_notification(db_path: str, employee_name: str, shift_date: str,
                        messenger: str, status: str, error: Optional[str] = None) -> None:
    sent_at = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO notifications (employee_name, shift_date, messenger, sent_at, status, error) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (employee_name, shift_date, messenger, sent_at, status, error),
        )


def get_last_run_summary(db_path: str) -> dict:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT sent_at FROM notifications ORDER BY sent_at DESC LIMIT 1"
        ).fetchone()
        if not row:
            return {"sent_at": None, "total": 0, "ok": 0, "fail": 0}
        last_sent_at = row[0]
        # Batch = same sent_at prefix (same second)
        prefix = last_sent_at[:19]
        counts = conn.execute(
            "SELECT status, COUNT(*) FROM notifications WHERE sent_at LIKE ? GROUP BY status",
            (f"{prefix}%",),
        ).fetchall()
    summary = {"sent_at": prefix, "total": 0, "ok": 0, "fail": 0}
    for status, count in counts:
        summary[status] = count
        summary["total"] += count
    return summary


def get_pending_count(db_path: str, shifts: list) -> int:
    count = 0
    for shift in shifts:
        if not was_notified(db_path, shift.employee_name, shift.shift_date):
            count += 1
    return count


def clear_notifications_for_dates(db_path: str, dates: list) -> int:
    placeholders = ",".join("?" * len(dates))
    with _connect(db_path) as conn:
        cursor = conn.execute(
            f"DELETE FROM notifications WHERE shift_date IN ({placeholders})",
            dates,
        )
    return cursor.rowcount


# --- S005: users + conversation state ---

def init_users_table(db_path: str) -> None:
    with _connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id   TEXT PRIMARY KEY,
                full_name     TEXT NOT NULL,
                role          TEXT NOT NULL DEFAULT 'pending',
                registered_at TEXT NOT NULL
            )
        """)


def init_conversations_table(db_path: str) -> None:
    with _connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                telegram_id  TEXT PRIMARY KEY,
                state        TEXT NOT NULL DEFAULT 'idle',
                context_json TEXT NOT NULL DEFAULT '{}',
                updated_at   TEXT NOT NULL
            )
        """)


def get_user(db_path: str, telegram_id: str) -> Optional[dict]:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT telegram_id, full_name, role, registered_at FROM users WHERE telegram_id=?",
            (telegram_id,),
        ).fetchone()
    if row is None:
        return None
    return {"telegram_id": row[0], "full_name": row[1], "role": row[2], "registered_at": row[3]}


def upsert_user(db_path: str, telegram_id: str, full_name: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO users (telegram_id, full_name, role, registered_at) VALUES (?, ?, 'pending', ?) "
            "ON CONFLICT(telegram_id) DO UPDATE SET full_name=excluded.full_name",
            (telegram_id, full_name, now),
        )
    return get_user(db_path, telegram_id)


def set_user_role(db_path: str, telegram_id: str, role: str) -> bool:
    with _connect(db_path) as conn:
        cursor = conn.execute(
            "UPDATE users SET role=? WHERE telegram_id=?",
            (role, telegram_id),
        )
    return cursor.rowcount > 0


def get_conversation_state(db_path: str, telegram_id: str) -> dict:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT state, context_json FROM conversations WHERE telegram_id=?",
            (telegram_id,),
        ).fetchone()
    if row is None:
        return {"state": "idle", "context_json": "{}"}
    return {"state": row[0], "context_json": row[1]}


def set_conversation_state(db_path: str, telegram_id: str, state: str, context_json: str = "{}") -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO conversations (telegram_id, state, context_json, updated_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(telegram_id) DO UPDATE SET "
            "state=excluded.state, context_json=excluded.context_json, updated_at=excluded.updated_at",
            (telegram_id, state, context_json, now),
        )
