from typing import Optional

from models import Shift, ShiftContext


def compute_contexts(shifts: list[Shift]) -> list[ShiftContext]:
    sorted_shifts = sorted(shifts, key=lambda s: (s.shift_date, s.department))
    contexts: list[ShiftContext] = []

    for i, shift in enumerate(sorted_shifts):
        prev_colleague: Optional[Shift] = None
        next_colleague: Optional[Shift] = None

        for j in range(i - 1, -1, -1):
            if sorted_shifts[j].department == shift.department:
                prev_colleague = sorted_shifts[j]
                break

        for j in range(i + 1, len(sorted_shifts)):
            if sorted_shifts[j].department == shift.department:
                next_colleague = sorted_shifts[j]
                break

        contexts.append(ShiftContext(
            shift=shift,
            prev_colleague=prev_colleague,
            next_colleague=next_colleague,
        ))

    return contexts
