from __future__ import annotations

import time
import uuid
from pathlib import Path

from .config import kx_dir, require_project
from .evidence import write_diff_summary, write_digest, write_usage
from .errors import BoundaryViolation
from .jsonio import write_json
from .path_policy import PathPolicy
from .snapshot import acquire_root_lock, release_root_lock, require_clean_worktree, write_post_diff, write_pre_status
from .store import Store
from .task_spec import TaskSpec, validate_task_spec
from .timeutil import utc_now
from .transport.registry import get_transport
from .verification import run_verification, write_verify_files


def _store(root: Path) -> Store:
    return Store(kx_dir(root) / "kodeximi.sqlite")


def new_job_id() -> str:
    return "job-" + uuid.uuid4().hex[:8]


def audit_changed_files(root: Path, spec: TaskSpec, changed: list[dict[str, str]], attempt_dir: Path) -> list[dict[str, str]]:
    policy = PathPolicy(root, spec)
    violations: list[dict[str, str]] = []
    for item in changed:
        path = item.get("path", "")
        try:
            policy.check_write(path)
        except BoundaryViolation as exc:
            violations.append({"path": path, "status": item.get("status", ""), "reason": exc.message})
    if violations:
        write_json(attempt_dir / "boundary-violations.json", violations)
    return violations


def run_job(root: Path, spec: TaskSpec, *, transport: str = "fake") -> dict[str, object]:
    root = require_project(root)
    store = _store(root)
    store.init_schema()
    job_id = new_job_id()
    now = utc_now()
    store.execute(
        "INSERT INTO jobs(job_id,state,task_type,goal,created_at,updated_at) VALUES(?,?,?,?,?,?)",
        (job_id, "created", spec.task_type, spec.goal, now, now),
    )
    return run_attempt(root, spec, job_id, 1, transport=transport)


