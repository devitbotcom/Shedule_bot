from typing import Optional
from models import Shift, ShiftContext

DUTY_ORDER = {"Day": 0, "Night": 1, "24h": 2}


def _sort_key(shift: Shift) -> tuple:
    return (shift.shift_date, DUTY_ORDER.get(shift.duty_type, 99))


def compute_contexts(shifts: list) -> list:
    sorted_shifts = sorted(shifts, key=_sort_key)
    contexts = []

    for i, shift in enumerate(sorted_shifts):
        prev_colleague: Optional[Shift] = None
        next_colleague: Optional[Shift] = None

        for j in range(i - 1, -1, -1):
            candidate = sorted_shifts[j]
            if candidate.role == shift.role and candidate.location == shift.location:
                prev_colleague = candidate
                break

        for j in range(i + 1, len(sorted_shifts)):
            candidate = sorted_shifts[j]
            if candidate.role == shift.role and candidate.location == shift.location:
                next_colleague = candidate
                break

        contexts.append(ShiftContext(
            shift=shift,
            prev_colleague=prev_colleague,
            next_colleague=next_colleague,
        ))

    return contexts
