# Shift Schedule Notification Bot — Production Deploy & Maintenance

> **Local development (Docker):** see [README.md](README.md)

Covers deploy to Namecheap cPanel shared hosting and ongoing maintenance. Docker is not available on shared hosting — the bot runs as a plain Python script under `venv`, triggered by cPanel cron jobs.

---

### P0. Prerequisites (once)

Configure SSH key access to your repository on the server via the cPanel terminal before running `git clone`. Without this, cloning a private repo will fail.

How to set it up in cPanel:

   ???

### P1. Clone the repository

```bash
cd ~
git clone git@github.com:devitbotcom/Shedule_bot.git
cd Shedule_bot
```

> `git clone` creates the folder `Shedule_bot` automatically (the repo name). All commands below use `~/Shedule_bot`.

### P2. Create virtual environment

The system `python3` on Namecheap shared hosting is 3.6 — too old. Use the hosted Python 3.11:

```bash
/opt/alt/python311/bin/python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### P3. Place data files

Upload these files to `~/Shedule_bot/data/` via cPanel File Manager or `scp`:

```
~/Shedule_bot/data/
├── schedule.xlsx
├── schedule_mapping.json      ← copy from .example, edit once
├── shift_bot.db               ← auto-created on first run
└── logs/                      ← auto-created on first run
```

```bash
cp data/schedule_mapping.json.example data/schedule_mapping.json
```

### P4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` — use **absolute paths** and fill in your credentials:

```
XLSX_PATH=/home/<username>/Shedule_bot/data/schedule.xlsx
DB_PATH=/home/<username>/Shedule_bot/data/shift_bot.db
LOG_DIR=/home/<username>/Shedule_bot/data/logs
TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here
TELEGRAM_GROUP_CHAT_ID=-1001234567890
TZ=Europe/Kyiv
```

### P5. Verify setup

```bash
cd ~/Shedule_bot && source venv/bin/activate && python main.py --health
```

All lines should show ✅. Expected output:

```
[CONFIG]    ✅ all variables loaded
[TIMEZONE]  Europe/Kyiv — YYYY-MM-DD HH:MM:SS local
[SCHEDULE]  shift_hours: labor=HH:MM  holiday=HH:MM  other=HH:MM
[ENV TIME]  <server local date and time>
[TZ OFFSET] bot leads server by 7h (Europe/Kyiv EEST UTC+3 vs server EDT UTC-4)
[DB]        ✅ shift_bot.db reachable, schema valid
[TELEGRAM]  ✅ bot reachable, token valid
[XLSX]      ✅ schedule.xlsx found — N employees, N shift dates
[LAST RUN]  no runs recorded yet
[PENDING]   N shifts pending notification
```

### P6. Preview before sending

```bash
cd ~/Shedule_bot && source venv/bin/activate && python main.py --dry-run
```

### P6b. First production run (manual)

Verify that notifications send and confirm messages arrive in the Telegram group:

```bash
cd ~/Shedule_bot && source venv/bin/activate && python main.py --production
```

This also creates `shift_bot.db` — required for the second chmod step in P7.

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

Go to **cPanel → Cron Jobs** and add four entries. For each entry, fill in the Minute, Hour, Day, Month, Weekday fields and paste the Command.

**Shift notifications — 3 entries:**

Times below are based on `shift_hours` defaults in `schedule_mapping.json` converted to server local time (Kyiv EEST UTC+3 − server EDT UTC-4 = 7h).

| Time (server) | Min | Hour | Day | Month | Weekday | Command                                                                                                                              |
|---------------|-----|------|-----|-------|---------|--------------------------------------------------------------------------------------------------------------------------------------|
| 10:00         | 0   | 10   | *   | *     | *       | `TZ=Europe/Kyiv /home/<username>/Shedule_bot/venv/bin/python /home/<username>/Shedule_bot/main.py --production --shift-type labor`   |
| 02:00         | 0   | 2    | *   | *     | *       | `TZ=Europe/Kyiv /home/<username>/Shedule_bot/venv/bin/python /home/<username>/Shedule_bot/main.py --production --shift-type holiday` |
| 02:00         | 0   | 2    | *   | *     | *       | `TZ=Europe/Kyiv /home/<username>/Shedule_bot/venv/bin/python /home/<username>/Shedule_bot/main.py --production --shift-type other`   |

> ⚠️ If you change `shift_hours` in `schedule_mapping.json`, recalculate: `cPanel time = shift_hours − (Kyiv offset − server offset)` and update these entries. See P9b.

**Log retention — 1 entry:**

| Min | Hour | Day | Month | Weekday | Command                                                                        |
|-----|------|-----|-------|---------|--------------------------------------------------------------------------------|
| 0   | 3    | *   | *     | 0       | `find /home/<username>/Shedule_bot/data/logs -name "*.log" -mtime +30 -delete` |

### P9. Maintenance commands

All commands follow this pattern — activate the venv first:

```bash
cd ~/Shedule_bot && source venv/bin/activate
```

| Task                | Command                                                  |
|---------------------|----------------------------------------------------------|
| Health check        | `python main.py --health`                                |
| Preview shifts      | `python main.py --dry-run`                               |
| Send notifications  | `python main.py --production`                            |
| Resend one person   | `python main.py --production --employee "Name"`          |
| Force resend all    | `python main.py --production --force`                    |
| Clear dedup records | `python main.py --reload-schedule`                       |
| Send one shift type | `python main.py --production --shift-type labor`         |

### P9b. Managing cPanel cron entries

**When you change `shift_hours` in `schedule_mapping.json`:**

1. Recalculate the new cPanel cron times using the formula from P8: `cPanel time = shift_hours − (Kyiv offset − server offset)`
2. In **cPanel → Cron Jobs**, edit each of the 3 shift notification entries to the new time
3. Verify: `cd ~/Shedule_bot && source venv/bin/activate && python main.py --health`
4. Confirm the `[SCHEDULE]` line shows the new times

**If a cron entry fires at the wrong time or is missed — run manually:**

```bash
cd ~/Shedule_bot && source venv/bin/activate
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
cd ~/Shedule_bot && source venv/bin/activate
python main.py --reload-schedule
python main.py --dry-run
python main.py --production
```

### P11. Update the bot

```bash
cd ~/Shedule_bot
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

`Clock drift check skipped` means the public time API (`worldtimeapi.org`) was temporarily unreachable — **not a clock drift event**. If it repeats for several days, check the API status. `Clock drift: server deviates...` means the server clock itself is wrong — contact hosting support or recalculate cron times for DST.