def run_attempt(root: Path, spec: TaskSpec, job_id: str, attempt_no: int, *, transport: str = "fake") -> dict[str, object]:
    store = _store(root)
    base = kx_dir(root)
    job_dir = base / "tasks" / job_id
    attempt_dir = job_dir / "attempts" / f"{attempt_no:03d}"
    attempt_dir.mkdir(parents=True, exist_ok=True)
    write_json(job_dir / "task-spec.normalized.json", spec.raw)
    started_at = utc_now()
    store.execute(
        "INSERT OR REPLACE INTO attempts(job_id,attempt_no,state,started_at) VALUES(?,?,?,?)",
        (job_id, attempt_no, "preflight", started_at),
    )
    lock = None
    start = time.monotonic()
    try:
        require_clean_worktree(root)
        lock = acquire_root_lock(base, job_id)
        write_pre_status(root, attempt_dir)
        store.execute("UPDATE attempts SET state=? WHERE job_id=? AND attempt_no=?", ("running_worker", job_id, attempt_no))
        worker = get_transport(transport)
        worker_result = worker.run(root=root, attempt_dir=attempt_dir, spec=spec, job_id=job_id, attempt_no=attempt_no)
        if worker_result.status != "finished":
            finished_at = utc_now()
            store.execute(
                "UPDATE attempts SET state=?,finished_at=?,error_code=?,error_message=? WHERE job_id=? AND attempt_no=?",
                ("worker_failed", finished_at, "WORKER_FAILED", worker_result.status, job_id, attempt_no),
            )
            store.execute(
                "UPDATE jobs SET state=?,updated_at=?,error_code=?,error_message=? WHERE job_id=?",
                ("failed", finished_at, "WORKER_FAILED", worker_result.status, job_id),
            )
            return {"ok": False, "error_code": "WORKER_FAILED", "message": worker_result.status, "job_id": job_id, "attempt_no": attempt_no}
        if not (attempt_dir / "RESULT.md").exists():
            finished_at = utc_now()
            store.execute(
                "UPDATE attempts SET state=?,finished_at=?,error_code=?,error_message=? WHERE job_id=? AND attempt_no=?",
                ("worker_failed", finished_at, "RESULT_MISSING", "RESULT.md missing", job_id, attempt_no),
            )
            store.execute(
                "UPDATE jobs SET state=?,updated_at=?,error_code=?,error_message=? WHERE job_id=?",
                ("failed", finished_at, "RESULT_MISSING", "RESULT.md missing", job_id),
            )
            return {"ok": False, "error_code": "RESULT_MISSING", "message": "RESULT.md missing", "job_id": job_id, "attempt_no": attempt_no}
        changed = write_post_diff(root, attempt_dir)
        violations = audit_changed_files(root, spec, changed, attempt_dir)
        if violations:
            finished_at = utc_now()
            store.execute(
                "UPDATE attempts SET state=?,finished_at=?,error_code=?,error_message=? WHERE job_id=? AND attempt_no=?",
                ("blocked", finished_at, "BOUNDARY_VIOLATION", f"{len(violations)} boundary violation(s)", job_id, attempt_no),
            )
            store.execute(
                "UPDATE jobs SET state=?,updated_at=?,error_code=?,error_message=? WHERE job_id=?",
                ("blocked", finished_at, "BOUNDARY_VIOLATION", f"{len(violations)} boundary violation(s)", job_id),
            )
            return {"ok": False, "error_code": "BOUNDARY_VIOLATION", "message": f"{len(violations)} boundary violation(s)", "job_id": job_id, "attempt_no": attempt_no, "attempt_dir": str(attempt_dir)}
        store.execute("UPDATE attempts SET state=? WHERE job_id=? AND attempt_no=?", ("verifying", job_id, attempt_no))
        verify = run_verification(root, attempt_dir, list(spec.verification.get("commands", [])))
        write_verify_files(attempt_dir, verify)
        write_diff_summary(attempt_dir)
        duration_ms = int((time.monotonic() - start) * 1000)
        usage = write_usage(attempt_dir, duration_ms=duration_ms)
        write_digest(attempt_dir, job_id=job_id, attempt_no=attempt_no, verify=verify, usage=usage)
        finished_at = utc_now()
        store.execute(
            "UPDATE attempts SET state=?,finished_at=?,duration_ms=?,verify_conclusion=?,usage_data_completeness=? WHERE job_id=? AND attempt_no=?",
            ("needs_review", finished_at, duration_ms, verify["conclusion"], usage["data_completeness"], job_id, attempt_no),
        )
        store.execute("UPDATE jobs SET state=?,updated_at=? WHERE job_id=?", ("needs_review", finished_at, job_id))
        return {"ok": True, "job_id": job_id, "attempt_no": attempt_no, "state": "needs_review", "attempt_dir": str(attempt_dir)}
    finally:
        release_root_lock(lock)


def _load_job_spec(root: Path, job_id: str) -> TaskSpec:
    spec_path = kx_dir(root) / "tasks" / job_id / "task-spec.normalized.json"
    if not spec_path.exists():
        from .errors import TaskSpecMissing

        raise TaskSpecMissing(f"missing normalized TaskSpec for job: {job_id}")
    import json

    return validate_task_spec(json.loads(spec_path.read_text(encoding="utf-8")))


