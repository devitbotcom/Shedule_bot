"""
Generates /app/crontab.generated from shift_hours in schedule_mapping.json.
Run by the cron container at startup before supercronic launches.
Changing shift_hours + docker compose restart cron is the only action IT needs.
"""
import json
import os
import pathlib
import sys

_mapping_path = pathlib.Path(
    os.path.dirname(os.environ.get("XLSX_PATH", "/data/schedule.xlsx")),
    "schedule_mapping.json",
)
_output_path = pathlib.Path(__file__).parent / "crontab.generated"

try:
    mapping = json.loads(_mapping_path.read_text(encoding="utf-8"))
except FileNotFoundError:
    print(f"[gen_crontab] ERROR: {_mapping_path} not found", file=sys.stderr)
    sys.exit(1)

shift_hours = mapping.get("shift_hours", {})
if not shift_hours:
    print("[gen_crontab] ERROR: shift_hours missing or empty in schedule_mapping.json", file=sys.stderr)
    sys.exit(1)

lines = [
    "# Auto-generated at container startup from data/schedule_mapping.json",
    "# Do not edit — change shift_hours in schedule_mapping.json, then: docker compose restart cron",
]
for day_type, time_str in shift_hours.items():
    try:
        h, m = time_str.split(":")
        lines.append(
            f"{int(m)} {int(h)} * * * python /app/main.py --production --shift-type {day_type}"
        )
    except ValueError:
        print(f"[gen_crontab] ERROR: invalid time '{time_str}' for day_type '{day_type}'", file=sys.stderr)
        sys.exit(1)

_output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"[gen_crontab] {len(shift_hours)} cron entries written to {_output_path}")
