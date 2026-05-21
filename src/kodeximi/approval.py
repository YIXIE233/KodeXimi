from __future__ import annotations

import re
from pathlib import Path

from .path_policy import PathPolicy, rel_path


FILE_TOOL_NAMES = {"WriteFile", "StrReplaceFile", "ReadFile", "Glob", "Grep"}


def extract_paths(text: str) -> list[str]:
    candidates: list[str] = []
    for match in re.finditer(r"`([^`]+)`", text):
        value = match.group(1).strip()
        if value:
            candidates.append(value)
    for match in re.finditer(r"([A-Za-z]:[\\/][^\s`]+)", text):
        candidates.append(match.group(1).strip())
    return candidates


def decide_approval(*, root: Path, policy: PathPolicy, attempt_dir: Path, payload: dict[str, object]) -> dict[str, str]:
    sender = str(payload.get("sender") or "")
    description = str(payload.get("description") or "")
    action = str(payload.get("action") or "")
    request_id = str(payload.get("id") or "")
    lower = f"{sender} {action} {description}".lower()
    if "shell" in lower or sender == "Shell":
        return {"request_id": request_id, "response": "reject", "feedback": "KodeXimi v0.1 does not allow worker shell execution."}

    if sender in FILE_TOOL_NAMES or "file" in lower:
        paths = extract_paths(description + " " + action)
        if not paths:
            return {"request_id": request_id, "response": "reject", "feedback": "KodeXimi could not determine the requested file path."}
        result_path = (attempt_dir / "RESULT.md").resolve()
        for item in paths:
            try:
                candidate = (root / item).resolve() if not Path(item).is_absolute() else Path(item).resolve()
                if candidate == result_path:
                    return {"request_id": request_id, "response": "approve"}
                policy.check_write(item)
                return {"request_id": request_id, "response": "approve"}
            except Exception:
                continue
        return {"request_id": request_id, "response": "reject", "feedback": "Requested path is outside KodeXimi write_policy."}

    return {"request_id": request_id, "response": "reject", "feedback": f"KodeXimi v0.1 rejects unsupported approval sender: {sender}"}