def write_rework_brief(root: Path, job_id: str, next_attempt_no: int) -> Path:
    job_dir = kx_dir(root) / "tasks" / job_id
    previous_attempt_no = next_attempt_no - 1
    previous_dir = job_dir / "attempts" / f"{previous_attempt_no:03d}"
    review_path = job_dir / "CODEX_REVIEW.md"
    verify_path = previous_dir / "VERIFY.md"
    diff_path = previous_dir / "diff-summary.md"

    def read_if_exists(path: Path, limit: int = 8000) -> str:
        if not path.exists():
            return ""
        text = path.read_text(encoding="utf-8")
        if len(text) > limit:
            return text[: limit // 2] + "\n...[truncated]...\n" + text[-limit // 2 :]
        return text

    next_dir = job_dir / "attempts" / f"{next_attempt_no:03d}"
    next_dir.mkdir(parents=True, exist_ok=True)
    brief_path = next_dir / "REWORK_BRIEF.md"
    brief = [
        "# REWORK BRIEF",
        "",
        f"Job: `{job_id}`",
        f"Previous attempt: `{previous_attempt_no:03d}`",
        f"Next attempt: `{next_attempt_no:03d}`",
        "",
        "## Codex Review",
        "",
        read_if_exists(review_path) or "No CODEX_REVIEW.md found.",
        "",
        "## Previous Verification",
        "",
        read_if_exists(verify_path) or "No VERIFY.md found.",
        "",
        "## Previous Diff Summary",
        "",
        read_if_exists(diff_path) or "No diff-summary.md found.",
        "",
        "## Worker instruction",
        "",
        "- Fix only the issues identified above.",
        "- Do not expand scope.",
        "- Preserve correct work from the previous attempt when applicable.",
        "- Write a fresh RESULT.md for this attempt.",
    ]
    brief_path.write_text("\n".join(brief).rstrip() + "\n", encoding="utf-8")
    return brief_path


def rerun_job(root: Path, job_id: str, *, transport: str = "fake") -> dict[str, object]:
    root = require_project(root)
    store = _store(root)
    job = store.query_one("SELECT * FROM jobs WHERE job_id=?", (job_id,))
    if not job:
        return {"ok": False, "error_code": "JOB_NOT_FOUND", "message": f"unknown job: {job_id}"}
    if job["state"] != "rework_requested":
        return {"ok": False, "error_code": "JOB_NOT_REWORK_REQUESTED", "message": "job must be in rework_requested state before rerun"}
    spec = _load_job_spec(root, job_id)
    attempts = store.query_all("SELECT * FROM attempts WHERE job_id=? ORDER BY attempt_no", (job_id,))
    next_attempt_no = len(attempts) + 1
    if next_attempt_no > spec.max_attempts:
        now = utc_now()
        store.execute("UPDATE jobs SET state=?,updated_at=?,error_code=?,error_message=? WHERE job_id=?", ("blocked", now, "REWORK_LIMIT_REACHED", "max_attempts reached", job_id))
        return {"ok": False, "error_code": "REWORK_LIMIT_REACHED", "message": "max_attempts reached", "job_id": job_id}
    brief = write_rework_brief(root, job_id, next_attempt_no)
    result = run_attempt(root, spec, job_id, next_attempt_no, transport=transport)
    result["rework_brief"] = str(brief)
    return result


def cancel_job(root: Path, job_id: str) -> dict[str, object]:
    root = require_project(root)
    store = _store(root)
    job = store.query_one("SELECT * FROM jobs WHERE job_id=?", (job_id,))
    if not job:
        return {"ok": False, "error_code": "JOB_NOT_FOUND", "message": f"unknown job: {job_id}"}
    if job["state"] not in {"created", "preflight", "snapshotting", "running_worker", "verifying", "diffing"}:
        return {"ok": False, "error_code": "JOB_NOT_ACTIVE", "message": f"job is not active: {job['state']}", "job_id": job_id, "state": job["state"]}
    now = utc_now()
    store.execute("UPDATE jobs SET state=?,updated_at=? WHERE job_id=?", ("cancelled", now, job_id))
    store.execute("UPDATE attempts SET state=?,finished_at=? WHERE job_id=? AND state IN ('preflight','running_worker','verifying','diffing')", ("cancelled", now, job_id))
    return {"ok": True, "job_id": job_id, "state": "cancelled"}


def job_status(root: Path, job_id: str) -> dict[str, object]:
    root = require_project(root)
    store = _store(root)
    job = store.query_one("SELECT * FROM jobs WHERE job_id=?", (job_id,))
    if not job:
        return {"ok": False, "error_code": "JOB_NOT_FOUND", "message": f"unknown job: {job_id}"}
    attempts = store.query_all("SELECT * FROM attempts WHERE job_id=? ORDER BY attempt_no", (job_id,))
    return {"ok": True, "job": job, "attempts": attempts}
