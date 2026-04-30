import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import Shift
from shift_logic import compute_contexts


def make_shift(name: str, dept: str, day_type: str, date: str) -> Shift:
    return Shift(name, dept, day_type, date, "telegram", "000")


# Mirrors the fixture XLSX structure
SHIFTS = [
    make_shift("Alice Kovalenko", "Приймальне відділення", "holiday", "2026-03-31"),  # boundary
    make_shift("Bob Petrenko",    "Приймальне відділення", "labor",   "2026-04-01"),
    make_shift("Carol Melnyk",    "Анестезіологія",        "labor",   "2026-04-01"),
    make_shift("Alice Kovalenko", "Приймальне відділення", "labor",   "2026-04-02"),
    make_shift("Dan Sydorenko",   "Анестезіологія",        "labor",   "2026-04-02"),
]


def _ctx_for(name: str, date: str):
    ctxs = compute_contexts(SHIFTS)
    for c in ctxs:
        if c.shift.employee_name == name and c.shift.shift_date == date:
            return c
    raise ValueError(f"Context not found: {name} {date}")


def test_middle_shift_has_prev_and_next():
    ctx = _ctx_for("Bob Petrenko", "2026-04-01")
    assert ctx.prev_colleague is not None
    assert ctx.prev_colleague.employee_name == "Alice Kovalenko"
    assert ctx.next_colleague is not None
    assert ctx.next_colleague.employee_name == "Alice Kovalenko"
    assert ctx.next_colleague.shift_date == "2026-04-02"


def test_first_shift_has_no_prev():
    ctx = _ctx_for("Alice Kovalenko", "2026-03-31")
    assert ctx.prev_colleague is None


def test_last_shift_has_no_next():
    ctx = _ctx_for("Alice Kovalenko", "2026-04-02")
    assert ctx.next_colleague is None


def test_department_isolation():
    ctx = _ctx_for("Carol Melnyk", "2026-04-01")
    # Carol is in Анестезіологія — prev/next must be same dept
    assert ctx.prev_colleague is None  # first in that dept
    assert ctx.next_colleague is not None
    assert ctx.next_colleague.department == "Анестезіологія"
    assert ctx.next_colleague.employee_name == "Dan Sydorenko"


def test_pure_function_no_mutation():
    original = list(SHIFTS)
    compute_contexts(SHIFTS)
    assert SHIFTS == original


def test_output_length_matches_input():
    result = compute_contexts(SHIFTS)
    assert len(result) == len(SHIFTS)
