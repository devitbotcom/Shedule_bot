# Sprint 003 — QA Review & UAT Checklist
**Sprint:** 003  
**Role:** QA Engineer  
**Date:** 2026-04-30 (re-review after Developer fixes)  
**Status:** ❌ FAILED — BUG-005 raised, escalated to Architect.  
**Arch ref:** [`20260430_Sprint003_ARCH_ShiftNotificationBot.md`](20260430_Sprint003_ARCH_ShiftNotificationBot.md)
**Dev ref:** [`20260430_Sprint003_DEV_ShiftNotificationBot.md`](20260430_Sprint003_DEV_ShiftNotificationBot.md)  
**QA ref:** [`20260430_Sprint003_QA_ShiftNotificationBot.md`](20260430_Sprint003_DEV_ShiftNotificationBot.md)

---



### 003-2 Change-request - Add department to message (DONE)

Expected:
Each staff member (per department) listed in the XLSX schedule grid receives one personal Telegram message per shift.

department_title  is by source XLSX - Shedule_bot/data/schedule.xlsx
and it needs to be mapped in Shedule_bot/data/schedule_mapping.json

Message format:

```
Зміна: {department_title} {date}
{staff_name} заступає на зміну замість {previous_staff_name}.

Наступна зміна:
{next_date} о {next_time} — {next_staff_name}
```

### 003-1  Unexpected - for upcoming shift. [DONE]

STR: 

```XLSX
4/30/2026	лікар1 Авіаіццац Ц.Б.	лікар2 Ивнуицу Б.І.	лікар9
5/1/2026	лікар3 Оврциф Л.Б.	лікар4 Роівг У.Г.	лікар11
```
docker compose run --rm bot python main.py --production --force


Actual:
```Log
2026-04-30 20:19:27,488 [INFO] Starting shift_bot | mode=production
2026-04-30 20:19:27,500 [INFO] Column 'Ургенція спеціалістів на дому' found but skipped (listed in skip_columns)
2026-04-30 20:19:27,922 [INFO] Sent: лікар9 2026-04-30
2026-04-30 20:19:29,248 [INFO] Sent: лікар1 Авіаіццац Ц.Б. 2026-04-30
2026-04-30 20:19:30,580 [INFO] Sent: лікар2 Ивнуицу Б.І. 2026-04-30
[PRODUCTION] sent=3  skipped=0  failed=0
```

```Telegram
Зміна: 30-04-2026
лікар9 заступає на зміну замість -.

Наступна зміна:
-
Зміна: 30-04-2026
лікар1 Авіаіццац Ц.Б. заступає на зміну замість -.

Наступна зміна:
-
Зміна: 30-04-2026
лікар2 Ивнуицу Б.І. заступає на зміну замість -.

Наступна зміна:
-
```

Expected:
Next shift is from same column, next row — e.g. лікар3 Оврциф Л.Б. for лікар1's department.

**QA Analysis:** Logged as BUG-005 in QA artifact. Root cause: date filter applied before `compute_contexts()` — tomorrow's shifts are stripped before next_colleague can be assigned. Escalated to Architect for fix decision.