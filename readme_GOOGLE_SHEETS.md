# Google Sheets Integration Setup (S006a)

> **Prerequisite:** base deploy must already be complete — see [readme_DEPLOY.md](readme_DEPLOY.md) P1–P8.

The bot reads the staff list and schedule grid from a Google Sheet using a service account — no user login required.

---

## Placeholders used in this guide

| Placeholder                  | What to put                                                                                    |
|------------------------------|------------------------------------------------------------------------------------------------|
| `<PROJECT_NAME>`             | Any name, e.g. `shedule-bot`                                                                   |
| `<SERVICE_ACCOUNT_EMAIL>`    | Email shown after creating the service account, e.g. `bot@shedule-bot.iam.gserviceaccount.com` |
| `<YOUR_SHEET_ID>`            | The ID from your Google Sheet URL: `.../spreadsheets/d/<ID>/edit`                              |
| `<username>`                 | Your cPanel username, e.g. `itbomenf`                                                          |

---

## Step 1 — Create a Google Cloud project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click **Select a project → New project**
3. Enter name `<PROJECT_NAME>` → click **Create**
4. Make sure the new project is selected in the top bar

> **💸 Pricing Note:** Google Application Integration is free up to 400 executions/month, 20 GiB data, and 2 Google-only nodes. 
> Exceeding these limits or connecting to third-party apps triggers pay-as-you-go billing.

---

## Step 2 — Enable the Google Sheets API

1. In the left menu go to **APIs & Services → Library**
2. Search for `Google Sheets API`
3. Click it → click **Enable**

Expected state: API page shows **Manage** button (meaning it is enabled).

---

## Step 3 — Create a service account and download the key

1. Go to **APIs & Services → Credentials**
2. Click **Create credentials → Service account**
3. Enter any name → click **Create and continue** → click **Done** (no roles needed)
4. Click the service account email that appears in the list
5. Go to the **Keys** tab → **Add key → Create new key → JSON → Create**
6. A `.json` file downloads automatically — this is your credentials file

Upload it to the server:

```bash
# From your local machine:
scp service_account.json <username>@<YOUR_DOMAIN>:~/Shedule_bot/data/service_account.json
```

Or paste the contents via **cPanel → File Manager** into `~/Shedule_bot/data/service_account.json`.

Verify the file is in place:

```bash
ls ~/Shedule_bot/data/service_account.json
# Expected: file exists
```

> The `data/` directory is in `.gitignore` — the credentials file will never be committed to git.

---

## Step 4 — Share the Google Sheet with the service account

1. Open your Google Sheet
2. Click **Share**
3. Enter `<SERVICE_ACCOUNT_EMAIL>` (from the downloaded JSON file, field `"client_email"`)
4. Set permission to **Editor**
5. Click **Send**

Find the service account email in the JSON file if needed:

```bash
python3 -c "import json; d=json.load(open('data/service_account.json')); print(d['client_email'])"
```

---

## Step 5 — Add variables to .env

Add these two lines to `~/Shedule_bot/.env`:

```
GOOGLE_SHEET_ID=<YOUR_SHEET_ID extracted from the URL you shared (...spreadsheets/d/<ID>/edit)>
GOOGLE_SERVICE_ACCOUNT_JSON=/home/<your cPanel username>/Shedule_bot/data/service_account.json
```

> Find `<YOUR_SHEET_ID>` in the Sheet URL:
> https://docs.google.com/spreadsheets/d/<YOUR_SHEET_ID>/edit


---

## Step 6 — Confirm tab names in schedule_mapping.json

Open `~/Shedule_bot/data/schedule_mapping.json` and confirm these keys match your Google Sheet:

```json
{
  "scheduler_staff_tab":          "Staff",
  "scheduler_schedule_tab":       "Draft",
  "scheduler_output_tab":         "Draft-by-bot",
  "scheduler_month_cell":         "A1",
  "scheduler_year_cell":          "B1",
  "scheduler_header_row":         2,
  "scheduler_day_type_column":    "Day-type",
  "scheduler_department_columns": ["Приймальне відділення", "..."]
}
```

- `scheduler_header_row` — row number (1-indexed) where column headers appear in the Draft tab
- `scheduler_day_type_column` — header of the day-type column in the Draft tab
- `scheduler_department_columns` — list of department column headers in the Draft tab (must match exactly, case-sensitive)

These three keys are independent from `header_row` / `day_type_column` / `department_columns` used by the notification pipeline.

---

## Step 7 — Verify

```bash
cd ~/Shedule_bot && source venv/bin/activate && python3 -c "import os; from dotenv import load_dotenv; load_dotenv('.env'); from google_sheets_adapter import get_staff_list; staff = get_staff_list(os.environ['GOOGLE_SHEET_ID'], 'Staff', os.environ['GOOGLE_SERVICE_ACCOUNT_JSON']); print(f'Staff rows: {len(staff)}'); [print(s) for s in staff[:3]]"
```

Expected output:

```
Staff rows: <number>
{'name': '...', 'department': '...'}
```

---

## Troubleshooting

| Symptom                                          | Check                                                                                                          |
|--------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| `FileNotFoundError: service_account.json`        | Verify the file path in `GOOGLE_SERVICE_ACCOUNT_JSON` is absolute and the file exists                          |
| `gspread.exceptions.SpreadsheetNotFound`         | Verify `GOOGLE_SHEET_ID` in `.env`; verify the sheet is shared with the service account email                  |
| `gspread.exceptions.WorksheetNotFound`           | Verify `scheduler_staff_tab` / `scheduler_schedule_tab` / `scheduler_output_tab` in `schedule_mapping.json` match actual tab names exactly (case-sensitive) |
| `google.auth.exceptions.TransportError`          | Server has no internet access or Google APIs are blocked                                                       |
| `ModuleNotFoundError: No module named 'gspread'` | Run `pip install -r requirements.txt` in venv                                                                  |
