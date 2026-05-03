from dataclasses import dataclass
from typing import Optional


@dataclass
class Shift:
    employee_name: str
    department: str        # XLSX column header, e.g. 'Приймальне відділення'
    day_type: str          # 'labor' | 'holiday' | 'other'
    shift_date: str        # ISO 8601: 'YYYY-MM-DD'
    messenger: str         # 'telegram' | 'viber'
    contact_id: str        # Telegram chat_id or Viber user ID


@dataclass
class ShiftContext:
    shift: Shift
    prev_colleague: Optional[Shift]   # None → display as '-'
    next_colleague: Optional[Shift]   # None → display as '-'


@dataclass
class RunMode:
    mode: str              # 'health' | 'dry_run' | 'production' | 'reload_schedule' | 'gen_crontab' | 'verify_cron' | 'register_webhook' | 'bootstrap_it'
    employee: Optional[str] = None
    date: Optional[str] = None       # ISO 8601 override; None = today
    shift_type: Optional[str] = None # day_type filter; None = all types (set by gen_crontab)
    force: bool = False
    dry_run: bool = False
    bootstrap_it: Optional[str] = None  # telegram_id for --bootstrap-it
