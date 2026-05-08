# Known Issues


### 005-1 Can admin be a setting file not only defined by communication with bot as now [High, on hold]

Actual: U005-4: run on the server:
   ```
   cd ~/Shedule_bot && source venv/bin/activate                                                                                                                                     
   TZ=Europe/Kyiv python main.py --bootstrap-it <YOUR_TELEGRAM_ID>
   
   Replace <YOUR_TELEGRAM_ID> with the ID shown in the /start reply.   
   ```

### 005-2 Too obsessive for commands [Minor, on hold]

Actual: bot reacts on absolutely any message, not only commands (chat message, add user, etc).

### 005-3 U005-5 help menu for IT admin not verified [Risk, deferred]

U005-5 (verify `/setrole` appears in `/help` for IT role) was skipped during UAT. Deferred — to be tested when IT admin role is exercised in S006d or later.

### 006b-01 `--health` does not check Google Sheets connectivity [P1, S006c+]

`--health` passes even when Google Sheets credentials are invalid or the sheet is unreachable. A misconfigured service account or wrong `GOOGLE_SHEET_ID` goes undetected until `/draft` fails at runtime. Health check should include a Google Sheets connectivity probe.

### 006b-02 Webhook handler does not log each incoming request attempt [P2, S006c+]

Only errors are logged to `webhook.log`. Each incoming Telegram update is not recorded, making silent failures (bot receives message but does nothing) invisible to IT without manual debugging.

### 006b2-01 Invalid year silently skips validation [Low, S007+]

In `bot_hook._cmd_draft`, if `year_str` cannot be parsed as an integer, `year_int` is set to `None` and the entire validator call is skipped without any feedback to Head. Only V4 and V6 require `year_int`; checks V1, V2, V3, V5, V7 could still run. No warning is sent to Head that validation was bypassed.

### 06b-03 Add Google Sheet link to `/draft` success response [Low, backlog]

The positive `/draft` reply does not include a link to the Google Sheet where the result was written. Head must navigate to the sheet manually after running the command.

Expected: success message includes a clickable link to the output tab, e.g.:
```
✅ Чернетку розкладу на червень 2026 записано у вкладку 'Draft-by-bot'.
🔗 https://docs.google.com/spreadsheets/d/<SHEET_ID>
```

The `GOOGLE_SHEET_ID` is already available in `bot_hook._cmd_draft` at the time the reply is sent.