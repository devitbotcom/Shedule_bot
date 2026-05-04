import json
import logging
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
_VENV = os.path.join(_ROOT, "venv", "lib",
                     f"python{sys.version_info.major}.{sys.version_info.minor}",
                     "site-packages")
if os.path.isdir(_VENV):
    sys.path.insert(0, _VENV)
sys.path.insert(0, _ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(_ROOT, ".env"))

from bot_hook import _handle
from db import init_users_table, init_conversations_table

_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
_SECRET = os.environ.get("WEBHOOK_SECRET_TOKEN", "")
_DB_PATH = os.environ.get("DB_PATH", "")
_LOG_DIR = os.environ.get("LOG_DIR", "/tmp")

if _DB_PATH:
    init_users_table(_DB_PATH)
    init_conversations_table(_DB_PATH)


def application(environ, start_response):
    incoming_secret = environ.get("HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN", "")
    if _SECRET and incoming_secret != _SECRET:
        start_response("403 Forbidden", [("Content-Type", "application/json")])
        return [b"{}"]

    try:
        content_length = int(environ.get("CONTENT_LENGTH") or 0)
        body = environ["wsgi.input"].read(content_length) if content_length > 0 else b""
        update = json.loads(body) if body else {}
    except Exception:
        start_response("200 OK", [("Content-Type", "application/json")])
        return [b"{}"]

    start_response("200 OK", [("Content-Type", "application/json")])

    if _TOKEN and _DB_PATH:
        try:
            _handle(update, _TOKEN, _DB_PATH)
        except Exception as exc:
            try:
                os.makedirs(_LOG_DIR, exist_ok=True)
                logging.basicConfig(
                    filename=os.path.join(_LOG_DIR, "webhook.log"),
                    level=logging.ERROR,
                )
                logging.error("webhook handler error: %s", exc)
            except Exception:
                pass

    return [b"{}"]
