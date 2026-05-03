# Sprint 004b — Owner UAT

*Sprint:* 004b +
*Role:* Owner +
*Date:* 2026-05-03 +
*Status:* ⏸ IN PROGRESS +
*Arch ref:* link:20260502_Sprint004b_ARCH_ShiftNotificationBot.md[`20260502_Sprint004b_ARCH_ShiftNotificationBot.md`]
*Dev ref:* link:20260502_Sprint004b_DEV_ShiftNotificationBot.md[`20260502_Sprint004b_DEV_ShiftNotificationBot.md`] +
*QA ref:* link:20260502_Sprint004b_QA_ShiftNotificationBot.md[`20260502_Sprint004b_QA_ShiftNotificationBot.md`]

'''

### 004b-1 Extend health with shift schedule [HIGH] — UAT

Actual:
```console
[CONFIG]   ✅ all variables loaded
[TIMEZONE] Europe/Kyiv — 2026-05-03 00:53:23 local
[DB]       ✅ shift_bot.db reachable, schema valid
[TELEGRAM] ✅ bot reachable, token valid
```

Expected:
Health output includes the active `shift_hours` mapping so IT can confirm which times the bot uses without opening `schedule_mapping.json` manually:
```console
[CONFIG]   ✅ all variables loaded
[TIMEZONE] Europe/Kyiv — 2026-05-03 00:53:23 local
[SCHEDULE] shift_hours: labor=17:00  holiday=09:00  other=08:20
[DB]       ✅ shift_bot.db reachable, schema valid
[TELEGRAM] ✅ bot reachable, token valid
```

Quality primitive was updated?

'''

### 004b-2 Extend health with environment time and offset [HIGH] — ⏸ OPEN

Actual:
```console
(venv) [itbomenf@server129 Shedule_bot]$ date
Sun May  3 01:02:35 EDT 2026
```
```console
[TIMEZONE] Europe/Kyiv — 2026-05-03 00:53:23 local
```
The health check shows only the bot's configured timezone. IT cannot see the server's actual clock or how far it deviates from the bot's reference timezone.

Expected:
```console
[TIMEZONE] Europe/Kyiv — 2026-05-03 00:53:23 local
[ENV TIME]  Sun May  3 01:02:35 EDT 2026
[TZ OFFSET] bot leads env by 7h (Europe/Kyiv EEST UTC+3 vs server EDT UTC-4)
```

Note: "Event diff -7" means the server clock (EDT, UTC-4) is 7 hours behind the bot's configured timezone (Kyiv EEST, UTC+3). A positive diff would mean the server leads.

> **S004b discovery:** This finding revealed that the production server runs EDT (UTC-4), not UTC as recorded in OQ-3 of S004b ARCH. OQ-3 was answered after `export TZ='UTC'` was run in the shell — the override masked the real server timezone. The S004b README cron conversion table was calculated for a UTC server and is therefore wrong. See finding 004b-4.



### 004b-3 README missing cron management instructions for production (non-Docker) [CRITICAL] — ✅ ADDRESSED

Actual:
README.md section `### 10. Local automation (cron service)` describes how to restart the cron scheduler in the Docker workflow (`docker compose restart cron`). There is no equivalent section in `## For Production (cPanel)` explaining how IT should:
- update cPanel cron times when `shift_hours` changes
- verify that the correct cron entries are active after a change
- manually trigger a run if cron fires at the wrong time (e.g., after a DST change)

Expected:
A dedicated subsection in the Production section of README that covers:
1. Where to find cPanel cron settings (cPanel UI → Cron Jobs)
2. How to update cron times when `shift_hours` changes (recalculate local server time → Kyiv conversion)
3. How to manually run the bot if a cron entry is missed: `cd ~/shift_bot && source venv/bin/activate && python main.py --production --shift-type <type>`
4. DST reminder: offset changes twice per year — update all 3 cron entries when clocks change



### 004b-4 README cron conversion table uses wrong server timezone [CRITICAL] — ✅ ADDRESSED

Actual:
README P8 cron conversion table (added in S004b) lists UTC times for the cPanel cron entries:

