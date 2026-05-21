from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_usage(attempt_dir: Path, *, duration_ms: int, completeness: str = "missing", payload: dict[str, Any] | None = None) -> dict[str, Any]:
    usage = {
        "schema_version": "0.1",
        "data_completeness": completeness,
        "is_billing_grade": False,
        "source": "none" if completeness == "missing" else "wire_status_update",
        "input_tokens": None,
        "output_tokens": None,
        "total_tokens": None,
        "raw_status_updates_count": 0,
        "duration_ms": duration_ms,
        "payload": payload or {},
    }
    (attempt_dir / "usage.json").write_text(json.dumps(usage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return usage


def write_diff_summary(attempt_dir: Path) -> None:
    changed_path = attempt_dir / "changed-files.json"
    changed = json.loads(changed_path.read_text(encoding="utf-8")) if changed_path.exists() else []
    lines = ["# Diff Summary", "", f"Changed files: {len(changed)}", ""]
    for item in changed:
        lines.append(f"- `{item.get('status')}` {item.get('path')}")
    if not changed:
        lines.append("- No tracked file changes detected.")
    lines.append("")
    lines.append("Full patch: `patch.diff`")
    (attempt_dir / "diff-summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_digest(attempt_dir: Path, *, job_id: str, attempt_no: int, verify: dict[str, Any], usage: dict[str, Any]) -> None:
    changed_path = attempt_dir / "changed-files.json"
    changed = json.loads(changed_path.read_text(encoding="utf-8")) if changed_path.exists() else []
    result_exists = (attempt_dir / "RESULT.md").exists()
    lines = [
        "# Evidence Digest",
        "",
        f"- Job: `{job_id}`",
        f"- Attempt: `{attempt_no}`",
        f"- RESULT.md exists: `{result_exists}`",
        f"- Verification conclusion: `{verify['conclusion']}`",
        f"- Changed files: `{len(changed)}`",
        f"- Usage data completeness: `{usage['data_completeness']}`",
        "",
        "## Changed files",
        "",
    ]
    if changed:
        for item in changed[:50]:
            lines.append(f"- `{item.get('status')}` {item.get('path')}")
        if len(changed) > 50:
            lines.append(f"- ... truncated {len(changed) - 50} more files")
    else:
        lines.append("- No tracked file changes detected.")
    lines.extend(["", "## Review focus", "", "- Check RESULT.md against the requested goal.", "- Check VERIFY.md and verify.json.", "- Check diff-summary.md and patch.diff before accepting."])
    (attempt_dir / "EVIDENCE_DIGEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

