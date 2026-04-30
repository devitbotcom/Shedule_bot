# Shift Schedule Notification Bot

Sends one Telegram message per duty shift to a shared staff group. Runs as a one-shot cron job on Namecheap cPanel (Python 3.11.14).

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
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
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
```

### 4. Build and verify setup

```bash
docker compose build
docker compose run --rm bot python main.py
```

All lines should show ✅. If `❌ missing required header: 'X'` appears, open `data/schedule_mapping.json` and fix the column name under `department_columns` to match what is written in your XLSX exactly.

### 5. Preview before sending

```bash
docker compose run --rm bot python main.py --dry-run
```

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
| `python main.py`                             | Health check — config, DB, XLSX      |
| `python main.py --dry-run`                   | Preview shift data, no sends         |
| `python main.py --production`                | Send notifications (S003)            |
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
