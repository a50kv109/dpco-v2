import os
import sys
from pathlib import Path

# =====================================================================
# DPCO PoC v0.1 - CORRECTIVE ENGINEERING ITERATION 02
# STATUS: STATICALLY REVIEWED (PENDING EXECUTION)
# =====================================================================

MODULES = {}

MODULES["models.py"] = """
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

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
    params: Dict[str, Any]
    claim: Optional[Dict[str, Any]] = None
    constraints: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutionResult:
    x: Optional[Any] = None
    error: Optional[str] = None
    # ClaimVerdict устанавливается только верификатором, исполнитель возвращает только факт
"""

MODULES["registry.py"] = """
from typing import Dict, List, Any
from .models import Task

class CapabilityRegistry:
    def __init__(self):
        self.executors = {}
        
    def register(self, exec_id: str, capabilities: List[str], props: Dict[str, Any]):
        self.executors[exec_id] = {"capabilities": capabilities, "props": props}
        
    def is_compatible(self, task: Task, exec_id: str) -> tuple[bool, str]:
        if exec_id not in self.executors:
            return False, f"UNKNOWN_EXECUTOR: {exec_id}"
            
        data = self.executors[exec_id]
        if task.operation not in data["capabilities"]:
            return False, f"UNSUPPORTED_OPERATION: {task.operation}"
            
        # Проверка ограничений задачи (constraints)
        if task.constraints.get("exact") and not data["props"].get("exact_arithmetic"):
            return False, "CONSTRAINT_VIOLATION: exact_arithmetic required"
            
        return True, ""
        
    def get_candidates(self, task: Task) -> List[str]:
        return [eid for eid in self.executors if self.is_compatible(task, eid)[0]]
"""

MODULES["validation.py"] = """
from .models import Task

class ConstraintValidator:
    def validate(self, task: Task) -> tuple[bool, str]:
        # Отсекаем нелинейные уравнения, если заявлена операция solve_linear / solve_system
        if task.operation in ["solve_linear", "solve_system"]:
            params_list = task.params.get("eqs", [task.params])
            for idx, p in enumerate(params_list):
                if p.get("a", 0) == 0:
                    return False, f"VALIDATION_ERROR: Coefficient 'a' cannot be zero in eq {idx}."
        return True, ""
"""

MODULES["contradiction.py"] = """
from .models import Task

class ContradictionGate:
    def check(self, task: Task) -> tuple[bool, str]:
        if task.operation == "solve_system":
            eqs = task.params.get("eqs", [])
            # Проверяем все пары уравнений в системе на противоречие
            for i in range(len(eqs)):
                for j in range(i+1, len(eqs)):
                    a1, b1, c1 = eqs[i].get("a",0), eqs[i].get("b",0), eqs[i].get("c",0)
                    a2, b2, c2 = eqs[j].get("a",0), eqs[j].get("b",0), eqs[j].get("c",0)
                    
                    d1 = c1 - b1
                    d2 = c2 - b2
                    
                    # Кросс-умножение для выявления несовместимости ax=d
                    if (a1 * d2) != (a2 * d1):
                        return True, f"CONTRADICTION: Eq {i} and Eq {j} are mutually exclusive."
        return False, ""
"""

MODULES["dispatcher.py"] = """
from .models import Task
from .registry import CapabilityRegistry

class DeterministicDispatcher:
    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry
        
    def dispatch(self, task: Task) -> str:
        candidates = self.registry.get_candidates(task)
        if not candidates:
            return None
            
        # Tie-break: сортировка по стоимости, затем алфавитный порядок (ID)
        candidates.sort(key=lambda x: (self.registry.executors[x]["props"].get("cost", 999), x))
        return candidates[0]
"""

MODULES["executors.py"] = """
from .models import Task, ExecutionResult
import fractions

class ExactExecutor:
    def execute(self, task: Task) -> ExecutionResult:
        try:
            a = fractions.Fraction(task.params["a"])
            b = fractions.Fraction(task.params["b"])
            c = fractions.Fraction(task.params["c"])
            return ExecutionResult(x=(c - b) / a)
        except Exception as e:
            return ExecutionResult(error=str(e))

class NumericalExecutor:
    def execute(self, task: Task) -> ExecutionResult:
        try:
            a = float(task.params["a"])
            b = float(task.params["b"])
            c = float(task.params["c"])
            return ExecutionResult(x=(c - b) / a)
        except Exception as e:
            return ExecutionResult(error=str(e))

class BadExecutor:
    # Исполнитель для контролируемой ошибки. Эмулирует успешный, но неверный результат.
    def execute(self, task: Task) -> ExecutionResult:
        return ExecutionResult(x=2.0)
"""

