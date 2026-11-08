"""Generate and validate the standalone DPCO algebra proof of concept."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


MODULES = {
    "src/__init__.py": r"""
""",
    "src/models.py": r"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExecStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class ClaimVerdict(Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class VerifyStatus(Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass
class Task:
    id: str
    operation: str
    params: dict[str, Any]
    claim: dict[str, Any] | None = None
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    x: Any = None
    error: str | None = None
""",
    "src/registry.py": r"""
from typing import Any

from .models import Task


class CapabilityRegistry:
    def __init__(self) -> None:
        self.executors: dict[str, dict[str, Any]] = {}

    def register(
        self, exec_id: str, capabilities: list[str], props: dict[str, Any]
    ) -> None:
        self.executors[exec_id] = {
            "capabilities": list(capabilities),
            "props": dict(props),
        }

    def is_compatible(self, task: Task, exec_id: str) -> tuple[bool, str]:
        if exec_id not in self.executors:
            return False, f"UNKNOWN_EXECUTOR: {exec_id}"

        data = self.executors[exec_id]
        if task.operation not in data["capabilities"]:
            return False, f"UNSUPPORTED_OPERATION: {task.operation}"

        if task.constraints.get("exact") and not data["props"].get(
            "exact_arithmetic"
        ):
            return False, "CONSTRAINT_VIOLATION: exact_arithmetic required"

        return True, ""

    def get_candidates(self, task: Task) -> list[str]:
        return [
            exec_id
            for exec_id, data in self.executors.items()
            if not data["props"].get("is_test", False)
            and self.is_compatible(task, exec_id)[0]
        ]
""",
    "src/validation.py": r"""
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
""",
    "src/contradiction.py": r"""
from fractions import Fraction

from .models import Task


class ContradictionGate:
    def check(self, task: Task) -> tuple[bool, str]:
        if task.operation != "solve_system":
            return False, ""

        equations = task.params["eqs"]
        for first in range(len(equations)):
            equation_a = equations[first]
            a1 = Fraction(equation_a["a"])
            d1 = Fraction(equation_a["c"]) - Fraction(equation_a["b"])

            for second in range(first + 1, len(equations)):
                equation_b = equations[second]
                a2 = Fraction(equation_b["a"])
                d2 = Fraction(equation_b["c"]) - Fraction(equation_b["b"])

                if a1 * d2 != a2 * d1:
                    return (
                        True,
                        f"CONTRADICTION: Eq {first} and Eq {second} "
                        "are mutually exclusive.",
                    )

        return False, ""
""",
    "src/dispatcher.py": r"""
from .models import Task
from .registry import CapabilityRegistry


class DeterministicDispatcher:
    def __init__(self, registry: CapabilityRegistry) -> None:
        self.registry = registry

    def dispatch(self, task: Task) -> str | None:
        candidates = self.registry.get_candidates(task)
        if not candidates:
            return None

        candidates.sort(
            key=lambda exec_id: (
                self.registry.executors[exec_id]["props"].get("cost", 999),
                exec_id,
            )
        )
        return candidates[0]
""",
    "src/executors.py": r"""
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
""",
    "src/verifier.py": r"""
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
""",
    "src/classifier.py": r"""
from .models import ClaimVerdict, ExecStatus, VerifyStatus


class ResultClassifier:
    def classify(
        self,
        exec_status: ExecStatus,
        verify_status: VerifyStatus,
        claim_verdict: ClaimVerdict,
    ) -> tuple[ExecStatus, ClaimVerdict, VerifyStatus]:
        if exec_status == ExecStatus.BLOCKED:
            return exec_status, ClaimVerdict.UNKNOWN, VerifyStatus.UNVERIFIED
        if exec_status == ExecStatus.FAILED:
            return exec_status, ClaimVerdict.UNKNOWN, VerifyStatus.NOT_APPLICABLE
        return exec_status, claim_verdict, verify_status
""",
    "src/ledger.py": r"""
import json
import math
import time
from typing import Any


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


class ExecutionLedger:
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath

    def append(self, record: dict[str, Any]) -> None:
        entry = {**record, "timestamp": time.time()}
        with open(self.filepath, "a", encoding="utf-8") as ledger_file:
            ledger_file.write(
                json.dumps(_json_safe(entry), ensure_ascii=False, allow_nan=False)
                + "\n"
            )
""",
    "src/core.py": r"""
import time
from typing import Any

from .classifier import ResultClassifier
from .contradiction import ContradictionGate
from .dispatcher import DeterministicDispatcher
from .executors import BadExecutor, ExactExecutor, NumericalExecutor
from .ledger import ExecutionLedger
from .models import ClaimVerdict, ExecStatus, Task, VerifyStatus
from .registry import CapabilityRegistry
from .validation import ConstraintValidator
from .verifier import IndependentVerifier


class DPCOCore:
    def __init__(self, ledger_path: str) -> None:
        self.registry = CapabilityRegistry()
        self.registry.register(
            "exact_solver",
            ["solve_linear"],
            {"exact_arithmetic": True, "cost": 10},
        )
        self.registry.register(
            "num_solver",
            ["solve_linear"],
            {"exact_arithmetic": False, "cost": 5},
        )
        self.registry.register(
            "test_bad_solver",
            ["solve_linear"],
            {"exact_arithmetic": True, "cost": 99, "is_test": True},
        )

        self.validator = ConstraintValidator()
        self.gate = ContradictionGate()
        self.dispatcher = DeterministicDispatcher(self.registry)
        self.verifier = IndependentVerifier()
        self.classifier = ResultClassifier()
        self.ledger = ExecutionLedger(ledger_path)
        self.executors = {
            "exact_solver": ExactExecutor(),
            "num_solver": NumericalExecutor(),
            "test_bad_solver": BadExecutor(),
        }

    def process_task(
        self, task: Task, force_executor: str | None = None
    ) -> dict[str, Any]:
        log: dict[str, Any] = {
            "task_id": task.id,
            "operation": task.operation,
            "params": task.params,
            "claim": task.claim,
            "constraints": task.constraints,
            "reason": None,
        }

        valid, reason = self.validator.validate(task)
        if not valid:
            log["reason"] = reason
            return self._finalize(
                log, ExecStatus.BLOCKED, VerifyStatus.UNVERIFIED, ClaimVerdict.UNKNOWN
            )

        contradiction, reason = self.gate.check(task)
        if contradiction:
            log["reason"] = reason
            return self._finalize(
                log, ExecStatus.BLOCKED, VerifyStatus.UNVERIFIED, ClaimVerdict.UNKNOWN
            )

        if force_executor is not None:
            compatible, reason = self.registry.is_compatible(task, force_executor)
            if not compatible:
                log["reason"] = f"FORCED_EXECUTOR_REJECTED: {reason}"
                return self._finalize(
                    log,
                    ExecStatus.BLOCKED,
                    VerifyStatus.UNVERIFIED,
                    ClaimVerdict.UNKNOWN,
                )
            exec_id = force_executor
        else:
            exec_id = self.dispatcher.dispatch(task)
            if exec_id is None:
                log["reason"] = "CAPABILITY_GAP"
                return self._finalize(
                    log,
                    ExecStatus.BLOCKED,
                    VerifyStatus.UNVERIFIED,
                    ClaimVerdict.UNKNOWN,
                )

        log["executor"] = exec_id
        started = time.time()
        result = self.executors[exec_id].execute(task)
        log["exec_time_ms"] = round((time.time() - started) * 1000, 2)
        log["executor_root"] = str(result.x) if result.x is not None else None

        if result.error:
            log["reason"] = result.error
            return self._finalize(
                log,
                ExecStatus.FAILED,
                VerifyStatus.NOT_APPLICABLE,
                ClaimVerdict.UNKNOWN,
            )

        verify_status, claim_verdict = self.verifier.verify(task, result, exec_id)
        if verify_status == VerifyStatus.UNVERIFIED:
            log["reason"] = "ROOT_VERIFICATION_FAILED"

        return self._finalize(log, ExecStatus.SUCCESS, verify_status, claim_verdict)

    def _finalize(
        self,
        log: dict[str, Any],
        exec_status: ExecStatus,
        verify_status: VerifyStatus,
        claim_verdict: ClaimVerdict,
    ) -> dict[str, Any]:
        final_exec, final_claim, final_verify = self.classifier.classify(
            exec_status, verify_status, claim_verdict
        )
        log["final_executionStatus"] = final_exec.value
        log["final_claimVerdict"] = final_claim.value
        log["final_verificationStatus"] = final_verify.value
        self.ledger.append(log)
        return log
""",
    "tests.py": r"""
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
""",
}


