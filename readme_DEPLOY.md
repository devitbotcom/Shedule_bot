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

```bash
cd ~/Shedule_bot && source venv/bin/activate && python main.py --production
```

This creates `shift_bot.db` — required for the second chmod step in P7.

If shifts are scheduled for today, notifications will be sent to the Telegram group — confirm they arrive. If there are no shifts today, the bot exits with `No shifts found for date: YYYY-MM-DD` — that is normal. The DB is created either way.

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

```bash
cd ~/Shedule_bot && source venv/bin/activate && TZ=Europe/Kyiv python main.py --gen-crontab
```

The command installs all cron entries automatically — no cPanel UI interaction needed. Times are calculated from `shift_hours` and the server's timezone offset.

A verification entry is included that fires ~5 minutes after install. When the Telegram confirmation message arrives, the entry removes itself automatically.

Expected output on success:

```
[CRONTAB] ✅ 5 entries installed (YYYY-MM-DD HH:MM)
[CRONTAB] Verification entry fires in ~5 min — watch for Telegram confirmation.
[CRONTAB] Re-run --gen-crontab any time to update (old entries replaced).
```

If the output shows `⚠️ Auto-install failed`, copy the printed entries manually into **cPanel → Cron Jobs**.

> ⚠️ Re-run `--gen-crontab` whenever you change `shift_hours` or after a DST transition — it always recalculates from current config. See P9b for the full update procedure.

### P9. Maintenance commands

All commands follow this pattern — activate the venv first:

```bash
cd ~/Shedule_bot && source venv/bin/activate && python3 main.py --health 
```
and then 

| Task                    | Command                                                   |
|-------------------------|-----------------------------------------------------------|
| Health check            | ` main.py --health`                                       |
| Preview shifts          | ` main.py --dry-run`                                      |
| Send notifications      | ` main.py --production`                                   |
| Resend one person       | ` main.py --production --employee "Name"`                 |
| Force resend all        | ` main.py --production --force`                           |
| Clear dedup records     | ` main.py --reload-schedule`                              |
| Send one shift type     | ` main.py --production --shift-type labor`                |
| Regenerate cron entries | `TZ=Europe/Kyiv python main.py --gen-crontab`             |

### P9b. Managing cPanel cron entries

**When you change `shift_hours` in `schedule_mapping.json`:**

1. Run `cd ~/Shedule_bot && source venv/bin/activate && TZ=Europe/Kyiv python main.py --gen-crontab` — entries reinstalled automatically
2. Verify: `TZ=Europe/Kyiv python main.py --health` — confirm `[SCHEDULE]` shows the new times

**If a cron entry fires at the wrong time or is missed — run manually:**

```bash
cd ~/Shedule_bot && source venv/bin/activate
python main.py --production --shift-type labor
# or: --shift-type holiday / --shift-type other
```

**After a DST change (either Kyiv or server clocks):**

1. Run `TZ=Europe/Kyiv python main.py --health` — confirm `[TZ OFFSET]` shows the new offset
2. Run `TZ=Europe/Kyiv python main.py --gen-crontab` — recalculates and reinstalls all entries automatically
3. Confirm `Clock drift OK` in the next production log

> ⚠️ **DST trap:** Kyiv and the server change clocks on different dates. The offset may stay the same or shift by 1h — always verify with `--health` first, do not assume.

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