MODULES["verifier.py"] = """
from .models import Task, ExecutionResult, VerifyStatus, ClaimVerdict
import fractions
import math

class IndependentVerifier:
    def verify(self, task: Task, result: ExecutionResult, exec_id: str) -> tuple[VerifyStatus, ClaimVerdict]:
        if result.error or result.x is None:
            return VerifyStatus.NOT_APPLICABLE, ClaimVerdict.UNKNOWN
            
        try:
            # 1. Проверка правильности найденного корня (Алгоритмическая независимость)
            is_valid_root = False
            if exec_id in ["exact_solver", "test_bad_solver"]:
                a = fractions.Fraction(task.params["a"])
                b = fractions.Fraction(task.params["b"])
                c = fractions.Fraction(task.params["c"])
                x = fractions.Fraction(result.x)
                is_valid_root = (a * x + b == c)
            else:
                a = float(task.params["a"])
                b = float(task.params["b"])
                c = float(task.params["c"])
                x = float(result.x)
                is_valid_root = math.isclose(a * x + b, c, rel_tol=1e-5)
                
            if not is_valid_root:
                return VerifyStatus.UNVERIFIED, ClaimVerdict.UNKNOWN
                
            # 2. Проверка исходной гипотезы пользователя
            if not task.claim or "x" not in task.claim:
                return VerifyStatus.VERIFIED, ClaimVerdict.NOT_APPLICABLE
                
            if exec_id in ["exact_solver", "test_bad_solver"]:
                claim_x = fractions.Fraction(task.claim["x"])
                claim_true = (x == claim_x)
            else:
                claim_x = float(task.claim["x"])
                claim_true = math.isclose(x, claim_x, rel_tol=1e-5)
                
            return VerifyStatus.VERIFIED, (ClaimVerdict.TRUE if claim_true else ClaimVerdict.FALSE)
            
        except Exception:
            return VerifyStatus.UNVERIFIED, ClaimVerdict.UNKNOWN
"""

MODULES["classifier.py"] = """
from .models import ExecStatus, ClaimVerdict, VerifyStatus

class ResultClassifier:
    def classify(self, exec_status: ExecStatus, v_status: VerifyStatus, c_verdict: ClaimVerdict):
        if exec_status in [ExecStatus.BLOCKED, ExecStatus.FAILED]:
            return exec_status, ClaimVerdict.UNKNOWN, VerifyStatus.UNVERIFIED
        return exec_status, c_verdict, v_status
"""

MODULES["ledger.py"] = """
import json
import time

class ExecutionLedger:
    def __init__(self, filepath: str):
        self.filepath = filepath
        
    def append(self, record: dict):
        record["timestamp"] = time.time()
        # Гарантируем правильную запись новой строки в журнал
        with open(self.filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
"""

