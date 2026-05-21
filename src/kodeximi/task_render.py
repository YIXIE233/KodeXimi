from __future__ import annotations

import json
from pathlib import Path

from .task_spec import TaskSpec


def render_worker_prompt(*, root: Path, attempt_dir: Path, spec: TaskSpec, job_id: str, attempt_no: int) -> str:
    result_path = attempt_dir / "RESULT.md"
    return (
        "You are running as a KodeXimi subordinate worker.\n\n"
        "Hard rules:\n"
        "- Do not decide whether the task is accepted.\n"
        "- Do not write VERIFY.md, verify.json, diff-summary.md, usage.json, or CODEX_REVIEW.md.\n"
        "- Do not run shell commands.\n"
        "- Only perform the bounded worker attempt described below.\n"
        "- Write your worker report to the exact RESULT.md path shown below.\n"
        "- If scope is insufficient, write Open Issues in RESULT.md instead of expanding scope.\n\n"
        f"Project root:\n{root}\n\n"
        f"Job: {job_id}\nAttempt: {attempt_no:03d}\n"
        f"RESULT.md path:\n{result_path}\n\n"
        "Normalized TaskSpec JSON:\n"
        "```json\n"
        f"{json.dumps(spec.raw, ensure_ascii=False, indent=2)}\n"
        "```\n"
    )

