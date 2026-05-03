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

### 9. Update schedule monthly (manually)

When a new monthly XLSX is ready:

1. Copy the new file to `data/schedule.xlsx`
2. Run `--reload-schedule` to clear the previous month's dedup records:
```bash
docker compose run --rm bot python main.py --reload-schedule
```

3. Run `--dry-run` to verify the new schedule looks correct
4. Run `--production` to send

### 6. Send notifications (manually)

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

### 7. Resend for one person (manually)

```bash
docker compose run --rm bot python main.py --production --employee "Іваненко О.В."
```

Sends only that person's shift notification. Useful if a message was missed or failed.

### 8. Force resend all (manually)

```bash
docker compose run --rm bot python main.py --production --force
```

Ignores deduplication and resends all shifts. Use after uploading a corrected XLSX.


---

## For Production (cPanel — Namecheap)

Docker is not available on shared hosting. The bot runs as a plain Python script under `venv`, triggered by cPanel cron jobs.

### P0. Prerequisites (once)

Configure SSH key access to your repository on the server via the cPanel terminal before running `git clone`. Without this, cloning a private repo will fail.

How to set it up in cPanel:

   ???



### P1. Clone the repository

```bash
cd ~
git clone <your-repo-url> shift_bot
cd shift_bot
```

### P2. Create virtual environment

The system `python3` on Namecheap shared hosting is 3.6 — too old. Use the hosted Python 3.11:

```bash
/opt/alt/python311/bin/python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### P3. Place data files

Upload these files to `~/shift_bot/data/` via cPanel File Manager or `scp`:

```
~/shift_bot/data/
├── schedule.xlsx
├── schedule_mapping.json      ← copy from .example, edit once
├── shift_bot.db               ← auto-created on first run
└── logs/                      ← auto-created on first run
```

### P4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` — use **absolute paths** and fill in your credentials:

```
XLSX_PATH=/home/<username>/shift_bot/data/schedule.xlsx
DB_PATH=/home/<username>/shift_bot/data/shift_bot.db
LOG_DIR=/home/<username>/shift_bot/data/logs
TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here
TELEGRAM_GROUP_CHAT_ID=-1001234567890
TZ=Europe/Kyiv
```

### P5. Verify setup

```bash
cd ~/shift_bot && source venv/bin/activate && python main.py --health
```

All lines should show ✅. Check that `[TIMEZONE]` shows `Europe/Kyiv` and matches your wall clock.

### P6. Preview before sending

```bash
cd ~/shift_bot && source venv/bin/activate && python main.py --dry-run
```

### P7. Security hardening

Run once after deploy:

```bash
chmod 600 .env
chmod 700 data
chmod 700 data/logs
```

After the first `--production` run (which creates `shift_bot.db`):

```bash
chmod 600 data/shift_bot.db
```

### P8. Configure cPanel cron jobs

In **cPanel → Cron Jobs**, add four entries.

**Shift notifications — 3 entries (one per shift type):**

Cron times are your `shift_hours` values converted to server local time. Formula:

```
cPanel time = shift_hours − (Kyiv UTC offset − server UTC offset)
            = shift_hours − (UTC+3 − UTC-4)
            = shift_hours − 7h    ← current value, summer 2026 (EEST / EDT)
```

If the result is negative, subtract one calendar day. Recalculate whenever either timezone changes clocks — the 7h is derived, not a fixed constant.

| Shift type | `shift_hours` (Kyiv EEST) | cPanel time (server local) | Same day?                |
|------------|--------------------------|-------------------|--------------------------|
| labor      | 17:00                    | 10:00             | ✅                        |
| holiday    | 17:34                    | 10:34             | ✅                        |
| other      | 01:25                    | 18:25             | ⚠️ previous calendar day |

> ⚠️ **DST reminder:** Both Kyiv and the server observe DST on different schedules. Verify the offset and update all 3 cron entries whenever either timezone changes clocks. Current offset: 7 h (EEST UTC+3 − EDT UTC-4). Winter offset also 7 h (EET UTC+2 − EST UTC-5) — but confirm at each transition.
>
> ⚠️ **Whenever you change `shift_hours`:** recalculate the server-local times using the formula above and update all 3 cPanel cron entries.

Each entry uses the `TZ=Europe/Kyiv` prefix so the bot sees Kyiv date, not server local date:

