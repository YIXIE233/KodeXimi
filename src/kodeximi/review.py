from __future__ import annotations

from pathlib import Path

from .config import kx_dir, require_project
from .store import Store
from .timeutil import utc_now


VALID_DECISIONS = {"accepted", "rework", "failed", "blocked"}


def decide(root: Path, job_id: str, decision: str, reason_text: str | None = None, reason_file: Path | None = None) -> dict[str, object]:
    root = require_project(root)
    if decision not in VALID_DECISIONS:
        return {"ok": False, "error_code": "REVIEW_DECISION_INVALID", "message": f"decision must be one of {sorted(VALID_DECISIONS)}"}
    store = Store(kx_dir(root) / "kodeximi.sqlite")
    attempts = store.query_all("SELECT * FROM attempts WHERE job_id=? ORDER BY attempt_no DESC", (job_id,))
    if not attempts:
        return {"ok": False, "error_code": "JOB_NOT_FOUND", "message": f"unknown job: {job_id}"}
    attempt_no = int(attempts[0]["attempt_no"])
    if reason_file and reason_file.exists():
        reason_text = reason_file.read_text(encoding="utf-8")
    now = utc_now()
    store.execute(
        "INSERT INTO reviews(job_id,attempt_no,decision,reason_text,reason_file,created_at) VALUES(?,?,?,?,?,?)",
        (job_id, attempt_no, decision, reason_text or "", str(reason_file) if reason_file else None, now),
    )
    new_state = "rework_requested" if decision == "rework" else decision
    store.execute("UPDATE jobs SET state=?,updated_at=? WHERE job_id=?", (new_state, now, job_id))
    review_path = kx_dir(root) / "tasks" / job_id / "CODEX_REVIEW.md"
    review_path.write_text(f"# CODEX REVIEW\n\nDecision: {decision}\n\n{reason_text or ''}\n", encoding="utf-8")
    if decision == "rework":
        log_path = kx_dir(root) / "tasks" / job_id / "REWORK_LOG.md"
        old = log_path.read_text(encoding="utf-8") if log_path.exists() else "# REWORK LOG\n\n"
        log_path.write_text(old.rstrip() + f"\n\n## Attempt {attempt_no}\n\n{reason_text or ''}\n", encoding="utf-8")
    return {"ok": True, "job_id": job_id, "attempt_no": attempt_no, "decision": decision, "state": new_state}

