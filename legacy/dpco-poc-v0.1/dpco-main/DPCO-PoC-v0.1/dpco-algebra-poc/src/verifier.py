import math
from fractions import Fraction

from .models import (
    ClaimVerdict,
    ExecutionResult,
    Task,
    VerifyStatus,
)


class IndependentVerifier:
    def verify(
        self, task: Task, result: ExecutionResult, exec_id: str
    ) -> tuple[VerifyStatus, ClaimVerdict]:
        if result.error or result.x is None:
            return VerifyStatus.NOT_APPLICABLE, ClaimVerdict.UNKNOWN

        try:
            if exec_id in {"exact_solver", "test_bad_solver"}:
                a = Fraction(task.params["a"])
                b = Fraction(task.params["b"])
                c = Fraction(task.params["c"])
                x = Fraction(result.x)
                root_is_valid = a * x + b == c
            else:
                a = float(task.params["a"])
                b = float(task.params["b"])
                c = float(task.params["c"])
                x = float(result.x)
                root_is_valid = (
                    all(math.isfinite(value) for value in (a, b, c, x))
                    and math.isclose(
                        a * x + b, c, rel_tol=1e-5, abs_tol=1e-9
                    )
                )
        except (KeyError, TypeError, ValueError, ZeroDivisionError, OverflowError):
            return VerifyStatus.UNVERIFIED, ClaimVerdict.UNKNOWN

        if not root_is_valid:
            return VerifyStatus.UNVERIFIED, ClaimVerdict.UNKNOWN

        if not task.claim or "x" not in task.claim:
            return VerifyStatus.VERIFIED, ClaimVerdict.NOT_APPLICABLE

        try:
            if exec_id in {"exact_solver", "test_bad_solver"}:
                claim_is_true = x == Fraction(task.claim["x"])
            else:
                claim_x = float(task.claim["x"])
                claim_is_true = math.isfinite(claim_x) and math.isclose(
                    x, claim_x, rel_tol=1e-5, abs_tol=1e-9
                )
        except (KeyError, TypeError, ValueError, ZeroDivisionError, OverflowError):
            return VerifyStatus.VERIFIED, ClaimVerdict.UNKNOWN

        verdict = ClaimVerdict.TRUE if claim_is_true else ClaimVerdict.FALSE
        return VerifyStatus.VERIFIED, verdict