def validate_generated_project(project_dir: Path) -> bool:
    python_files = sorted(project_dir.rglob("*.py"))
    syntax_ok = True
    for path in python_files:
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec")
            print(f"[SYNTAX PASS] {path.relative_to(project_dir)}")
        except SyntaxError as error:
            syntax_ok = False
            text = error.text.rstrip() if error.text else ""
            print(
                f"[SYNTAX FAIL] {path.relative_to(project_dir)}:"
                f"{error.lineno}: {error.msg}"
            )
            if text:
                print(f"    {text}")

    if not syntax_ok or not python_files:
        if not python_files:
            print("[SYNTAX FAIL] no generated Python files were found")
        return False

    imports = [
        "src.models",
        "src.registry",
        "src.validation",
        "src.contradiction",
        "src.dispatcher",
        "src.executors",
        "src.verifier",
        "src.classifier",
        "src.ledger",
        "src.core",
    ]
    import_script = (
        "import importlib; "
        + "; ".join(f"importlib.import_module({module!r})" for module in imports)
        + "; import importlib.util; "
        + "spec=importlib.util.spec_from_file_location('dpco_tests', 'tests.py'); "
        + "module=importlib.util.module_from_spec(spec); "
        + "spec.loader.exec_module(module); "
        + "print('Imported all src modules and tests.py')"
    )
    result = subprocess.run(
        [sys.executable, "-c", import_script],
        cwd=project_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.returncode:
        print("[IMPORT FAIL]")
        if result.stderr:
            print(result.stderr.rstrip())
        return False
    print("[IMPORT PASS]")
    return True


def generate_project() -> int:
    project_dir = Path(__file__).resolve().parent / "dpco-algebra-poc"
    try:
        project_dir.mkdir(parents=True, exist_ok=True)
        for relative_path, content in MODULES.items():
            path = project_dir / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content.strip() + "\n", encoding="utf-8")
            print(f"Created: {path.relative_to(project_dir)}")
    except OSError as error:
        print(f"[GENERATION FAIL] {error}", file=sys.stderr)
        return 1

    if not validate_generated_project(project_dir):
        print("[PROJECT NOT READY] Generated source verification failed.")
        return 1

    print("[PROJECT GENERATED AND SOURCE-VERIFIED]")
    return 0


if __name__ == "__main__":
    raise SystemExit(generate_project())
