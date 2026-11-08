import math
from fractions import Fraction
from typing import Any

from .models import Task


def _as_fraction(value: Any) -> Fraction:
    if isinstance(value, bool):
        raise ValueError("boolean is not a numeric coefficient")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("coefficient must be finite")
    return Fraction(value)


class ConstraintValidator:
    def validate(self, task: Task) -> tuple[bool, str]:
        if task.operation not in {"solve_linear", "solve_system"}:
            return True, ""
        if not isinstance(task.params, dict):
            return False, "VALIDATION_ERROR: params must be an object"

        if task.operation == "solve_linear":
            equations = [task.params]
        else:
            equations = task.params.get("eqs")
            if not isinstance(equations, list) or not equations:
                return False, "VALIDATION_ERROR: eqs must be a non-empty list"

        for index, equation in enumerate(equations):
            label = f" in eq {index}" if task.operation == "solve_system" else ""
            if not isinstance(equation, dict):
                return False, f"VALIDATION_ERROR: equation{label} must be an object"

            for key in ("a", "b", "c"):
                if key not in equation:
                    return False, (
                        f"VALIDATION_ERROR: missing coefficient '{key}'{label}"
                    )
                try:
                    _as_fraction(equation[key])
                except (TypeError, ValueError, ZeroDivisionError, OverflowError):
                    return False, (
                        f"VALIDATION_ERROR: coefficient '{key}' must be finite "
                        f"numeric data{label}"
                    )

            if _as_fraction(equation["a"]) == 0:
                return False, (
                    f"VALIDATION_ERROR: coefficient 'a' cannot be zero{label}"
                )

        return True, ""
