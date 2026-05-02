# Shift Schedule Notification Bot

Sends one Telegram message per duty shift to a shared staff group. Runs automatically via a Docker cron service locally, or as a cPanel cron job on Namecheap in production.

---

## For IT Owner

### 0. Telegram Bot Setup

    Open Telegram and search for @BotFather (look for the official blue verified checkmark).
    Press Start and type the command /newbot.
    Give your bot a display name (e.g., "Shift Notifications").
    Give it a unique username that must end in bot (e.g., MyCompanyShiftBot).
    BotFather will reply with a long string of characters called the HTTP API Token (it looks like 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11).

### 1. Telegram Group Setup (once)

1. Create a closed Telegram group and add all staff members.
2. Add your bot to the group and promote it to Administrator.
3. Get the group ID — send any message to the group, then open:
   
   [https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates](TG URL with YOUR_BOT_TOKEN)
   
Find the `"chat"` object and copy the `"id"` (starts with a minus, e.g. `-1001234567890`).

### 2. Place data files

Put these files in the `data/` folder — no rebuild needed when they change:

```
data/
├── schedule.xlsx              ← copy monthly XLSX here
├── schedule_mapping.json      ← column name config (copy from .example, edit once)
├── shift_bot.db               ← auto-created on first run
└── logs/                      ← auto-created on first run
```

Copy the mapping example and open it in a text editor:

```bash
cp data/schedule_mapping.json.example data/schedule_mapping.json
```

Edit two things to match your XLSX file:
- `header_row` — the row number where column headers are (open the XLSX and count)
- `department_columns` — open the XLSX, go to that header row, and copy each department column name exactly as written, one per line

Leave `date_column` and `day_type_column` unchanged unless your XLSX uses different names for those columns.

### 3. Configure environment

```bash
cp .env.example .env
```

Fill in the two values — everything else is pre-set:

```
TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here
TELEGRAM_GROUP_CHAT_ID=-1001234567890
TZ=Europe/Kyiv
```

### 4. Build and verify setup

```bash
docker compose build  --no-cache
docker compose run --rm bot python main.py
```

All lines should show ✅. If `❌ missing required header: 'X'` appears, open `data/schedule_mapping.json` and fix the column name under `department_columns` to match what is written in your XLSX exactly.

### 5. Preview before sending

```bash
docker compose run --rm bot python main.py --dry-run
```

Review the output — each shift block shows the employee name, date, and the exact message that will be sent to the group.

### 10. Local automation (cron service)

Default is to start the cron service once and let it fire automatically.

```bash
docker compose up -d cron
```

The cron service runs in the background and restarts automatically if Docker restarts.

**Watch the cron logs:**
```bash
docker compose logs -f cron
```

**Change the schedule:**

Open `data/schedule_mapping.json` and edit the `shift_hours` section, then reload the cron service:

```bash
docker compose restart cron
```

> The cron fires at these times, in the timezone set by `TZ` in your `.env` (e.g. `TZ=Europe/Kyiv`).

⚠️ **If the new fire time has already passed today**, the cron will not send until tomorrow.
Run manually to send immediately:
```bash
docker compose run --rm bot python main.py --production
```

**Full workflow when correcting a shift that was already notified:**
```bash
# 1. Edit data/schedule_mapping.json (change shift_hours or day types)
# 2. Edit data/schedule.xlsx if day type changed
# 3. Clear dedup so the bot will resend
docker compose run --rm bot python main.py --reload-schedule
# 4. Reload cron with new schedule
docker compose restart cron
# 5. If new fire time already passed — send now
docker compose run --rm bot python main.py --production
```

**Verify container time before go-live:**
```bash
docker compose run --rm bot python main.py --health
```
Check the `[TIMEZONE]` line — the timezone and local time shown must match your wall clock. If the timezone is wrong, update `TZ` in `.env` and restart. If the time itself is wrong, check your system clock and Docker daemon.

**Stop the cron service:**
```bash
docker compose stop cron
```

### 9. Update schedule monthly

When a new monthly XLSX is ready:

1. Copy the new file to `data/schedule.xlsx`
2. Run `--reload-schedule` to clear the previous month's dedup records:
```bash
docker compose run --rm bot python main.py --reload-schedule
```

3. Run `--dry-run` to verify the new schedule looks correct
4. Run `--production` to send

### 6. Send notifications manually

```bash
docker compose run --rm bot python main.py --production
```

Sends one Telegram message per shift to the group. Each message follows this format:

```
Зміна: Приймальне відділення 07-04-2026
Іваненко О.В. заступає на зміну замість Петренко А.С.

Наступна зміна:
08-04-2026 о 17:00 — Сидоренко В.М.
```

The bot skips shifts already sent (deduplication) — safe to re-run if cron fires twice.

### 7. Resend manually for one person

```bash
docker compose run --rm bot python main.py --production --employee "Іваненко О.В."
```

Sends only that person's shift notification. Useful if a message was missed or failed.

### 8. Force resend all manually

```bash
docker compose run --rm bot python main.py --production --force
```

Ignores deduplication and resends all shifts. Use after uploading a corrected XLSX.


---

## For Developer

### Required XLSX column names

Configured in `data/schedule_mapping.json` (see `data/schedule_mapping.json.example`). 

The parser reads `header_row`, `date_column`, `day_type_column`, and `department_columns` from that file at startup — no code change needed when column names change.

### First-time setup

```bash
docker compose build
docker compose run --rm bot python tests/create_fixture.py
```
```bash
docker compose run --rm bot pytest
```
It collects and runs every file matching tests/test_*.py, prints results, then the container disappears. Nothing is left running afterward.

### CLI reference

| Command                                      | Effect                               |
|----------------------------------------------|--------------------------------------|
| `python main.py --health`                    | Health check — config, DB, XLSX, timezone |
| `python main.py`                             | Same as `--health` (default)         |
| `python main.py --dry-run`                   | Preview shift data, no sends         |
| `python main.py --production`                | Send notifications to group          |
| `python main.py --production --employee "X"` | Send for one employee only           |
| `python main.py --production --force`        | Resend all, ignore deduplication     |
| `python main.py --reload-schedule`           | Clear dedup records so cron re-sends |
| `python main.py --reload-schedule --dry-run` | Preview what would be cleared        |

### Project structure

```
Shedule_bot/
├── main.py               — entry point
├── models.py             — Shift, ShiftContext, RunMode dataclasses
├── config.py             — env var loading and validation
├── cli.py                — argument parsing
├── db.py                 — SQLite access (all SQL lives here)
├── schedule_parser.py    — XLSX parser (reads column config from schedule_mapping.json)
├── shift_logic.py        — pure prev/next shift computation
├── messenger/
│   ├── gateway.py        — MessengerGateway abstract interface
│   ├── telegram_adapter.py
│   └── viber_adapter.py
├── tests/
│   ├── create_fixture.py — run once to generate test fixtures
│   ├── fixtures/         — generated test data (not committed)
│   └── test_*.py
├── data/                 — IT-managed files (not committed)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Coming next — S004b

Production deploy: Namecheap cPanel setup, venv, cron job configuration, hardening.
