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
