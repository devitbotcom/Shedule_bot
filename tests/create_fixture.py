"""Run once to generate tests/fixtures/sample_schedule.xlsx"""
import os
import openpyxl

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "sample_schedule.xlsx")

wb = openpyxl.Workbook()

# Sheet 1 — Schedule
ws1 = wb.active
ws1.title = "Schedule"
ws1.append(["shift_date", "employee_name", "duty_type"])
ws1.append(["31-03-2026", "Alice Kovalenko", "Night"])
ws1.append(["01-04-2026", "Bob Petrenko",    "Day"])
ws1.append(["01-04-2026", "Carol Melnyk",    "Night"])
ws1.append(["02-04-2026", "Alice Kovalenko", "Day"])
ws1.append(["02-04-2026", "Dan Sydorenko",   "24h"])

# Sheet 2 — Employee Registry
ws2 = wb.create_sheet("Employee Registry")
ws2.append(["employee_name", "role", "messenger", "contact_id"])
ws2.append(["Alice Kovalenko", "Nurse",  "telegram", "111111"])
ws2.append(["Bob Petrenko",    "Doctor", "telegram", "222222"])
ws2.append(["Carol Melnyk",    "Nurse",  "viber",    "333333"])
ws2.append(["Dan Sydorenko",   "Doctor", "telegram", "444444"])

wb.save(FIXTURE_PATH)
print(f"Fixture created: {FIXTURE_PATH}")
