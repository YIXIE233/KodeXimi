from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from kodeximi.task_spec import TaskSpec


@dataclass(frozen=True)
class WorkerResult:
    status: str
    result_path: Path | None = None
    usage_payload: dict[str, object] = field(default_factory=dict)


class Transport(Protocol):
    name: str

    def run(self, *, root: Path, attempt_dir: Path, spec: TaskSpec, job_id: str, attempt_no: int) -> WorkerResult:
        ...

