"""Run once to generate tests/fixtures/sample_schedule.xlsx and schedule_mapping.json"""
import json
import os

import openpyxl

FIXTURES_DIR     = os.path.join(os.path.dirname(__file__), "fixtures")
FIXTURE_XLSX     = os.path.join(FIXTURES_DIR, "sample_schedule.xlsx")
FIXTURE_MAPPING  = os.path.join(FIXTURES_DIR, "schedule_mapping.json")

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
    "Ургенція спеціалістів на дому",   # present but listed in skip_columns
])

# Row 7+: data rows
# date          day_type   Приймальне           Анестезіологія   Ургенція
ws.append(["31-03-2026", "holiday", "Alice Kovalenko",  None,            None])
ws.append(["01-04-2026", "labor",   "Bob Petrenko",     "Carol Melnyk",  None])
ws.append(["02-04-2026", "labor",   "Alice Kovalenko",  "Dan Sydorenko", None])

wb.save(FIXTURE_XLSX)
print(f"XLSX fixture created: {FIXTURE_XLSX}")

# --- schedule_mapping.json fixture ---
mapping = {
    "header_row": 6,
    "date_column": "Дата",
    "day_type_column": "Day-type",
    "skip_columns": ["Ургенція спеціалістів на дому"],
    "department_columns": [
        "Приймальне відділення",
        "Анестезіологія",
    ],
    "shift_hours": {
        "labor":   "17:00",
        "holiday": "09:00",
        "other":   "09:00",
    },
}

with open(FIXTURE_MAPPING, "w", encoding="utf-8") as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)

print(f"Mapping fixture created: {FIXTURE_MAPPING}")
