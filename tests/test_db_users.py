"""
Tests for db.py user/conversation functions added in S005.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db import (
    init_users_table,
    init_conversations_table,
    get_user,
    upsert_user,
    set_user_role,
    get_conversation_state,
    set_conversation_state,
)


@pytest.fixture()
def db(tmp_path):
    path = str(tmp_path / "test.db")
    init_users_table(path)
    init_conversations_table(path)
    return path


# ---------------------------------------------------------------------------
# upsert_user
# ---------------------------------------------------------------------------

def test_upsert_creates_user_with_pending_role(db):
    user = upsert_user(db, "1", "Тест Тестенко")
    assert user["telegram_id"] == "1"
    assert user["role"] == "pending"
    assert user["full_name"] == "Тест Тестенко"


def test_upsert_updates_name_preserves_role(db):
    upsert_user(db, "2", "Старе Ім'я")
    set_user_role(db, "2", "staff")
    user = upsert_user(db, "2", "Нове Ім'я")
    assert user["full_name"] == "Нове Ім'я"
    assert user["role"] == "staff"       # role must not be reset


def test_upsert_idempotent_same_data(db):
    upsert_user(db, "3", "Same")
    upsert_user(db, "3", "Same")
    assert get_user(db, "3")["full_name"] == "Same"


# ---------------------------------------------------------------------------
# get_user
# ---------------------------------------------------------------------------

def test_get_user_returns_none_for_unknown(db):
    assert get_user(db, "nonexistent") is None


# ---------------------------------------------------------------------------
# set_user_role
# ---------------------------------------------------------------------------

def test_set_user_role_returns_true_on_success(db):
    upsert_user(db, "4", "Worker")
    assert set_user_role(db, "4", "head") is True
    assert get_user(db, "4")["role"] == "head"


def test_set_user_role_returns_false_for_unknown(db):
    assert set_user_role(db, "99999", "staff") is False


# ---------------------------------------------------------------------------
# conversation state
# ---------------------------------------------------------------------------

def test_get_conversation_state_returns_idle_for_new_user(db):
    state = get_conversation_state(db, "5")
    assert state["state"] == "idle"
    assert state["context_json"] == "{}"


def test_set_and_get_conversation_state(db):
    set_conversation_state(db, "6", "awaiting_date", '{"draft": true}')
    state = get_conversation_state(db, "6")
    assert state["state"] == "awaiting_date"
    assert state["context_json"] == '{"draft": true}'


def test_set_conversation_state_idempotent_update(db):
    set_conversation_state(db, "7", "step1", "{}")
    set_conversation_state(db, "7", "step2", '{"x": 1}')
    state = get_conversation_state(db, "7")
    assert state["state"] == "step2"
    assert state["context_json"] == '{"x": 1}'
