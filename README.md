# Shift Schedule Notification Bot

Sends one personal Telegram message per duty shift to each staff member listed in the monthly XLSX schedule. Runs as a one-shot cron job on Namecheap cPanel (Python 3.11.14).

---

## Prerequisites

- Docker + Docker Compose (local development)
- Namecheap cPanel with Python 3.11.14 (production) — see S004

---

## Local Development (Docker)

### 1. Build the image

```bash
docker compose build
```

### 2. Generate test fixtures (run once)

```bash
docker compose run --rm bot python tests/create_fixture.py
```

### 3. Run tests

```bash
docker compose run --rm bot pytest
```

### 4. Set up data files

The `data/` directory is mounted into the container as `/data`. Place IT-managed files there — no rebuild needed when they change.

```
data/
├── schedule.xlsx       ← copy monthly XLSX here
├── contacts.json       ← copy from contacts.json.example and fill in real values
├── shift_bot.db        ← auto-created on first run
└── logs/               ← auto-created on first run
```

```bash
cp data/contacts.json.example data/contacts.json
# edit data/contacts.json with real names and Telegram chat IDs
```

### 5. Set up environment

```bash
cp .env.example .env
# TELEGRAM_BOT_TOKEN is the only value to fill in — all paths already point to /data/...
```

### 6. Run health check

```bash
docker compose run --rm bot python main.py
```

### 7. Dry run (preview messages, no sends, no DB writes)

```bash
docker compose run --rm bot python main.py --dry-run
```

---

## contacts.json format

```json
[
  {
    "name": "Єрема В.Р.",
    "channels": { "telegram": "123456789" },
    "primary_channel": "telegram"
  }
]
```

Name must match the XLSX cell value exactly. IT Owner maintains this file on the server — it is never committed to Git.

---
``` NOTE
1. Set Up the Group
   Create a closed Telegram group and add your employees.
   Add your bot to the group and promote it to Administrator.

2. Get the Group ID
   Send a test message in the group.
   Open this URL in your browser: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   Find the "chat" object and copy the "id" (it will start with a minus, e.g., -1001234567890).

3. Update Your System
   Save this -1001234567890 ID in your .env file as the target chat ID.
```

## Project structure

```
Shedule_bot/
├── main.py               — entry point (health / dry-run / production / reload-schedule)
├── models.py             — Shift, ShiftContext, RunMode dataclasses
├── config.py             — env var loading and validation
├── cli.py                — argument parsing
├── db.py                 — SQLite access (all SQL lives here)
├── schedule_parser.py    — XLSX parser + contacts.json loader
├── shift_logic.py        — pure prev/next shift computation
├── messenger/
│   ├── gateway.py        — MessengerGateway abstract interface
│   ├── telegram_adapter.py
│   └── viber_adapter.py
├── tests/
│   ├── fixtures/         — sample_schedule.xlsx + contacts.json (generated)
│   └── test_*.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## CLI reference

| Command | Effect |
|---------|--------|
| `python main.py` | Health check — config, DB, XLSX |
| `python main.py --dry-run` | Preview shift data for all staff, no sends |
| `python main.py --production` | Send notifications (S003) |
| `python main.py --reload-schedule` | Clear dedup records so cron re-sends |
| `python main.py --reload-schedule --dry-run` | Preview what would be cleared |