```
0  10 * * *  TZ=Europe/Kyiv /home/<username>/shift_bot/venv/bin/python /home/<username>/shift_bot/main.py --production --shift-type labor
34 10 * * *  TZ=Europe/Kyiv /home/<username>/shift_bot/venv/bin/python /home/<username>/shift_bot/main.py --production --shift-type holiday
25 18 * * *  TZ=Europe/Kyiv /home/<username>/shift_bot/venv/bin/python /home/<username>/shift_bot/main.py --production --shift-type other
```

> ℹ️ The `other` entry fires at 18:25 EDT the evening before. With `TZ=Europe/Kyiv`, the Python process sees 01:25 Kyiv time on the next calendar day — which is the correct Kyiv date for that shift. This is intentional.

**Log retention — 1 entry (weekly, Sunday 03:00 EDT server local time):**

```
0 3 * * 0  find /home/<username>/shift_bot/data/logs -name "*.log" -mtime +30 -delete
```

### P9. Production maintenance commands

Replace `docker compose run --rm bot` with the venv prefix `cd ~/shift_bot && source venv/bin/activate &&`:

| Task                | Command                                         |
|---------------------|-------------------------------------------------|
| Health check        | `python main.py`                                |
| Preview shifts      | `python main.py --dry-run`                      |
| Send notifications  | `python main.py --production`                   |
| Resend one person   | `python main.py --production --employee "Name"` |
| Force resend all    | `python main.py --production --force`           |
| Clear dedup records | `python main.py --reload-schedule`              |

### P9b. Managing cPanel cron entries

This is the production equivalent of `docker compose restart cron`.

**When you change `shift_hours` in `schedule_mapping.json`:**

1. Recalculate the new cPanel cron times using the formula from P8: `cPanel time = shift_hours − (Kyiv offset − server offset)`
2. In **cPanel → Cron Jobs**, edit each of the 3 shift notification entries to the new time
3. Verify with a health check: `cd ~/shift_bot && source venv/bin/activate && python main.py`
4. Confirm the `[SCHEDULE]` line shows the new times (available after S005 is deployed)

**If a cron entry fires at the wrong time or is missed — run manually:**

```bash
cd ~/shift_bot && source venv/bin/activate
python main.py --production --shift-type labor
# or: --shift-type holiday / --shift-type other
```

**After a DST change (either Kyiv or server clocks):**

1. Verify the current offset: run `date` on the server and compare to current Kyiv time
2. Recalculate: `cPanel time = shift_hours − (new Kyiv offset − new server offset)`
3. Update all 3 cron entries in **cPanel → Cron Jobs**
4. Run a health check and confirm the clock drift log shows `Clock drift OK`

> ⚠️ **DST trap:** Kyiv and the server change clocks on different dates. The offset may stay the same (7h) or shift by 1h depending on which side changes first. Always verify by checking both clocks, not by assuming.

### P10. Update schedule monthly

```bash
cd ~/shift_bot && source venv/bin/activate
python main.py --reload-schedule
python main.py --dry-run
python main.py --production
```

### P11. Update the bot

```bash
cd ~/shift_bot
git pull
source venv/bin/activate
pip install -r requirements.txt
```

No restart needed — cPanel cron picks up changes on the next fire.

### P12. Clock drift monitor

Every `--production` run logs one of:

```
Clock drift OK: 2s
Clock drift: server deviates from world time by 3720s — check server NTP or DST offset
Clock drift check skipped — time API unreachable
```

A `WARNING: Clock drift check skipped` line means the public time API (`worldtimeapi.org`) was temporarily unreachable — **this is not a clock drift event**. If it appears repeatedly over several days, check the API status. A `WARNING: Clock drift: server deviates...` line means the server clock itself is wrong — contact hosting support or recalculate cron times for DST.

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

| Command                                      | Effect                                    |
|----------------------------------------------|-------------------------------------------|
| `python main.py --health`                    | Health check — config, DB, XLSX, timezone |
| `python main.py`                             | Same as `--health` (default)              |
| `python main.py --dry-run`                   | Preview shift data, no sends              |
| `python main.py --production`                | Send notifications to group               |
| `python main.py --production --employee "X"` | Send for one employee only                |
| `python main.py --production --force`        | Resend all, ignore deduplication          |
| `python main.py --reload-schedule`           | Clear dedup records so cron re-sends      |
| `python main.py --reload-schedule --dry-run` | Preview what would be cleared             |

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

