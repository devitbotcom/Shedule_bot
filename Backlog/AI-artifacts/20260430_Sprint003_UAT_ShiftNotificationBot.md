# Sprint 003 — QA Review & UAT Checklist
**Sprint:** 003  
**Role:** QA Engineer  
**Date:** 2026-04-30 (re-review after Developer fixes)  
**Status:** ✅ FAILED.  
**Arch ref:** [`20260430_Sprint003_ARCH_ShiftNotificationBot.md`](20260430_Sprint003_ARCH_ShiftNotificationBot.md)
**Dev ref:** [`20260430_Sprint003_DEV_ShiftNotificationBot.md`](20260430_Sprint003_DEV_ShiftNotificationBot.md)  
**QA ref:** [`20260430_Sprint003_QA_ShiftNotificationBot.md`](20260430_Sprint003_DEV_ShiftNotificationBot.md)

---


Feedback:

### 003-1  [CRITICAL]

Actual:
```Log
2026-04-30 20:03:14,623 [INFO] Starting shift_bot | mode=production
2026-04-30 20:03:14,637 [INFO] Column 'Ургенція спеціалістів на дому' found but skipped (listed in skip_columns)
2026-04-30 20:03:14,997 [INFO] Sent: лікар2 Ивнуицу Б.І. 2026-04-30
2026-04-30 20:03:16,321 [INFO] Sent: лікар9 2026-04-30
2026-04-30 20:03:17,652 [INFO] Sent: лікар1 Авіаіццац Ц.Б. 2026-04-30
2026-04-30 20:03:18,986 [INFO] Sent: лікар8 2026-04-30
2026-04-30 20:03:20,315 [INFO] Sent: лікар5 Рівтон 2026-04-30
2026-04-30 20:03:21,648 [INFO] Sent: лікар7 2026-04-30
2026-04-30 20:03:22,977 [INFO] Sent: лікар3 Оврциф Л.Б. 2026-04-30
2026-04-30 20:03:24,303 [INFO] Sent: лікар6 Цой О.Й. 2026-04-30
2026-04-30 20:03:25,636 [INFO] Sent: лікар4 Роівг У.Г. 2026-04-30
[PRODUCTION] sent=9  skipped=0  failed=0
```

```Telegram
Зміна: 30-04-2026
лікар1 Авіаіццац Ц.Б. заступає на зміну замість -.

Наступна зміна:
-
```

