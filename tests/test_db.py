import os
import sys
import sqlite3
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db import (
    init_db, was_notified, record_notification,
    get_last_run_summary, get_pending_count, clear_notifications_for_dates
)
from models import Shift


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def sample_shifts():
    return [
        Shift("Alice Kovalenko", "Приймальне відділення", "labor",   "2026-04-01", "telegram", "-1001234567890"),
        Shift("Bob Petrenko",    "Анестезіологія",        "labor",   "2026-04-01", "telegram", "-1001234567890"),
        Shift("Alice Kovalenko", "Приймальне відділення", "holiday", "2026-04-02", "telegram", "-1001234567890"),
    ]


def test_db_created(db_path):
    # First run on a fresh server — DB file does not exist yet and must be created
    init_db(db_path)
    assert os.path.exists(db_path)


def test_schema_idempotent(db_path):
    # Cron runs init_db on every execution — second call must not corrupt the schema
    init_db(db_path)
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert "notifications" in tables
    assert "receipts" in tables
    conn.close()


def test_wal_mode(db_path):
    # WAL mode prevents read/write locking if cron overlaps with an IT health check
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    conn.close()
    assert mode == "wal"


def test_was_notified_false_when_empty(db_path):
    # Brand-new DB has no records — every shift is pending on the first run
    init_db(db_path)
    assert was_notified(db_path, "Alice Kovalenko", "2026-04-01") is False


def test_was_notified_true_after_ok_record(db_path):
    # Cron already sent successfully — same shift must not be sent again
    init_db(db_path)
    record_notification(db_path, "Alice Kovalenko", "2026-04-01", "telegram", "ok")
    assert was_notified(db_path, "Alice Kovalenko", "2026-04-01") is True


def test_was_notified_false_after_fail_record(db_path):
    # Previous send failed — shift stays pending so next cron run retries it
    init_db(db_path)
    record_notification(db_path, "Alice Kovalenko", "2026-04-01", "telegram", "fail", "timeout")
    assert was_notified(db_path, "Alice Kovalenko", "2026-04-01") is False


def test_clear_only_specified_dates(db_path):
    # IT uploads a corrected XLSX for Apr 1 only — Apr 2 records must stay untouched
    init_db(db_path)
    record_notification(db_path, "Alice Kovalenko", "2026-04-01", "telegram", "ok")
    record_notification(db_path, "Bob Petrenko",    "2026-04-02", "telegram", "ok")
    deleted = clear_notifications_for_dates(db_path, ["2026-04-01"])
    assert deleted == 1
    assert was_notified(db_path, "Bob Petrenko", "2026-04-02") is True


def test_get_pending_count(db_path, sample_shifts):
    # One shift already sent — pending count must reflect only the remaining two
    init_db(db_path)
    record_notification(db_path, "Alice Kovalenko", "2026-04-01", "telegram", "ok")
    pending = get_pending_count(db_path, sample_shifts)
    assert pending == 2  # Bob + Alice's 2026-04-02 shift


def test_last_run_summary_empty(db_path):
    # IT checks health on a fresh install — last-run summary returns safe zero values
    init_db(db_path)
    summary = get_last_run_summary(db_path)
    assert summary["sent_at"] is None
    assert summary["total"] == 0
