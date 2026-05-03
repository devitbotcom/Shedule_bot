import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

import requests

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
    tz = os.environ.get("TZ", "(not set — using host timezone)")
    local_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[TIMEZONE] {tz} — {local_now} local")

    # Schedule config (D10)
    try:
        hours = _shift_hours(config)
        hours_str = "  ".join(f"{k}={hours.get(k, '?')}" for k in ("labor", "holiday", "other"))
        print(f"[SCHEDULE] shift_hours: {hours_str}")
    except Exception:
        print("[SCHEDULE] ❌ could not read schedule_mapping.json")

    # Server local time and TZ offset (D11)
    try:
        result = subprocess.run(
            ["bash", "-c", "unset TZ; date; date +%z; date +%Z"],
            capture_output=True, text=True, timeout=3,
        )
        lines = result.stdout.strip().splitlines()
        env_date, srv_offset_str, srv_abbr = lines[0], lines[1], lines[2]

        sign = 1 if srv_offset_str[0] == "+" else -1
        srv_offset_h = sign * (int(srv_offset_str[1:3]) + int(srv_offset_str[3:5]) / 60)
        bot_offset_h = datetime.now().astimezone().utcoffset().total_seconds() / 3600
        diff_h = bot_offset_h - srv_offset_h

        bot_abbr = datetime.now().astimezone().strftime("%Z")
        bot_utc = f"UTC{int(bot_offset_h):+d}"
        srv_utc = f"UTC{srv_offset_h:+.0f}"
        if diff_h > 0:
            label = f"bot leads server by {diff_h:.0f}h"
        elif diff_h < 0:
            label = f"server leads bot by {abs(diff_h):.0f}h"
        else:
            label = "bot and server clocks match"

        print(f"[ENV TIME]  {env_date}")
        print(f"[TZ OFFSET] {label} ({tz} {bot_abbr} {bot_utc} vs server {srv_abbr} {srv_utc})")
    except Exception:
        print("[ENV TIME]  ❌ could not read server local time")

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


def _shift_time_to_server(kyiv_hhmm: str, bot_offset_h: float, server_offset_h: float) -> tuple:
    h, m = map(int, kyiv_hhmm.split(":"))
    offset_minutes = round((bot_offset_h - server_offset_h) * 60)
    total = (h * 60 + m - offset_minutes) % (24 * 60)
    return total // 60, total % 60


def _check_clock_drift() -> None:
    try:
        resp = requests.get("https://worldtimeapi.org/api/timezone/UTC", timeout=5)
        world_utc = datetime.fromisoformat(resp.json()["utc_datetime"])
        delta = abs((datetime.now(timezone.utc) - world_utc).total_seconds())
        if delta > 300:
            logging.warning(
                "Clock drift: server deviates from world time by %.0fs — check server NTP or DST offset",
                delta,
            )
        else:
            logging.info("Clock drift OK: %.0fs", delta)
    except Exception:
        logging.warning("Clock drift check skipped — time API unreachable")


def run_production(config: dict, run_mode: RunMode) -> None:
    _check_clock_drift()

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


def run_gen_crontab(config: dict) -> None:
    install_root = os.path.dirname(os.path.dirname(config["XLSX_PATH"]))
    python_bin = os.path.join(install_root, "venv", "bin", "python")
    main_script = os.path.join(install_root, "main.py")
    tz = os.environ.get("TZ", "Europe/Kyiv")
    bot_offset_h = datetime.now().astimezone().utcoffset().total_seconds() / 3600
    hours = _shift_hours(config)

    server_offset_h = None
    server_now_hhmm = None
    offset_ok = False
    try:
        result = subprocess.run(
            ["bash", "-c", "unset TZ; date +%z; date +%H%M"],
            capture_output=True, text=True, timeout=3,
        )
        lines = result.stdout.strip().splitlines()
        offset_str, time_str = lines[0], lines[1]
        sign = 1 if offset_str[0] == "+" else -1
        server_offset_h = sign * (int(offset_str[1:3]) + int(offset_str[3:5]) / 60)
        server_now_hhmm = time_str.strip()
        offset_ok = True
    except Exception:
        pass

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    if offset_ok:
        diff_h = bot_offset_h - server_offset_h
        bot_abbr = datetime.now().astimezone().strftime("%Z")
        tz_header = (
            f"Kyiv={bot_abbr} UTC{int(bot_offset_h):+d} | "
            f"Server=UTC{int(server_offset_h):+d} | Offset={diff_h:.0f}h"
        )
    else:
        tz_header = "⚠️ Could not read server offset — replace <HOUR> and <MIN> manually"

    print(f"# Generated: {now_str} ({tz})")
    print(f"# {tz_header}")
    print(f"# Install: {install_root}")
    print(f"# Paste all entries into cPanel → Cron Jobs.")
    print(f"# Add the last entry too — remove it after the Telegram confirmation arrives.")
    print()

    def _entry(shift_type):
        hhmm = hours.get(shift_type, "09:00")
        if offset_ok:
            sh, sm = _shift_time_to_server(hhmm, bot_offset_h, server_offset_h)
            return f"{sm:2d} {sh:2d} * * *  TZ={tz} {python_bin} {main_script} --production --shift-type {shift_type}"
        return f"<MIN> <HOUR> * * *  TZ={tz} {python_bin} {main_script} --production --shift-type {shift_type}  # Kyiv={hhmm}"

    print("# Shift notifications")
    for st in hours.keys():
        print(_entry(st))
    print()

    print("# Log retention (weekly, Sunday)")
    print(f" 0  3 * * 0  find {config['LOG_DIR']} -name \"*.log\" -mtime +30 -delete")
    print()

    print("# Verification — REMOVE AFTER FIRST FIRE")
    if offset_ok:
        now_h, now_m = int(server_now_hhmm[:2]), int(server_now_hhmm[2:])
        verify_total = (now_h * 60 + now_m + 5) % (24 * 60)
        vh, vm = verify_total // 60, verify_total % 60
        print(f"{vm:2d} {vh:2d} * * *  TZ={tz} {python_bin} {main_script} --verify-cron")
    else:
        print(f"<MIN> <HOUR> * * *  TZ={tz} {python_bin} {main_script} --verify-cron")

    sys.exit(0)


def run_verify_cron(config: dict) -> None:
    adapter = TelegramAdapter(config["TELEGRAM_BOT_TOKEN"])
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    tz = os.environ.get("TZ", "")
    message = f"✅ Cron active — schedule configured\nVerified: {now_str} ({tz})"
    try:
        adapter.send(config["TELEGRAM_GROUP_CHAT_ID"], message)
        print("[VERIFY] ✅ Confirmation sent to Telegram group")
        sys.exit(0)
    except Exception as exc:
        logging.error("Verification send failed: %s", exc)
        sys.exit(1)


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

    elif run_mode.mode == "gen_crontab":
        run_gen_crontab(config)

    elif run_mode.mode == "verify_cron":
        run_verify_cron(config)


if __name__ == "__main__":
    main()
