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

### 004-05 Day-type correction after notification sent — ✅ ARCHITECT RULED (by design + gap noted)

STR

    1. We have a setting
        ```JSON
          "shift_hours": {
            "labour":   "23:23",
            "holiday": "16:30",
            "other":   "08:51"
          }
        ```
        and
        ```XLSLX
        Other	5/2/2026	лікар11 Aaaaaaaaaaaaaaaaa B.B.
        ```
        
        System sent notification to messenger, as expected. 
    
    2. We changed type and run: docker compose run --rm bot python main.py --reload-schedule
    
        ```XLSLX
        holiday	5/2/2026	лікар11 Aaaaaaaaaaaaaaaaa B.B.
        ```
        
        System did not send a notification to messenger, as expected. 

Expected: 
Clarify this usecase, What is expected.

Architect ruling (2026-05-02):
Step 2 sent nothing because `python main.py` without `--production` runs in **health mode** — health mode never sends. This is correct behaviour.

**Dedup key is `(employee_name, shift_date)` — day_type is not part of it.**  
After `--reload-schedule` clears the dedup record, the system CAN resend with the corrected day type.

**Correct workflows for day-type correction:**

Full order when correcting a shift that was already sent:

    1. Edit data/schedule_mapping.json
    2. Clear dedup so bot will resend
       docker compose run --rm bot python main.py --reload-schedule
    3. Reload cron schedule
       docker compose restart cron

ACTUAL:
No new message has been sent. 

### 004-06 No notification after shift_hours change + restart cron past the fire time — ✅ ADDRESSED

**Steps taken by Owner:**
1. Changed `shift_hours.holiday` to `14:15`
2. Ran `--reload-schedule` at 14:13
3. Ran `docker compose restart cron` at ~14:17
4. **Actual:** no message sent

**Root cause:** Cron was restarted at 14:17 — after 14:15 had already passed. Supercronic loaded the new `15 14 * * *` entry but does not retroactively fire times that have passed today. Entry will fire tomorrow at 14:15.

**This is expected cron behaviour — not a bug.** The workflow has a timing trap: if `docker compose restart cron` happens after the new fire time, the notification is missed for today.

**Fix for today — run manually:**
```bash
docker compose run --rm bot python main.py --production
```

**README updated** — section 10 now documents the full correction workflow including the ⚠️ warning that if the new fire time has already passed, `--production` must be run manually.

