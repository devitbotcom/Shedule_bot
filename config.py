import os
import sys

from dotenv import load_dotenv

load_dotenv()

REQUIRED_VARS = (
    "XLSX_PATH",
    "DB_PATH",
    "LOG_DIR",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_GROUP_CHAT_ID",
)


def load_config() -> dict:
    missing = [v for v in REQUIRED_VARS if not os.getenv(v)]
    if missing:
        for var in missing:
            print(f"[CONFIG]  ❌ missing required variable: {var}")
        sys.exit(1)
    return {v: os.getenv(v) for v in REQUIRED_VARS}
