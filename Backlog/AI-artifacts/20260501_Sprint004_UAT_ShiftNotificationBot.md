# Sprint 004 — Owner UAT

*Sprint:* 004 +
*Role:* Owner +
*Date:* 2026-05-02 +
*Status:* ⏸ IN PROGRESS — 004-3 pending Owner re-test after rebuild +
*Arch ref:* link:20260501_Sprint004_ARCH_ShiftNotificationBot.md[`20260501_Sprint004_ARCH_ShiftNotificationBot.md`]
*Dev ref:* link:20260501_Sprint004_DEV_ShiftNotificationBot.md[`20260501_Sprint004_DEV_ShiftNotificationBot.md`] +
*QA ref:* link:20260501_Sprint004_QA_ShiftNotificationBot.md[`20260501_Sprint004_QA_ShiftNotificationBot.md`]

'''

### 004-1 Do we have the Logs for review [HIGH] — ✅ ADDRESSED

Expected:
IT needs to easily maintain. So need to be able to find when specific feature was in use.

Expected:
Simple log file or SQ-lite

Developer response:
Logs exist in three places:
1. *File logs:* `data/logs/shift_bot_YYYYMMDD_HHMMSS.log` — one file per run, written to the host filesystem via the `./data:/data` volume mount. Survives container restarts.
2. *Docker logs:* `docker compose logs cron` — real-time stdout captured by supercronic, shows each cron firing.
3. *SQLite DB:* `data/shift_bot.db` — every notification recorded with timestamp, employee, status (`ok`/`fail`), and error message. Queryable with any SQLite viewer.

See QA OBS-001 for detail. README section 4 covers verification.

'''

=== 004-2 Maintainability cron vs schedule. [HIGH] — ✅ ADDRESSED

Actual result:
System has 2 settings now `/Shedule_bot/crontab` &amp; `/Shedule_bot/data/schedule.xlsx`

Expected: change in only one place OR if it is not possible advise how to optimize

Developer response:
Single source of truth is already implemented. `data/schedule_mapping.json` → `shift_hours` section drives the cron schedule directly. `gen_crontab.py` runs at cron container startup and generates `crontab.generated` automatically from those times.

IT workflow: edit `shift_hours` in `data/schedule_mapping.json`, then run `docker compose restart cron`. No separate crontab file to edit.

The static `crontab` file seen previously is no longer used — the cron service runs `gen_crontab.py` at startup. See ARCH DI-S004-001.

'''

=== 004-3 Missing startup time quality check of time [HIGH] — ⏸ PENDING RE-TEST

Actual: IT does not have instruction in readme.md on how to make sure how the local docker time is set. 

Expected: IT needs make sure docker time does not affect the integrity and suitability.

During the test I found docker local time is 04:38:50 while real time is 07:40:47 

Actual
```console]
----
itb@myk-VivoBook-ASUSLaptop-X515EA-X1500EA:~/GIT-IT-BOT/Project_Schedule_bot/Shedule_bot$ docker compose run --rm bot date
Sat May  2 05:00:40 Europe 2026

itb@myk-VivoBook-ASUSLaptop-X515EA-X1500EA:~/GIT-IT-BOT/Project_Schedule_bot/Shedule_bot$ date
субота, 2 травня 2026 08:00:48 +0300
----
```
Quality primitive was updated?

### 004-4 Why two images? shedule_bot-cron & shedule_bot-bot — ✅ FIXED (2026-05-02)

Using README.ms I always get 2 files schedule_bot-cron & schedule_bot-bot

Developer response:
Both services had `build: .` — Docker Compose builds and names a separate image per service, producing `shedule_bot-bot` and `shedule_bot-cron` even though both are identical builds from the same Dockerfile.

Fix applied to `docker-compose.yml`:
- `bot` service: `build: .` + `image: shedule_bot:latest` → builds once and tags the image
- `cron` service: `image: shedule_bot:latest` (no `build:`) → reuses the same image

Quality primitive was updated

### 004-05 Trigger was found but skipped
```log
2026-05-02 08:44:11,882 [INFO] Starting shift_bot | mode=health
2026-05-02 08:44:12,225 [INFO] Column 'Ургенція спеціалістів на дому' found but skipped (listed in skip_columns)
```

