import argparse
import sys
from models import RunMode


def parse_args() -> RunMode:
    parser = argparse.ArgumentParser(
        description="Shift Schedule Notification Bot",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--production", action="store_true",
                        help="Send real notifications (required for any send)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview what would be sent — no send, no DB write")
    parser.add_argument("--force", action="store_true",
                        help="Bypass deduplication — resend all (requires --production)")
    parser.add_argument("--employee", metavar="NAME",
                        help="Send to one employee only (requires --production)")
    parser.add_argument("--reload-schedule", action="store_true",
                        help="Validate XLSX and clear dedup records for its dates")

    args = parser.parse_args()

    # Validate combinations
    if args.force and not args.production:
        parser.error("--force requires --production")

    if args.employee and not args.production:
        parser.error("--employee requires --production")

    if args.dry_run and args.production:
        parser.error("--dry-run and --production are mutually exclusive")

    if args.reload_schedule and args.production:
        parser.error("--reload-schedule and --production are mutually exclusive")

    # Determine mode
    if args.reload_schedule:
        mode = "reload_schedule"
    elif args.dry_run:
        mode = "dry_run"
    elif args.production:
        mode = "production"
    else:
        mode = "health"

    return RunMode(
        mode=mode,
        employee=args.employee,
        force=args.force,
        dry_run=args.dry_run,
    )
