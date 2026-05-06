"""
Tests for bot_hook._handle — command dispatch and role gating.
No CGI environment required; _handle is a pure function.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bot_hook import _handle, VALID_ROLES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_update(text: str, telegram_id: str = "111", first: str = "Тест") -> dict:
    return {
        "message": {
            "from": {"id": int(telegram_id), "first_name": first, "last_name": ""},
            "chat": {"id": int(telegram_id)},
            "text": text,
        }
    }


class _FakeSend:
    """Captures all calls to _send without hitting the network."""

    def __init__(self):
        self.calls: list[tuple[str, str, str]] = []  # (token, chat_id, text)

    def __call__(self, token: str, chat_id: str, text: str) -> None:
        self.calls.append((token, chat_id, text))

    @property
    def last_text(self) -> str:
        return self.calls[-1][2] if self.calls else ""

    @property
    def count(self) -> int:
        return len(self.calls)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def db(tmp_path):
    from db import init_users_table, init_conversations_table
    path = str(tmp_path / "test.db")
    init_users_table(path)
    init_conversations_table(path)
    return path


@pytest.fixture()
def it_db(tmp_path):
    """DB with a pre-registered IT admin (id='999')."""
    from db import init_users_table, init_conversations_table, upsert_user, set_user_role
    path = str(tmp_path / "it.db")
    init_users_table(path)
    init_conversations_table(path)
    upsert_user(path, "999", "Admin")
    set_user_role(path, "999", "it")
    return path


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------

def test_start_registers_new_user_and_replies(db, monkeypatch):
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    _handle(_make_update("/start", telegram_id="42"), token="T", db_path=db)
    assert sent.count == 1
    assert "42" in sent.last_text          # telegram_id shown
    assert "pending" in sent.last_text     # default role


def test_start_preserves_existing_role(it_db, monkeypatch):
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    _handle(_make_update("/start", telegram_id="999"), token="T", db_path=it_db)
    assert "it" in sent.last_text


# ---------------------------------------------------------------------------
# /whoami
# ---------------------------------------------------------------------------

def test_whoami_returns_id_name_role(db, monkeypatch):
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    _handle(_make_update("/whoami", telegram_id="7"), token="T", db_path=db)
    txt = sent.last_text
    assert "7" in txt
    assert "pending" in txt


# ---------------------------------------------------------------------------
# /help
# ---------------------------------------------------------------------------

def test_help_pending_user_no_setrole(db, monkeypatch):
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    _handle(_make_update("/help", telegram_id="8"), token="T", db_path=db)
    assert "/setrole" not in sent.last_text


def test_help_it_user_includes_setrole(it_db, monkeypatch):
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    _handle(_make_update("/help", telegram_id="999"), token="T", db_path=it_db)
    assert "/setrole" in sent.last_text


# ---------------------------------------------------------------------------
# /setrole — role gating
# ---------------------------------------------------------------------------

def test_setrole_denied_for_pending(db, monkeypatch):
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    _handle(_make_update("/setrole 42 staff", telegram_id="42"), token="T", db_path=db)
    assert "⛔" in sent.last_text


def test_setrole_sets_role_as_it(it_db, monkeypatch):
    from db import upsert_user, get_user
    upsert_user(it_db, "55", "Target")
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    _handle(_make_update("/setrole 55 staff", telegram_id="999"), token="T", db_path=it_db)
    assert "✅" in sent.last_text
    assert get_user(it_db, "55")["role"] == "staff"


def test_setrole_invalid_role_shows_usage(it_db, monkeypatch):
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    _handle(_make_update("/setrole 999 superadmin", telegram_id="999"), token="T", db_path=it_db)
    assert "⛔" not in sent.last_text   # not a permission error
    assert "Використання" in sent.last_text


def test_setrole_unknown_target_warns(it_db, monkeypatch):
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    _handle(_make_update("/setrole 99999 staff", telegram_id="999"), token="T", db_path=it_db)
    assert "⚠️" in sent.last_text


# ---------------------------------------------------------------------------
# Unknown command
# ---------------------------------------------------------------------------

def test_unknown_command_suggests_help(db, monkeypatch):
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    _handle(_make_update("/unknown_xyz", telegram_id="3"), token="T", db_path=db)
    assert "/help" in sent.last_text


# ---------------------------------------------------------------------------
# No-crash guarantees
# ---------------------------------------------------------------------------

def test_handle_ignores_update_without_message(db, monkeypatch):
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    _handle({}, token="T", db_path=db)
    assert sent.count == 0


def test_handle_ignores_message_without_from(db, monkeypatch):
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    _handle({"message": {"chat": {"id": 1}, "text": "/start"}}, token="T", db_path=db)
    assert sent.count == 0


# ---------------------------------------------------------------------------
# /draft — role gating
# ---------------------------------------------------------------------------

@pytest.fixture()
def head_db(tmp_path):
    from db import init_users_table, init_conversations_table, upsert_user, set_user_role
    path = str(tmp_path / "head.db")
    init_users_table(path)
    init_conversations_table(path)
    upsert_user(path, "200", "Head User")
    set_user_role(path, "200", "head")
    return path


def test_draft_denied_for_pending(db, monkeypatch):
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    _handle(_make_update("/draft", telegram_id="42"), token="T", db_path=db)
    assert "⛔" in sent.last_text


def test_draft_denied_for_staff(tmp_path, monkeypatch):
    from db import init_users_table, init_conversations_table, upsert_user, set_user_role
    path = str(tmp_path / "staff.db")
    init_users_table(path)
    init_conversations_table(path)
    upsert_user(path, "300", "Staff User")
    set_user_role(path, "300", "staff")
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    _handle(_make_update("/draft", telegram_id="300"), token="T", db_path=path)
    assert "⛔" in sent.last_text


def test_draft_calls_cmd_draft_for_head(head_db, monkeypatch):
    called = []
    monkeypatch.setattr("bot_hook._cmd_draft", lambda t, c: called.append((t, c)))
    _handle(_make_update("/draft", telegram_id="200"), token="T", db_path=head_db)
    assert called == [("T", "200")]


def test_help_shows_draft_for_head(head_db, monkeypatch):
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    _handle(_make_update("/help", telegram_id="200"), token="T", db_path=head_db)
    assert "/draft" in sent.last_text


def test_help_hides_draft_for_pending(db, monkeypatch):
    sent = _FakeSend()
    monkeypatch.setattr("bot_hook._send", sent)
    _handle(_make_update("/help", telegram_id="42"), token="T", db_path=db)
    assert "/draft" not in sent.last_text
