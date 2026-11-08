import math
from fractions import Fraction

from .models import ExecutionResult, Task


class ExactExecutor:
    def execute(self, task: Task) -> ExecutionResult:
        try:
            a = Fraction(task.params["a"])
            b = Fraction(task.params["b"])
            c = Fraction(task.params["c"])
            return ExecutionResult(x=(c - b) / a)
        except (KeyError, TypeError, ValueError, ZeroDivisionError, OverflowError) as error:
            return ExecutionResult(error=str(error))


class NumericalExecutor:
    def execute(self, task: Task) -> ExecutionResult:
        try:
            a = float(task.params["a"])
            b = float(task.params["b"])
            c = float(task.params["c"])
            if not all(math.isfinite(value) for value in (a, b, c)):
                return ExecutionResult(error="coefficients must be finite")
            return ExecutionResult(x=(c - b) / a)
        except (KeyError, TypeError, ValueError, ZeroDivisionError, OverflowError) as error:
            return ExecutionResult(error=str(error))


class BadExecutor:
    def execute(self, task: Task) -> ExecutionResult:
        return ExecutionResult(x=2.0)
