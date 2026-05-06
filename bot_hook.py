#!/opt/alt/python311/bin/python3.11
"""
Telegram webhook handler — CGI entry point.
Symlink from ~/public_html/cgi-bin/bot_hook.py to ~/Shedule_bot/bot_hook.py.
See readme_WEBHOOK.md for setup instructions.
"""
import json
import os
import sys

_ROOT = os.path.dirname(os.path.realpath(__file__))
_VENV = os.path.join(_ROOT, "venv", "lib",
                     f"python{sys.version_info.major}.{sys.version_info.minor}",
                     "site-packages")
if os.path.isdir(_VENV):
    sys.path.insert(0, _VENV)
sys.path.insert(0, _ROOT)

import requests

from db import (
    init_users_table, init_conversations_table,
    get_user, upsert_user, set_user_role,
)

VALID_ROLES = ("pending", "staff", "head", "it")


def _send(token: str, chat_id: str, text: str) -> None:
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
    except Exception:
        pass


def _cmd_draft(token: str, chat_id: str) -> None:
    sheet_id = os.environ.get("GOOGLE_SHEET_ID", "")
    creds = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not sheet_id or not creds:
        _send(token, chat_id, "❌ GOOGLE_SHEET_ID або GOOGLE_SERVICE_ACCOUNT_JSON не налаштовано.")
        return

    mapping_path = os.path.join(_ROOT, "data", "schedule_mapping.json")
    try:
        with open(mapping_path, encoding="utf-8") as f:
            mapping = json.load(f)
    except Exception as exc:
        _send(token, chat_id, f"❌ Не вдалось прочитати schedule_mapping.json: {exc}")
        return

    staff_tab = mapping.get("scheduler_staff_tab", "Staff")
    schedule_tab = mapping.get("scheduler_schedule_tab", "Draft")
    output_tab = mapping.get("scheduler_output_tab", "Draft-by-bot")
    month_cell = mapping.get("scheduler_month_cell", "A1")
    year_cell = mapping.get("scheduler_year_cell", "B1")

    from google_sheets_adapter import get_staff_list, get_schedule_grid, read_cell, write_schedule_grid
    from schedule_generator import UA_MONTHS, generate_schedule

    try:
        month_str = read_cell(sheet_id, schedule_tab, month_cell, creds).strip().lower()
        year_str = read_cell(sheet_id, schedule_tab, year_cell, creds).strip()
    except Exception as exc:
        _send(token, chat_id, f"❌ Не вдалось прочитати місяць/рік з Google Sheets: {exc}")
        return

    if month_str not in UA_MONTHS:
        _send(token, chat_id, f"❌ Невідома назва місяця: '{month_str}'. Очікується українська назва (наприклад, 'червень').")
        return

    try:
        staff_list = get_staff_list(sheet_id, staff_tab, creds)
        template_grid = get_schedule_grid(sheet_id, schedule_tab, creds)
    except Exception as exc:
        _send(token, chat_id, f"❌ Не вдалось прочитати дані з Google Sheets: {exc}")
        return

    try:
        filled_grid = generate_schedule(staff_list, template_grid, mapping)
    except Exception as exc:
        _send(token, chat_id, f"❌ Помилка генерації розкладу: {exc}")
        return

    try:
        write_schedule_grid(sheet_id, output_tab, filled_grid, creds)
    except Exception as exc:
        _send(token, chat_id, f"❌ Не вдалось записати результат до Google Sheets: {exc}")
        return

    _send(token, chat_id, f"✅ Чернетку розкладу на {month_str} {year_str} записано у вкладку '{output_tab}'.")


def _handle(update: dict, token: str, db_path: str) -> None:
    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    from_user = message.get("from", {})
    telegram_id = str(from_user.get("id", ""))
    if not telegram_id:
        return

    first = from_user.get("first_name", "")
    last = from_user.get("last_name", "")
    full_name = f"{first} {last}".strip() or telegram_id
    chat_id = str(message.get("chat", {}).get("id", telegram_id))
    text = (message.get("text") or "").strip()

    user = upsert_user(db_path, telegram_id, full_name)
    role = user["role"]

    if text.startswith("/start"):
        _send(token, chat_id,
              f"👋 Вітаю, {full_name}!\n"
              f"Ваш Telegram ID: {telegram_id}\n"
              f"Роль: {role}\n"
              f"Використайте /help для списку команд.")

    elif text.startswith("/whoami"):
        _send(token, chat_id,
              f"ID: {telegram_id}\nІм'я: {full_name}\nРоль: {role}")

    elif text.startswith("/help"):
        lines = [
            "/start — реєстрація",
            "/whoami — ваш профіль",
            "/help — допомога",
        ]
        if role == "head":
            lines.append("/draft — згенерувати чернетку розкладу")
        if role == "it":
            lines.append(f"/setrole <telegram_id> <role> — призначити роль ({', '.join(VALID_ROLES)})")
        _send(token, chat_id, "\n".join(lines))

    elif text.startswith("/draft"):
        if role != "head":
            _send(token, chat_id, "⛔ Не авторизовано.")
        else:
            _cmd_draft(token, chat_id)

    elif text.startswith("/setrole"):
        if role != "it":
            _send(token, chat_id, "⛔ Не авторизовано.")
        else:
            parts = text.split()
            if len(parts) != 3 or parts[2] not in VALID_ROLES:
                _send(token, chat_id,
                      f"Використання: /setrole <telegram_id> <role>\n"
                      f"Ролі: {', '.join(VALID_ROLES)}")
            else:
                target_id, new_role = parts[1], parts[2]
                if set_user_role(db_path, target_id, new_role):
                    _send(token, chat_id, f"✅ Роль {target_id} оновлено: {new_role}")
                else:
                    _send(token, chat_id, f"⚠️ Користувача {target_id} не знайдено.")

    else:
        _send(token, chat_id, "Невідома команда. Використайте /help.")


def main() -> None:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_ROOT, ".env"))

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    secret = os.environ.get("WEBHOOK_SECRET_TOKEN", "")
    db_path = os.environ.get("DB_PATH", "")

    # Validate secret before any output — return 403 to Telegram if wrong
    incoming_secret = os.environ.get("HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN", "")
    if secret and incoming_secret != secret:
        sys.stdout.write("Status: 403 Forbidden\r\nContent-Type: application/json\r\n\r\n{}")
        sys.exit(0)

    # Respond 200 immediately — Telegram stops retrying once it gets 200
    sys.stdout.write("Content-Type: application/json\r\n\r\n{}")
    sys.stdout.flush()

    if not token or not db_path:
        sys.exit(0)

    try:
        content_length = int(os.environ.get("CONTENT_LENGTH", 0))
        body = sys.stdin.read(content_length) if content_length > 0 else ""
        update = json.loads(body) if body else {}
    except Exception:
        sys.exit(0)

    init_users_table(db_path)
    init_conversations_table(db_path)

    try:
        _handle(update, token, db_path)
    except Exception as exc:
        try:
            import logging
            log_dir = os.environ.get("LOG_DIR", "/tmp")
            os.makedirs(log_dir, exist_ok=True)
            logging.basicConfig(
                filename=os.path.join(log_dir, "webhook.log"),
                level=logging.ERROR,
            )
            logging.error("webhook handler error: %s", exc)
        except Exception:
            pass


if __name__ == "__main__":
    main()
