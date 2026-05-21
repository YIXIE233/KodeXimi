from __future__ import annotations

from pathlib import Path

from kodeximi.task_spec import TaskSpec
from kodeximi.transport.base import WorkerResult


class FakeTransport:
    name = "fake"

    def run(self, *, root: Path, attempt_dir: Path, spec: TaskSpec, job_id: str, attempt_no: int) -> WorkerResult:
        result_path = attempt_dir / "RESULT.md"
        if spec.task_type == "inventory":
            result_path.write_text(
                "# RESULT\n\n"
                "FakeTransport inventory completed.\n\n"
                "## Candidate files\n\n"
                "- No real inventory was performed by FakeTransport.\n\n"
                "## Open Issues\n\n"
                "- Replace FakeTransport with Kimi worker for real inventory.\n",
                encoding="utf-8",
            )
        else:
            result_path.write_text("# RESULT\n\nFakeTransport completed without business-file edits.\n", encoding="utf-8")
        return WorkerResult(status="finished", result_path=result_path, usage_payload={"transport": self.name})
