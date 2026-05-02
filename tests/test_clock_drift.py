import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from main import _check_clock_drift


def _api_response(utc_dt: datetime) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = {"utc_datetime": utc_dt.isoformat()}
    return resp


def test_clock_drift_ok_logs_info(caplog):
    world_time = datetime.now(timezone.utc)
    with patch("requests.get", return_value=_api_response(world_time)):
        with caplog.at_level(logging.INFO):
            _check_clock_drift()
    assert any("Clock drift OK" in r.message for r in caplog.records)
    assert not any(r.levelno == logging.WARNING for r in caplog.records)


def test_clock_drift_warning_when_delta_exceeds_threshold(caplog):
    world_time = datetime.now(timezone.utc) - timedelta(seconds=400)
    with patch("requests.get", return_value=_api_response(world_time)):
        with caplog.at_level(logging.WARNING):
            _check_clock_drift()
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any("Clock drift" in r.message for r in warnings)


def test_clock_drift_warning_when_api_unreachable(caplog):
    with patch("requests.get", side_effect=Exception("connection refused")):
        with caplog.at_level(logging.WARNING):
            _check_clock_drift()
    assert any("skipped" in r.message for r in caplog.records)


def test_clock_drift_does_not_raise_on_api_failure():
    with patch("requests.get", side_effect=Exception("timeout")):
        _check_clock_drift()  # must not raise
