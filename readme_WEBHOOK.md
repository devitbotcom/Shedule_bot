# Webhook Setup (S005)

> **Prerequisite:** base deploy must already be complete — see [readme_DEPLOY.md](readme_DEPLOY.md) P1–P8.  
> (Bot files cloned, venv created, `.env` filled, cron installed.)

Telegram delivers messages to the bot via HTTPS POST to your server.
On cPanel shared hosting this runs as a CGI script — no persistent process required.

---

## Step 0 — Pull latest code

In **cPanel → Advanced → Terminal**:

```bash
cd ~/Shedule_bot && git pull
```

---

## Step 1 — Symlink the CGI handler

```bash
ln -s ~/Shedule_bot/bot_hook.py ~/public_html/bot_hook.py
chmod 755 ~/Shedule_bot/bot_hook.py
```

> If you see `ln: failed to create symbolic link … File exists`, remove the old entry first:
> ```bash
> rm ~/public_html/bot_hook.py
> ln -s ~/Shedule_bot/bot_hook.py ~/public_html/bot_hook.py
> ```

Verify it is reachable:

```bash
curl -s https://yourdomain.com/bot_hook.py
# Expected: {}   (printed on its own line — empty output means a script error)
```

---

## Step 2 — Add webhook variables to .env

Generate a secret token:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Add these two lines to `~/Shedule_bot/.env`:

```
WEBHOOK_URL=https://yourdomain.com/bot_hook.py
WEBHOOK_SECRET_TOKEN=<token from above>
```

---

## Step 3 — Register the webhook with Telegram

```bash
cd ~/Shedule_bot && source venv/bin/activate
TZ=Europe/Kyiv python main.py --register-webhook
```

Expected output:

```
[WEBHOOK] ✅ Registered: https://yourdomain.com/bot_hook.py
```

---

## Step 4 — Bootstrap the first IT admin

Get your Telegram ID by messaging the bot `/start` (it appears in the reply).

```bash
cd ~/Shedule_bot && source venv/bin/activate
TZ=Europe/Kyiv python main.py --bootstrap-it <your_telegram_id>
```

Expected output:

```
[BOOTSTRAP] ✅ IT user <your_telegram_id> registered
```

---

## Step 5 — Verify

Send `/whoami` to your bot. Reply should show your ID, name, and role `it`.

---

## Updating the webhook URL

If your domain or path changes, re-run Step 3. `--register-webhook` is idempotent.

---

## Removing the webhook

```bash
curl -s "https://api.telegram.org/bot<TOKEN>/deleteWebhook"
```

---

## Troubleshooting

| Symptom | Check |
|---|---|
| Bot silent after message | `tail -20 ~/Shedule_bot/data/logs/webhook.log` |
| `curl` returns HTML instead of `{}` | Symlink broken or `bot_hook.py` not executable |
| 403 from bot_hook | `WEBHOOK_SECRET_TOKEN` mismatch — fix `.env`, re-run Step 3 |
| Role stays `pending` | Run Step 4 (`--bootstrap-it`) first |
