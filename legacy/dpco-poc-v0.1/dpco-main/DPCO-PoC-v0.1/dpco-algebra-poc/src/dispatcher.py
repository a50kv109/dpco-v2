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
