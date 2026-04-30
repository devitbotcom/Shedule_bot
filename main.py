import logging
import os
import sys
from datetime import datetime, timezone

from cli import parse_args
from config import load_config
from db import get_last_run_summary, get_pending_count, init_db, clear_notifications_for_dates
from schedule_parser import parse_schedule
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


def _fmt_colleague(shift) -> str:
    if shift is None:
        return "-"
    return f"{shift.employee_name} ({shift.department}) — {shift.shift_date}"


def _mapping_path(config: dict) -> str:
    return os.path.join(os.path.dirname(config["XLSX_PATH"]), "schedule_mapping.json")


def run_health(config: dict) -> None:
    all_ok = True

    # CONFIG already validated — always green here
    print("[CONFIG]  ✅ all variables loaded")

    # DB
    try:
        init_db(config["DB_PATH"])
        print("[DB]      ✅ shift_bot.db reachable, schema valid")
    except Exception as exc:
        print(f"[DB]      ❌ {exc}")
        all_ok = False

    # XLSX
    shifts = []
    try:
        shifts = parse_schedule(config["XLSX_PATH"], config["TELEGRAM_GROUP_CHAT_ID"], _mapping_path(config))
        dates = sorted({s.shift_date for s in shifts})
        employees = len({s.employee_name for s in shifts})
        print(f"[XLSX]    ✅ schedule.xlsx found — {employees} employees, {len(dates)} shift dates")
    except SystemExit:
        print("[XLSX]    ❌ see errors above")
        all_ok = False
    except RuntimeError as exc:
        print(f"[XLSX]    ❌ {exc}")
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
            print(f"[PENDING]  {pending} employees pending notification")
    except Exception as exc:
        print(f"[STATS]   ❌ {exc}")
        all_ok = False

    sys.exit(0 if all_ok else 1)


def run_dry_run(config: dict) -> None:
    shifts = parse_schedule(config["XLSX_PATH"], config["TELEGRAM_GROUP_CHAT_ID"], _mapping_path(config))
    contexts = compute_contexts(shifts)

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
        raise NotImplementedError("Production mode — implemented in Sprint 003")


if __name__ == "__main__":
    main()
