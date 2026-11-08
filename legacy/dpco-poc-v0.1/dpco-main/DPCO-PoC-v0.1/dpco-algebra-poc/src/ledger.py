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