| Shift type | shift_hours (Kyiv) | cPanel cron time     |
|------------|--------------------|----------------------|
| labor      | 17:00              | 14:00 UTC            |
| holiday    | 09:00              | 06:00 UTC            |
| other      | 01:25              | 22:25 UTC (prev day) |

This table is wrong. The server timezone is EDT (UTC-4), not UTC. S004b OQ-3 was answered under a `export TZ='UTC'` shell override, which masked the actual server clock.

Expected:
Correct cron times for an EDT server (UTC-4, EEST = UTC+3, offset = 7h):

| Shift type | shift_hours (Kyiv EEST) | cPanel cron time (EDT) | Calendar day        |
|------------|------------------------|------------------------|---------------------|
| labor      | 17:00                  | 10:00 EDT              | ✅ same day          |
| holiday    | 09:00                  | 02:00 EDT              | ✅ same day          |
| other      | 01:25                  | 18:25 EDT (prev day)   | ⚠️ crosses midnight |

> **DST note:** Both EEST (summer) and EDT (summer) are active now. When either timezone switches, the offset changes and all 3 cron entries must be recalculated. In winter: Kyiv → EET (UTC+2), server → EST (UTC-5), offset = 7h (unchanged in this case). Verify each transition.

ARCH action: ✅ DONE — AD-S004b-001 and OQ-3 corrected in `20260502_Sprint004b_ARCH_ShiftNotificationBot.md` (2026-05-03). Developer must fix README (D2 correction + D9 new section).

Quality primitive was updated? — Yes: the `export TZ=` masking trap should be added to the quality guide so future deployments verify server timezone without shell overrides active.


### 004b-5 Unexpected files to track in GIT on prod [CRITICAL] — ✅ FIXED

Actual:
```console
[itbomenf@server129 ~]$ cd Shedule_bot/
[itbomenf@server129 Shedule_bot]$ git status
On branch main
Your branch is up to date with 'origin/main'.

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	venv/
```

Expected: `git status` shows no untracked files (clean working tree).

Root cause: `.gitignore` covered `.venv/` but not `venv/` — the convention used on the server.

Fix: `venv/` added to `.gitignore` (2026-05-03).

Quality primitive was updated? — Yes: rule added to `AI-assistance/ext/backend-python.md` — `.gitignore` must cover all local runtime artifacts; QA must run `git status` on a clean checkout before release.


### 004b-6 Wrong info about offset. [high]

Actual:
```console 
(venv) [itbomenf@server129 Shedule_bot]$ cd ~/Shedule_bot && source venv/bin/activate && python main.py --health                   
2026-05-03 03:05:53,449 [INFO] Starting shift_bot | mode=health                                                                                                                         
[CONFIG]   ✅ all variables loaded                                                                                                                                                      
[TIMEZONE] Europe/Kyiv — 2026-05-03 03:05:53 local                                                                                                                                      
[SCHEDULE] shift_hours: labor=17:00  holiday=09:00  other=09:44                                                                                                                         
[ENV TIME]  Sun May  3 03:05:53 EDT 2026                                                                                                                                                
[TZ OFFSET] bot and server clocks match (Europe/Kyiv EDT UTC-4 vs server EDT UTC-4)   
```
and 
```console 
(venv) [itbomenf@server129 Shedule_bot]$ date
Sun May  3 03:07:03 EDT 2026
```

Ecpected:
meaningful info for maintainers to show

---

### 004b-7 `--gen-crontab` does not install cron entries — IT still required to add manually [CRITICAL]

Actual:
```console
(venv) [itbomenf@server129 Shedule_bot]$ TZ=Europe/Kyiv python main.py --gen-crontab
# Generated: 2026-05-03 16:51 (Europe/Kyiv)
# ...
# Paste all entries into cPanel → Cron Jobs.
```

The command prints cron entries but does not install them. IT must manually open cPanel → Cron Jobs and add each entry within a 5-minute window to catch the verification entry.

Expected:
The system installs the cron entries automatically — no manual cPanel interaction required. The `crontab` shell command is available on cPanel shared hosting and can be used to install entries programmatically.
