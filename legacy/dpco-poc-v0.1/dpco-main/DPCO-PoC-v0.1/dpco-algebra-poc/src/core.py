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
