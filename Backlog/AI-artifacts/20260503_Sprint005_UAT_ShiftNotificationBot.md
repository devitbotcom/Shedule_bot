# Sprint S005 — Owner UAT
**Date:** 2026-05-03  
**Sprint:** S005 — Webhook Infrastructure  
**Prepared by:** QA  
**For:** Owner (Myk)

---

## What this sprint delivers

The bot can now receive Telegram messages in real time (webhook, near-zero latency).  
Users who message the bot are registered automatically. An IT admin can assign roles.  
POC1 notification pipeline is untouched.

---

## Prerequisites before starting UAT

The following must already be done on the server (see `readme_WEBHOOK.md` for full steps):

- [+] Latest code pulled: `cd ~/Shedule_bot && git pull`
- [ ] `passenger_wsgi.py` present in `~/Shedule_bot/`; cPanel Python App running with app root `Shedule_bot`; verify: `curl -s https://<YOUR_DOMAIN>/Shedule_bot` returns `{}`
- [+] `.env` has `WEBHOOK_URL`, `WEBHOOK_SECRET_TOKEN`, `TELEGRAM_BOT_TOKEN`, `DB_PATH`
- [ ] Webhook registered: `cd ~/Shedule_bot && source venv/bin/activate && TZ=Europe/Kyiv python main.py --register-webhook` → `[WEBHOOK] ✅ Registered: https://<YOUR_DOMAIN>/Shedule_bot`

If prerequisites are not yet done, complete them first — UAT cannot proceed without a live webhook.

---

## Test cases

### U005-1 — First contact: new user registered automatically

**Actor:** any Telegram user (can be yourself from a second account or phone)  
**Steps:**
1. Open the bot in Telegram and send `/start`

**Expected reply:**
```
👋 Вітаю, <your name>!
Ваш Telegram ID: <number>
Роль: pending
Використайте /help для списку команд.
```

**Pass criteria:** reply received; Telegram ID shown; role is `pending`.

---

### U005-2 — Profile query

**Steps:**
1. Send `/whoami`

**Expected reply:**
```
ID: <number>
Ім'я: <your name>
Роль: pending
```

**Pass criteria:** all three fields shown correctly.

---

### U005-3 — Help menu for unprivileged user

**Steps:**
1. Send `/help`

**Expected reply:** list of commands (`/start`, `/whoami`, `/help`).  
**Pass criteria:** `/setrole` is NOT in the reply.

---

### U005-4 — Bootstrap IT admin (server command)

**Actor:** Owner, on the server via SSH or cPanel Terminal  
**Steps:**
1. Note your Telegram ID from U005-1
2. Run:
   ```bash
   cd ~/Shedule_bot && source venv/bin/activate && TZ=Europe/Kyiv python main.py --bootstrap-it <your_telegram_id>
   ```

**Expected output:**
```
[BOOTSTRAP] ✅ IT user <your_telegram_id> registered
```

**Pass criteria:** command exits 0 with the confirmation line.

---

### U005-5 — Help menu for IT admin

**Steps:**
1. Send `/help` from the same account used in U005-4

**Expected reply:** same list as U005-3 **plus** a `/setrole` line.  
**Pass criteria:** `/setrole` IS in the reply.

---

### U005-6 — Assign a role (IT admin action)

**Prerequisite:** a second Telegram account has already messaged the bot (so it is registered).  
Note that user's Telegram ID from the bot's reply to their `/start`.

**Steps:**
1. As IT admin, send:
   ```
   /setrole <their_telegram_id> staff
   ```

**Expected reply:**
```
✅ Роль <their_telegram_id> оновлено: staff
```

**Pass criteria:** success message received; if that user sends `/whoami`, role now shows `staff`.

---

### U005-7 — Role assignment blocked for non-IT user

**Actor:** any user with role `pending` or `staff`  
**Steps:**
1. Send `/setrole <any_id> staff`

**Expected reply:**
```
⛔ Не авторизовано.
```

**Pass criteria:** blocked message received; no role change occurs.

---

### U005-8 — Unknown command

**Steps:**
1. Send any unrecognised text, e.g. `/hello`

**Expected reply:** message containing `/help`.  
**Pass criteria:** bot replies and does not crash.

---

### U005-9 — POC1 notifications unaffected (regression)

**Steps:**
1. Run the existing notification pipeline as normal (or dry-run):
   ```bash
   cd ~/Shedule_bot && source venv/bin/activate && TZ=Europe/Kyiv python main.py --dry-run
   ```

**Pass criteria:** output identical to pre-S005 behaviour; no errors referencing webhook or user tables.

---

## UAT sign-off

| Case   | Result | Notes                        |
|--------|--------|------------------------------|
| U005-1 | -      | Bot does not react on /start |
| U005-2 | ⬜      |                              |
| U005-3 | ⬜      |                              |
| U005-4 | ⬜      |                              |
| U005-5 | ⬜      |                              |
| U005-6 | ⬜      |                              |
| U005-7 | ⬜      |                              |
| U005-8 | ⬜      |                              |
| U005-9 | ⬜      |                              |

**Owner sign-off:** _________________________________ Date: _____________

---

## If something goes wrong

| Symptom                                               | Where to look                                                                     |
|-------------------------------------------------------|-----------------------------------------------------------------------------------|
| Bot does not reply at all                             | `tail -20 ~/Shedule_bot/data/logs/webhook.log`                                    |
| `curl https://<YOUR_DOMAIN>/bot_hook.py` returns HTML | Symlink broken or file not executable                                             |
| Webhook registered but bot still silent               | `WEBHOOK_SECRET_TOKEN` mismatch — re-run `--register-webhook` after fixing `.env` |
| U005-4 fails with `DB_PATH not set`                   | Check `~/Shedule_bot/.env` has `DB_PATH` set to an absolute path                  |
