# Webhook Setup (S005)

> **Prerequisite:** base deploy must already be complete — see [readme_DEPLOY.md](readme_DEPLOY.md) P1–P8.  
> (Bot files cloned, venv created, `.env` filled, cron installed.)

Telegram delivers messages to the bot via HTTPS POST to your server.
On cPanel shared hosting this runs as a CGI script — no persistent process required.

---

## Placeholders used in this guide

Replace every placeholder before running a command. Placeholders use `<ALL_CAPS>` format.

| Placeholder          | What to put                                             |
|----------------------|---------------------------------------------------------|
| `<YOUR_DOMAIN>`      | Your public domain, e.g. `itbomenf.server129.com`       |
| `<YOUR_TELEGRAM_ID>` | Your numeric Telegram user ID (shown by `/start` reply) |
| `<YOUR_BOT_TOKEN>`   | Your Telegram bot token from @BotFather                 |

---

## Step 0 — Pull latest code

In **cPanel → Advanced → Terminal**:

```bash
cd ~/Shedule_bot && git pull
```

If this is your first time setting up the webhook, also run once:

```bash
git config --local core.fileMode false
```

This tells git to ignore file permission changes on this server. Without it, the `chmod` in Step 1 will show as a pending change on every future `git pull`.

---

## Step 1 — Configure the Python App in cPanel

This hosting uses Passenger (WSGI), not CGI. No symlinks are needed.

In **cPanel → Software → Setup Python App**:

1. If no app exists yet: click **Create Application**
2. Set **Python version** to `3.11.x`
3. Set **Application root** to `Shedule_bot`
4. Set **Application URL** to `<YOUR_DOMAIN>/Shedule_bot`
5. Leave **Application startup file** as `passenger_wsgi.py`
6. Click **Create** (or **Save**)

Verify the app is reachable:

```bash
curl -s https://<YOUR_DOMAIN>/Shedule_bot
# Expected: {}
```

---

## Step 2 — Add webhook variables to .env

Generate a secret token:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Add these two lines to `~/Shedule_bot/.env` (e.g. using $ nano .env):

```
WEBHOOK_URL=https://<YOUR_DOMAIN>/Shedule_bot
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
[WEBHOOK] ✅ Registered: https://<YOUR_DOMAIN>/Shedule_bot
```

---

## Step 4 — Bootstrap the first IT admin

Get your Telegram ID by messaging the bot `/start` (it appears in the reply).

```bash
cd ~/Shedule_bot && source venv/bin/activate
TZ=Europe/Kyiv python main.py --bootstrap-it <YOUR_TELEGRAM_ID>
```

Expected output:

```
[BOOTSTRAP] ✅ IT user <YOUR_TELEGRAM_ID> registered
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
curl -s "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook"
```

---

## Troubleshooting

| Symptom                             | Check                                                       |
|-------------------------------------|-------------------------------------------------------------|
| Bot silent after message            | `tail -20 ~/Shedule_bot/data/logs/webhook.log`              |
| `curl` returns 404 or HTML instead of `{}` | App not started in cPanel, or `passenger_wsgi.py` missing from app root |
| 403 from bot_hook                   | `WEBHOOK_SECRET_TOKEN` mismatch — fix `.env`, re-run Step 3 |
| Role stays `pending`                | Run Step 4 (`--bootstrap-it`) first                         |

---

### "Virtual environment already exists" error during setup

cPanel Python App UI refuses to create a new app because a `venv/` directory already exists.

**Fix:**

1. In **cPanel → Software → Setup Python App**, find the existing app and click **Remove Application** (this removes the app config but does not delete your files).
2. Delete the old virtual environment:
   ```bash
   rm -rf ~/Shedule_bot/venv
   ```
3. Re-create the app following Step 1 of this guide.

---

### Existing app configured for wrong domain

If the app was previously created with the wrong Application URL, the webhook URL will not match.

**Fix:**

1. In **cPanel → Software → Setup Python App**, click **Remove Application** on the existing app.
2. Re-create it with the correct **Application URL** (Step 1 of this guide).
3. Re-run Step 3 (`--register-webhook`) so Telegram is updated with the new URL.

You can verify Telegram has the correct URL:

```bash
curl -s "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo" | python3 -m json.tool
```

The `url` field in the response should match your webhook URL exactly.

---

### Webhook registered but bot not receiving messages

Telegram reports the webhook as set but the bot never responds.

**Checks:**

1. Verify the webhook URL and secret are registered correctly:
   ```bash
   curl -s "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo" | python3 -m json.tool
   ```
   Confirm `url` matches your server URL and `has_custom_certificate` is `false` (unless you are using a self-signed cert).

2. Confirm the app is running in cPanel — visit `https://<YOUR_DOMAIN>/Shedule_bot` in a browser; it should return `{}`.

3. Check the secret token in `.env` matches what was registered:
   ```bash
   grep WEBHOOK_SECRET_TOKEN ~/Shedule_bot/.env
   ```
   If in doubt, regenerate the token, update `.env`, and re-run `--register-webhook`.
