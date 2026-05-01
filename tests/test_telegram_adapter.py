import os
import sys
from unittest.mock import MagicMock, patch
import pytest
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from messenger.telegram_adapter import TelegramAdapter


@pytest.fixture
def adapter():
    return TelegramAdapter("test-token-123")


def _mock_response(ok_json: dict, status_code: int = 200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = ok_json
    resp.raise_for_status = MagicMock()
    return resp


def test_send_success(adapter):
    # Happy path — Telegram returns ok:true, no exception raised
    with patch("requests.post") as mock_post:
        mock_post.return_value = _mock_response({"ok": True, "result": {}})
        adapter.send("-1001234567890", "Test message")
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    assert "sendMessage" in call_kwargs[0][0]
    assert call_kwargs[1]["json"]["chat_id"] == "-1001234567890"
    assert call_kwargs[1]["json"]["text"] == "Test message"


def test_send_raises_on_http_error(adapter):
    # HTTP error (e.g. 429) is wrapped in a sanitized RuntimeError — no URL or token exposed
    with patch("requests.post") as mock_post:
        resp = _mock_response({}, status_code=429)
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "429 Too Many Requests"
        )
        mock_post.return_value = resp
        with pytest.raises(RuntimeError, match="Telegram send failed"):
            adapter.send("-1001234567890", "Test message")


def test_send_raises_on_connection_error(adapter):
    # DNS/network failure is wrapped in a sanitized RuntimeError — token never appears in message
    with patch("requests.post", side_effect=requests.exceptions.ConnectionError(
        "Failed to resolve 'api.telegram.org/botSECRET_TOKEN/sendMessage'"
    )):
        with pytest.raises(RuntimeError) as exc_info:
            adapter.send("-1001234567890", "Test message")
        assert "SECRET_TOKEN" not in str(exc_info.value)
        assert "Telegram send failed" in str(exc_info.value)


def test_send_token_not_in_exception(adapter):
    # BUG-S004-001 regression: token must never appear in logged exception string
    with patch("requests.post", side_effect=requests.exceptions.ConnectionError(
        "Max retries exceeded with url: /botSECRET_TOKEN/sendMessage"
    )):
        with pytest.raises(RuntimeError) as exc_info:
            adapter.send("-1001234567890", "Test message")
        assert "SECRET_TOKEN" not in str(exc_info.value)


def test_send_raises_on_telegram_api_error(adapter):
    # HTTP 200 but Telegram returns ok:false — must raise with description
    with patch("requests.post") as mock_post:
        mock_post.return_value = _mock_response({"ok": False, "description": "Bad Request: chat not found"})
        with pytest.raises(RuntimeError, match="chat not found"):
            adapter.send("-1001234567890", "Test message")


def test_health_check_returns_true_when_ok(adapter):
    # Bot token is valid and getMe responds ok:true
    with patch("requests.get") as mock_get:
        mock_get.return_value = _mock_response({"ok": True, "result": {"username": "testbot"}})
        assert adapter.health_check() is True


def test_health_check_returns_false_on_network_error(adapter):
    # Network unreachable — health_check must return False, not raise
    with patch("requests.get", side_effect=Exception("connection refused")):
        assert adapter.health_check() is False


def test_health_check_returns_false_on_bad_token(adapter):
    # Invalid token — Telegram returns ok:false
    with patch("requests.get") as mock_get:
        mock_get.return_value = _mock_response({"ok": False, "description": "Unauthorized"})
        assert adapter.health_check() is False
