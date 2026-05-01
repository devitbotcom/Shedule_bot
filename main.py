import logging
import os
import sys
import time
from datetime import datetime, timezone

from cli import parse_args
from config import load_config
from db import (
    get_last_run_summary, get_pending_count, init_db,
    clear_notifications_for_dates, was_notified, record_notification,
)
from messenger.telegram_adapter import TelegramAdapter
from models import RunMode, ShiftContext
from schedule_parser import parse_schedule, load_mapping
from shift_logic import compute_contexts


def setup_logging(log_dir: str) -> None:
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"shift_bot_{timestamp}.log")
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


_DEFAULT_SHIFT_HOURS = {"labor": "17:00", "holiday": "09:00", "other": "09:00"}


def _mapping_path(config: dict) -> str:
    return os.path.join(os.path.dirname(config["XLSX_PATH"]), "schedule_mapping.json")


def _shift_hours(config: dict) -> dict:
    mapping = load_mapping(_mapping_path(config))
    hours = dict(_DEFAULT_SHIFT_HOURS)
    hours.update(mapping.get("shift_hours", {}))
    return hours


def _fmt_colleague(shift) -> str:
    if shift is None:
        return "-"
    return f"{shift.employee_name} ({shift.department}) — {shift.shift_date}"


def _format_message(ctx: ShiftContext, shift_hours: dict) -> str:
    s = ctx.shift
    date_display = datetime.strptime(s.shift_date, "%Y-%m-%d").strftime("%d-%m-%Y")

    # BUG-001: strip trailing period to avoid double period for names like "А.С."
    raw_prev = ctx.prev_colleague.employee_name if ctx.prev_colleague else "-"
    prev_name = raw_prev.rstrip(".")

    if ctx.next_colleague:
        n = ctx.next_colleague
        next_date = datetime.strptime(n.shift_date, "%Y-%m-%d").strftime("%d-%m-%Y")
        next_time = shift_hours.get(n.day_type, "09:00")
        next_line = f"{next_date} о {next_time} — {n.employee_name}"
    else:
        next_line = "-"

    return (
        f"Зміна: {s.department} {date_display}\n"
        f"{s.employee_name} заступає на зміну замість {prev_name}.\n"
        f"\n"
        f"Наступна зміна:\n"
        f"{next_line}"
    )


def run_health(config: dict) -> None:
    all_ok = True

    print("[CONFIG]   ✅ all variables loaded")

    # DB
    try:
        init_db(config["DB_PATH"])
        print("[DB]       ✅ shift_bot.db reachable, schema valid")
    except Exception as exc:
        print(f"[DB]       ❌ {exc}")
        all_ok = False

    # Telegram
    adapter = TelegramAdapter(config["TELEGRAM_BOT_TOKEN"])
    if adapter.health_check():
        print("[TELEGRAM] ✅ bot reachable, token valid")
    else:
        print("[TELEGRAM] ❌ bot not reachable or token invalid")
        all_ok = False

    # XLSX
    shifts = []
    try:
        shifts = parse_schedule(config["XLSX_PATH"], config["TELEGRAM_GROUP_CHAT_ID"], _mapping_path(config))
        dates = sorted({s.shift_date for s in shifts})
        employees = len({s.employee_name for s in shifts})
        print(f"[XLSX]     ✅ schedule.xlsx found — {employees} employees, {len(dates)} shift dates")
    except SystemExit:
        print("[XLSX]     ❌ see errors above")
        all_ok = False
    except RuntimeError as exc:
        print(f"[XLSX]     ❌ {exc}")
        all_ok = False

    # Last run + pending
    try:
        summary = get_last_run_summary(config["DB_PATH"])
        if summary["sent_at"]:
            print(f"[LAST RUN] {summary['sent_at']} — {summary['ok']} sent, {summary['fail']} failed")
        else:
            print("[LAST RUN] no runs recorded yet")

        if shifts:
            pending = get_pending_count(config["DB_PATH"], shifts)
            print(f"[PENDING]  {pending} shifts pending notification")
    except Exception as exc:
        print(f"[STATS]    ❌ {exc}")
        all_ok = False

    sys.exit(0 if all_ok else 1)


