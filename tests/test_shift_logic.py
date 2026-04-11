import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import Shift
from shift_logic import compute_contexts


def make_shift(name, role, duty, date, location="Ward A"):
    return Shift(name, role, duty, date, location, "telegram", "000")


SHIFTS = [
    make_shift("Alice Kovalenko", "Nurse",  "Night", "2026-03-31"),  # boundary row
    make_shift("Bob Petrenko",    "Doctor", "Day",   "2026-04-01"),
    make_shift("Carol Melnyk",    "Nurse",  "Night", "2026-04-01"),
    make_shift("Alice Kovalenko", "Nurse",  "Day",   "2026-04-02"),
    make_shift("Dan Sydorenko",   "Doctor", "24h",   "2026-04-02"),
]


def _ctx_for(name, date):
    ctxs = compute_contexts(SHIFTS)
    for c in ctxs:
        if c.shift.employee_name == name and c.shift.shift_date == date:
            return c
    raise ValueError(f"Context not found: {name} {date}")


def test_middle_shift_has_prev_and_next():
    ctx = _ctx_for("Carol Melnyk", "2026-04-01")
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


def test_role_isolation_nurse_vs_doctor():
    ctx = _ctx_for("Bob Petrenko", "2026-04-01")
    # Bob is a Doctor — prev/next must be Doctors only
    if ctx.prev_colleague:
        assert ctx.prev_colleague.role == "Doctor"
    if ctx.next_colleague:
        assert ctx.next_colleague.role == "Doctor"


def test_pure_function_no_mutation():
    original = list(SHIFTS)
    compute_contexts(SHIFTS)
    assert SHIFTS == original


def test_output_length_matches_input():
    result = compute_contexts(SHIFTS)
    assert len(result) == len(SHIFTS)
