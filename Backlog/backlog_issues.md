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