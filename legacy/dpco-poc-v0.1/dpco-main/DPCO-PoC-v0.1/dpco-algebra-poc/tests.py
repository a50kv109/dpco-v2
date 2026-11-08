import json
import math
from fractions import Fraction
from pathlib import Path

from src.core import DPCOCore
from src.models import Task


def main() -> int:
    print("DPCO PoC v0.1 - EXECUTING TESTS")
    ledger_path = Path(__file__).with_name("execution_ledger.jsonl")
    core = DPCOCore(str(ledger_path))
    results = {"PASS": 0, "FAIL": 0}

    def check(
        name: str,
        task: Task,
        expected: tuple[str, str, str],
        expected_reason: str | None = None,
        force_executor: str | None = None,
        expected_root: str | float | None = None,
        expected_executor: str | None = None,
    ) -> dict:
        log = core.process_task(task, force_executor=force_executor)
        actual = (
            log["final_executionStatus"],
            log["final_claimVerdict"],
            log["final_verificationStatus"],
        )
        passed = actual == expected
        if expected_reason is not None:
            passed = passed and expected_reason in str(log.get("reason", ""))
        if expected_root is not None:
            actual_root = log.get("executor_root")
            if isinstance(expected_root, float):
                passed = passed and actual_root is not None and math.isclose(
                    float(actual_root), expected_root, rel_tol=1e-12, abs_tol=1e-12
                )
            else:
                passed = passed and actual_root == expected_root
        if expected_executor is not None:
            passed = passed and log.get("executor") == expected_executor

        if passed:
            print(f"[PASS] {name}")
            results["PASS"] += 1
        else:
            print(
                f"[FAIL] {name}: expected {expected}, reason "
                f"{expected_reason!r}, root {expected_root!r}; got {actual}, "
                f"reason {log.get('reason')!r}, root {log.get('executor_root')!r}"
            )
            results["FAIL"] += 1
        return log

    success_verified = ("SUCCESS", "NOT_APPLICABLE", "VERIFIED")
    blocked_unknown = ("BLOCKED", "UNKNOWN", "UNVERIFIED")

    # T01-T10 comprise 11 checks because T03 has two cases.
    check(
        "T01 - Exact Arithmetic",
        Task("T01", "solve_linear", {"a": 2, "b": 0, "c": 3},
             constraints={"exact": True}),
        success_verified,
        expected_root="3/2",
    )
    check(
        "T02 - False Claim",
        Task("T02", "solve_linear", {"a": 2, "b": 0, "c": 3},
             claim={"x": 2}, constraints={"exact": True}),
        ("SUCCESS", "FALSE", "VERIFIED"),
    )
    check(
        "T03.1 - Shift Contradiction",
        Task("T03.1", "solve_system", {"eqs": [
            {"a": 1, "b": 0, "c": 2}, {"a": 1, "b": 1, "c": 4}
        ]}),
        blocked_unknown,
        "CONTRADICTION",
    )
    check(
        "T03.2 - Proportional Contradiction",
        Task("T03.2", "solve_system", {"eqs": [
            {"a": 1, "b": 0, "c": 2}, {"a": 2, "b": 0, "c": 5}
        ]}),
        blocked_unknown,
        "CONTRADICTION",
    )
    check(
        "T04 - Capability Gap",
        Task("T04", "solve_cubic", {"a": 1, "b": 2, "c": 3, "d": 4}),
        blocked_unknown,
        "CAPABILITY_GAP",
    )
    check(
        "T05 - Verification Failure",
        Task("T05", "solve_linear", {"a": 2, "b": 0, "c": 3},
             claim={"x": 2}),
        ("SUCCESS", "UNKNOWN", "UNVERIFIED"),
        "ROOT_VERIFICATION_FAILED",
        force_executor="test_bad_solver",
    )
    check(
        "T06 - Deterministic Dispatch",
        Task("T06", "solve_linear", {"a": 3, "b": 0, "c": 1}),
        success_verified,
        expected_root=1 / 3,
        expected_executor="num_solver",
    )
    check(
        "T07 - Forced Executor Constraint Violation",
        Task("T07", "solve_linear", {"a": 2, "b": 0, "c": 3},
             constraints={"exact": True}),
        blocked_unknown,
        "CONSTRAINT_VIOLATION",
        force_executor="num_solver",
    )
    check(
        "T08 - Consistent Two-Equation System",
        Task("T08", "solve_system", {"eqs": [
            {"a": 1, "b": 0, "c": 2}, {"a": 2, "b": 0, "c": 4}
        ]}),
        blocked_unknown,
        "CAPABILITY_GAP",
    )
    check(
        "T09 - Consistent Three-Equation System",
        Task("T09", "solve_system", {"eqs": [
            {"a": 1, "b": 0, "c": 2}, {"a": 2, "b": 0, "c": 4},
            {"a": 3, "b": 0, "c": 6}
        ]}),
        blocked_unknown,
        "CAPABILITY_GAP",
    )
    check(
        "T10 - Three-Equation Contradiction",
        Task("T10", "solve_system", {"eqs": [
            {"a": 1, "b": 0, "c": 2}, {"a": 2, "b": 0, "c": 4},
            {"a": 3, "b": 0, "c": 7}
        ]}),
        blocked_unknown,
        "CONTRADICTION",
    )
    matrix_passes = results["PASS"]

    # Supplemental edge checks do not change the T01-T10 matrix.
    check(
        "E01 - Negative Coefficients",
        Task("E01", "solve_linear", {"a": -2, "b": 3, "c": -2},
             constraints={"exact": True}),
        success_verified,
        expected_root="5/2",
    )
    check(
        "E02 - Fractional Coefficients",
        Task("E02", "solve_linear", {"a": "1/2", "b": "1/3", "c": "5/6"},
             constraints={"exact": True}),
        success_verified,
        expected_root="1",
    )
    large_value = 10**80
    large_root = Fraction(large_value - 5, 3)
    check(
        "E03 - Large Integer Coefficients",
        Task("E03", "solve_linear", {"a": 3, "b": 5, "c": large_value},
             constraints={"exact": True}),
        success_verified,
        expected_root=str(large_root),
    )
    check(
        "E04 - Missing Parameter",
        Task("E04", "solve_linear", {"a": 1, "b": 2}),
        blocked_unknown,
        "missing coefficient 'c'",
    )
    check(
        "E05 - Zero Coefficient",
        Task("E05", "solve_linear", {"a": 0, "b": 2, "c": 3}),
        blocked_unknown,
        "cannot be zero",
    )
    check(
        "E06 - Malformed Equation",
        Task("E06", "solve_system", {"eqs": [{"a": 1, "b": 2}]}),
        blocked_unknown,
        "missing coefficient 'c'",
    )
    check(
        "E07 - Non-Finite Coefficient",
        Task("E07", "solve_linear", {"a": float("inf"), "b": 0, "c": 1}),
        blocked_unknown,
        "must be finite numeric data",
    )

    try:
        def reject_non_json_constant(value: str) -> None:
            raise ValueError(f"non-standard JSON constant: {value}")

        ledger_records = [
            json.loads(
                line, parse_constant=reject_non_json_constant
            )
            for line in ledger_path.read_text(encoding="utf-8").splitlines()
        ]
        if len(ledger_records) < 18:
            raise ValueError(f"expected at least 18 ledger records, got {len(ledger_records)}")
        required_fields = {
            "task_id", "operation", "params", "claim", "constraints", "reason",
            "final_executionStatus", "final_claimVerdict",
            "final_verificationStatus", "timestamp",
        }
        if not required_fields.issubset(ledger_records[-1]):
            raise ValueError("latest ledger record is missing required fields")
        print("[PASS] JSONL ledger records parse and contain required fields")
        results["PASS"] += 1
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"[FAIL] JSONL ledger validation: {error}")
        results["FAIL"] += 1

    print(
        f"\nSUMMARY: {results['PASS']} PASS, {results['FAIL']} FAIL "
        f"(T01-T10 matrix: {matrix_passes}/11; "
        "7 supplemental checks plus ledger validation)"
    )
    return 0 if results["FAIL"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