def run_dry_run(config: dict) -> None:
    shifts = parse_schedule(config["XLSX_PATH"], config["TELEGRAM_GROUP_CHAT_ID"], _mapping_path(config))
    contexts = compute_contexts(shifts)
    hours = _shift_hours(config)

    print(f"\n{'='*60}")
    print(f"DRY RUN — {len(contexts)} shifts found. No messages will be sent.")
    print(f"{'='*60}\n")

    for ctx in contexts:
        s = ctx.shift
        print(f"  Employee : {s.employee_name}")
        print(f"  Dept     : {s.department}  |  Day type: {s.day_type}  |  Date: {s.shift_date}")
        print(f"  Messenger: {s.messenger}  |  Contact: {s.contact_id}")
        print(f"  Prev     : {_fmt_colleague(ctx.prev_colleague)}")
        print(f"  Next     : {_fmt_colleague(ctx.next_colleague)}")
        print(f"  --- Message preview ---")
        print(_format_message(ctx, hours))
        print()

    sys.exit(0)


def run_reload_schedule(config: dict, dry_run: bool) -> None:
    shifts = parse_schedule(config["XLSX_PATH"], config["TELEGRAM_GROUP_CHAT_ID"], _mapping_path(config))
    dates = sorted({s.shift_date for s in shifts})

    if dry_run:
        print(f"[RELOAD DRY RUN] Would clear dedup records for {len(dates)} dates:")
        for d in dates:
            print(f"  {d}")
        print("No changes made.")
    else:
        deleted = clear_notifications_for_dates(config["DB_PATH"], dates)
        logging.info("Cleared %d notification record(s) for dates: %s", deleted, dates)
        print(f"[RELOAD] Cleared {deleted} record(s) for {len(dates)} dates. Cron will re-send on next --production run.")

    sys.exit(0)


def run_production(config: dict, run_mode: RunMode) -> None:
    from datetime import date as _date
    target_date = run_mode.date or _date.today().strftime("%Y-%m-%d")

    all_shifts = parse_schedule(config["XLSX_PATH"], config["TELEGRAM_GROUP_CHAT_ID"], _mapping_path(config))

    # AD-001: compute contexts on full month so prev/next resolve across date boundaries
    all_contexts = compute_contexts(all_shifts)

    # AD-001 + BUG-003: filter contexts (not input shifts) to target date
    contexts = [c for c in all_contexts if c.shift.shift_date == target_date]
    if not contexts:
        print(f"[PRODUCTION] No shifts found for date: {target_date}")
        sys.exit(0)

    # Filter by shift_type when set by gen_crontab (e.g. --shift-type labour)
    if run_mode.shift_type:
        contexts = [c for c in contexts if c.shift.day_type == run_mode.shift_type]
        if not contexts:
            print(f"[PRODUCTION] No {run_mode.shift_type} shifts found for date: {target_date}")
            sys.exit(0)

    # AD-004: apply employee filter after context computation
    if run_mode.employee:
        contexts = [c for c in contexts if c.shift.employee_name == run_mode.employee]
        if not contexts:
            print(f"[PRODUCTION] No shifts found for employee: {run_mode.employee} on {target_date}")
            sys.exit(1)

    adapter = TelegramAdapter(config["TELEGRAM_BOT_TOKEN"])
    hours = _shift_hours(config)
    sent = skipped = failed = 0

    for ctx in contexts:
        s = ctx.shift

        if not run_mode.force and was_notified(config["DB_PATH"], s.employee_name, s.shift_date):
            logging.info("Skip (already notified): %s %s", s.employee_name, s.shift_date)
            skipped += 1
            continue

        message = _format_message(ctx, hours)
        try:
            adapter.send(s.contact_id, message)
            record_notification(config["DB_PATH"], s.employee_name, s.shift_date, s.messenger, "ok")
            logging.info("Sent: %s %s", s.employee_name, s.shift_date)
            sent += 1
            time.sleep(1)  # Telegram: max 1 message/second to same chat
        except Exception as exc:
            record_notification(config["DB_PATH"], s.employee_name, s.shift_date, s.messenger, "fail", str(exc))
            logging.error("Failed: %s %s — %s", s.employee_name, s.shift_date, exc)
            failed += 1

    print(f"[PRODUCTION] sent={sent}  skipped={skipped}  failed={failed}")
    sys.exit(0 if failed == 0 else 1)


def main() -> None:
    run_mode = parse_args()
    config = load_config()
    setup_logging(config["LOG_DIR"])

    logging.info("Starting shift_bot | mode=%s", run_mode.mode)

    if run_mode.mode == "health":
        run_health(config)

    elif run_mode.mode == "dry_run":
        init_db(config["DB_PATH"])
        run_dry_run(config)

    elif run_mode.mode == "reload_schedule":
        init_db(config["DB_PATH"])
        run_reload_schedule(config, dry_run=run_mode.dry_run)

    elif run_mode.mode == "production":
        init_db(config["DB_PATH"])
        run_production(config, run_mode)


if __name__ == "__main__":
    main()
