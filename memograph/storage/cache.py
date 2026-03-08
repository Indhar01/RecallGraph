import json
from pathlib import Path
from typing import Any


class JsonCache:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> dict[Any, Any]:
        if not self.path.exists():
            return {}
        try:
            data: dict[Any, Any] = json.loads(self.path.read_text(encoding="utf-8"))
            return data
        except json.JSONDecodeError:
            return {}

    def save(self, payload: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload), encoding="utf-8")