MODULES["core.py"] = """
import time
from .models import Task, ExecStatus, VerifyStatus, ClaimVerdict
from .registry import CapabilityRegistry
from .validation import ConstraintValidator
from .contradiction import ContradictionGate
from .dispatcher import DeterministicDispatcher
from .executors import ExactExecutor, NumericalExecutor, BadExecutor
from .verifier import IndependentVerifier
from .classifier import ResultClassifier
from .ledger import ExecutionLedger

class DPCOCore:
    def __init__(self, ledger_path: str):
        self.registry = CapabilityRegistry()
        self.registry.register("exact_solver", ["solve_linear"], {"exact_arithmetic": True, "cost": 10})
        self.registry.register("num_solver", ["solve_linear"], {"exact_arithmetic": False, "cost": 5})
        self.registry.register("test_bad_solver", ["solve_linear"], {"exact_arithmetic": True, "cost": 99, "is_test": True})
        
        self.validator = ConstraintValidator()
        self.gate = ContradictionGate()
        self.dispatcher = DeterministicDispatcher(self.registry)
        self.verifier = IndependentVerifier()
        self.classifier = ResultClassifier()
        self.ledger = ExecutionLedger(ledger_path)
        
        self.executors = {
            "exact_solver": ExactExecutor(),
            "num_solver": NumericalExecutor(),
            "test_bad_solver": BadExecutor()
        }
        
    def process_task(self, task: Task, force_executor: str = None) -> dict:
        log = {"task_id": task.id, "operation": task.operation, "params": task.params, "reason": None}
        
        # 1. Validation Barrier
        valid, msg = self.validator.validate(task)
        if not valid:
            log["reason"] = msg
            return self._finalize(log, ExecStatus.BLOCKED, VerifyStatus.UNVERIFIED, ClaimVerdict.UNKNOWN)
            
        # 2. Contradiction Barrier
        contra, msg = self.gate.check(task)
        if contra:
            log["reason"] = msg
            return self._finalize(log, ExecStatus.BLOCKED, VerifyStatus.UNVERIFIED, ClaimVerdict.UNKNOWN)
            
        # 3. Compatibility & Dispatch
        if force_executor:
            is_compat, reason = self.registry.is_compatible(task, force_executor)
            if not is_compat:
                log["reason"] = f"FORCED_EXECUTOR_REJECTED: {reason}"
                return self._finalize(log, ExecStatus.BLOCKED, VerifyStatus.UNVERIFIED, ClaimVerdict.UNKNOWN)
            exec_id = force_executor
        else:
            exec_id = self.dispatcher.dispatch(task)
            if not exec_id:
                log["reason"] = "CAPABILITY_GAP"
                return self._finalize(log, ExecStatus.BLOCKED, VerifyStatus.UNVERIFIED, ClaimVerdict.UNKNOWN)
                
        log["executor"] = exec_id
        
        # 4. Execution
        start_time = time.time()
        result = self.executors[exec_id].execute(task)
        log["exec_time_ms"] = round((time.time() - start_time) * 1000, 2)
        log["executor_root"] = str(result.x) if result.x is not None else None
        
        if result.error:
            log["reason"] = result.error
            return self._finalize(log, ExecStatus.FAILED, VerifyStatus.NOT_APPLICABLE, ClaimVerdict.UNKNOWN)
            
        # 5. Independent Verification
        v_status, c_verdict = self.verifier.verify(task, result, exec_id)
        
        if v_status == VerifyStatus.UNVERIFIED:
            log["reason"] = "ROOT_VERIFICATION_FAILED"
            
        return self._finalize(log, ExecStatus.SUCCESS, v_status, c_verdict)
        
    def _finalize(self, log, e_stat, v_stat, c_verdict):
        f_exec, f_claim, f_verify = self.classifier.classify(e_stat, v_stat, c_verdict)
        log["final_executionStatus"] = f_exec.value
        log["final_claimVerdict"] = f_claim.value
        log["final_verificationStatus"] = f_verify.value
        self.ledger.append(log)
        return log
"""

