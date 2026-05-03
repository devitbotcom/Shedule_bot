import argparse
import sys
from models import RunMode


def parse_args() -> RunMode:
    parser = argparse.ArgumentParser(
        description="Shift Schedule Notification Bot",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--health", action="store_true",
                        help="Run health check — config, DB, Telegram, XLSX (default when no flags given)")
    parser.add_argument("--production", action="store_true",
                        help="Send real notifications (required for any send)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview what would be sent — no send, no DB write")
    parser.add_argument("--force", action="store_true",
                        help="Bypass deduplication — resend all (requires --production)")
    parser.add_argument("--employee", metavar="NAME",
                        help="Send to one employee only (requires --production)")
    parser.add_argument("--date", metavar="YYYY-MM-DD",
                        help="Date to send notifications for (default: today, requires --production)")
    parser.add_argument("--shift-type", metavar="TYPE",
                        help="Only send shifts matching this day_type key from schedule_mapping.json\n"
                             "(set automatically by gen_crontab.py; requires --production)")
    parser.add_argument("--reload-schedule", action="store_true",
                        help="Validate XLSX and clear dedup records for its dates")
    parser.add_argument("--gen-crontab", action="store_true",
                        help="Print ready-to-paste cPanel cron entries calculated from shift_hours and server timezone")
    parser.add_argument("--verify-cron", action="store_true",
                        help="Send Telegram confirmation that cron is active (used by the verification cron entry)")

    args = parser.parse_args()

    # Validate combinations
    if args.gen_crontab and any([args.production, args.dry_run, args.reload_schedule, args.verify_cron]):
        parser.error("--gen-crontab cannot be combined with other modes")
    if args.verify_cron and any([args.production, args.dry_run, args.reload_schedule, args.gen_crontab]):
        parser.error("--verify-cron cannot be combined with other modes")

    if args.force and not args.production:
        parser.error("--force requires --production")

    if args.employee and not args.production:
        parser.error("--employee requires --production")

    if args.date and not args.production:
        parser.error("--date requires --production")

    if args.shift_type and not args.production:
        parser.error("--shift-type requires --production")

    if args.date:
        try:
            from datetime import datetime
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            parser.error(f"--date must be in YYYY-MM-DD format, got: {args.date}")

    if args.dry_run and args.production:
        parser.error("--dry-run and --production are mutually exclusive")

    if args.reload_schedule and args.production:
        parser.error("--reload-schedule and --production are mutually exclusive")

    # Determine mode
    if args.gen_crontab:
        mode = "gen_crontab"
    elif args.verify_cron:
        mode = "verify_cron"
    elif args.reload_schedule:
        mode = "reload_schedule"
    elif args.dry_run:
        mode = "dry_run"
    elif args.production:
        mode = "production"
    else:
        mode = "health"  # default, also triggered by --health

    return RunMode(
        mode=mode,
        employee=args.employee,
        date=args.date,
        shift_type=args.shift_type,
        force=args.force,
        dry_run=args.dry_run,
    )
