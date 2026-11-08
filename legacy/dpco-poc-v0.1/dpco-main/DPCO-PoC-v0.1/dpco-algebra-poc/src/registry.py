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