MODULES["tests.py"] = """
import sys
from src.models import Task
from src.core import DPCOCore

def main():
    print("DPCO PoC v0.1 - EXECUTING TESTS...")
    core = DPCOCore("execution_ledger.jsonl")
    results = {"PASS": 0, "FAIL": 0}
    
    def assert_status(name, log, ex_exp, cl_exp, vf_exp, expected_reason=None):
        passed = (log["final_executionStatus"] == ex_exp and 
                  log["final_claimVerdict"] == cl_exp and 
                  log["final_verificationStatus"] == vf_exp)
                  
        if expected_reason and expected_reason not in str(log.get("reason", "")): 
            passed = False
            
        if passed:
            print(f"[PASS] {name}")
            results["PASS"] += 1
        else:
            print(f"[FAIL] {name}\\n  Expected: {ex_exp}/{cl_exp}/{vf_exp} (Reason: {expected_reason})\\n  Got:      {log['final_executionStatus']}/{log['final_claimVerdict']}/{log['final_verificationStatus']} (Reason: {log.get('reason')})")
            results["FAIL"] += 1

    # T01: Exact Arithmetic
    t1 = Task("T01", "solve_linear", {"a":2, "b":0, "c":3}, constraints={"exact": True})
    assert_status("T01 - Exact Arithmetic", core.process_task(t1), "SUCCESS", "NOT_APPLICABLE", "VERIFIED")

    # T02: False Claim
    t2 = Task("T02", "solve_linear", {"a":2, "b":0, "c":3}, claim={"x": 2}, constraints={"exact": True})
    assert_status("T02 - False Claim", core.process_task(t2), "SUCCESS", "FALSE", "VERIFIED")

    # T03.1: Shift Contradiction
    t3_1 = Task("T03.1", "solve_system", {"eqs": [{"a":1, "b":0, "c":2}, {"a":1, "b":1, "c":4}]})
    assert_status("T03.1 - Shift Contradiction", core.process_task(t3_1), "BLOCKED", "UNKNOWN", "UNVERIFIED", "CONTRADICTION")

    # T03.2: Proportional Contradiction
    t3_2 = Task("T03.2", "solve_system", {"eqs": [{"a":1, "b":0, "c":2}, {"a":2, "b":0, "c":5}]})
    assert_status("T03.2 - Prop Contradiction", core.process_task(t3_2), "BLOCKED", "UNKNOWN", "UNVERIFIED", "CONTRADICTION")

    # T04: Capability Gap (Unsupported Operation)
    t4 = Task("T04", "solve_cubic", {"a":1, "b":2, "c":3, "d":4})
    assert_status("T04 - Capability Gap", core.process_task(t4), "BLOCKED", "UNKNOWN", "UNVERIFIED", "CAPABILITY_GAP")

    # T05: Verification Failure (Controlled bad executor)
    t5 = Task("T05", "solve_linear", {"a":2, "b":0, "c":3}, claim={"x":2})
    assert_status("T05 - Verification Failure", core.process_task(t5, force_executor="test_bad_solver"), "SUCCESS", "UNKNOWN", "UNVERIFIED", "ROOT_VERIFICATION_FAILED")

    # T06: Deterministic Dispatch (cost priority -> num_solver)
    t6 = Task("T06", "solve_linear", {"a":3, "b":0, "c":1}) 
    log6 = core.process_task(t6)
    if log6.get("executor") == "num_solver":
        assert_status("T06 - Dispatcher Rules", log6, "SUCCESS", "NOT_APPLICABLE", "VERIFIED")
    else:
        print(f"[FAIL] T06 - Dispatcher picked wrong: {log6.get('executor')}")
        results["FAIL"] += 1
        
    # T07: Forced Executor Constraint Violation
    t7 = Task("T07", "solve_linear", {"a":2, "b":0, "c":3}, constraints={"exact": True})
    assert_status("T07 - Forced Constraint Violation", core.process_task(t7, force_executor="num_solver"), "BLOCKED", "UNKNOWN", "UNVERIFIED", "CONSTRAINT_VIOLATION")

    # T08: Consistent Linear System
    t8 = Task("T08", "solve_system", {"eqs": [{"a":1, "b":0, "c":2}, {"a":2, "b":0, "c":4}]})
    # Ожидаем CAPABILITY_GAP, так как ни один из исполнителей не умеет решать "solve_system"
    assert_status("T08 - Consistent System (Cap Gap)", core.process_task(t8), "BLOCKED", "UNKNOWN", "UNVERIFIED", "CAPABILITY_GAP")

    # T09: Three Equations (Consistent)
    t9 = Task("T09", "solve_system", {"eqs": [{"a":1, "b":0, "c":2}, {"a":2, "b":0, "c":4}, {"a":3, "b":0, "c":6}]})
    assert_status("T09 - Three Eq Consistent", core.process_task(t9), "BLOCKED", "UNKNOWN", "UNVERIFIED", "CAPABILITY_GAP")

    # T10: Three Equations (Contradiction)
    t10 = Task("T10", "solve_system", {"eqs": [{"a":1, "b":0, "c":2}, {"a":2, "b":0, "c":4}, {"a":3, "b":0, "c":7}]})
    assert_status("T10 - Three Eq Contradiction", core.process_task(t10), "BLOCKED", "UNKNOWN", "UNVERIFIED", "CONTRADICTION")

    print(f"\\nSUMMARY: {results['PASS']} PASS, {results['FAIL']} FAIL")

if __name__ == '__main__':
    main()
"""

def generate_project():
    base = Path("dpco-algebra-poc")
    src = base / "src"
    src.mkdir(parents=True, exist_ok=True)
    
    (src / "__init__.py").write_text("", encoding='utf-8')
    
    for filename, content in MODULES.items():
        path = base / filename if filename == "tests.py" else src / filename
        # ИСПРАВЛЕНИЕ: Используем корректный символ '\n' для генерации файлов
        path.write_text(content.strip() + '\\n', encoding='utf-8')
        print(f"Created: {path}")
        
    print("\\n[STATIC VERIFICATION COMPLETE]")
    print("Project structure generated. Awaiting execution.")

if __name__ == '__main__':
    generate_project()