"""Run once to generate tests/fixtures/sample_schedule.xlsx and contacts.json"""
import json
import os

import openpyxl

FIXTURES_DIR  = os.path.join(os.path.dirname(__file__), "fixtures")
FIXTURE_XLSX  = os.path.join(FIXTURES_DIR, "sample_schedule.xlsx")
FIXTURE_CONTACTS = os.path.join(FIXTURES_DIR, "contacts.json")

os.makedirs(FIXTURES_DIR, exist_ok=True)

# --- XLSX fixture ---
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Schedule"

# Rows 1-5: title block (mirrors real XLSX structure)
ws.append(["Графік чергувань — Квітень 2026"])
ws.append([])
ws.append([])
ws.append([])
ws.append([])

# Row 6: column headers
ws.append([
    "Дата",
    "Day-type",
    "Приймальне відділення",
    "Анестезіологія",
    "Ургенція спеціалістів на дому",   # present but skipped in POC
])

# Row 7+: data rows
# date        day_type  Приймальне           Анестезіологія   Ургенція
ws.append(["31-03-2026", "holiday", "Alice Kovalenko",  None,            None])
ws.append(["01-04-2026", "labor",   "Bob Petrenko",     "Carol Melnyk",  None])
ws.append(["02-04-2026", "labor",   "Alice Kovalenko",  "Dan Sydorenko", None])

wb.save(FIXTURE_XLSX)
print(f"XLSX fixture created: {FIXTURE_XLSX}")

# --- contacts.json fixture ---
contacts = [
    {"name": "Alice Kovalenko", "channels": {"telegram": "111111"}, "primary_channel": "telegram"},
    {"name": "Bob Petrenko",    "channels": {"telegram": "222222"}, "primary_channel": "telegram"},
    {"name": "Carol Melnyk",    "channels": {"viber":    "333333"}, "primary_channel": "viber"},
    {"name": "Dan Sydorenko",   "channels": {"telegram": "444444"}, "primary_channel": "telegram"},
]

with open(FIXTURE_CONTACTS, "w", encoding="utf-8") as f:
    json.dump(contacts, f, ensure_ascii=False, indent=2)

print(f"Contacts fixture created: {FIXTURE_CONTACTS}")
