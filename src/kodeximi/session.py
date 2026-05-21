from __future__ import annotations

from pathlib import Path

from .config import kx_dir, require_project
from .jsonio import read_json, write_json
from .timeutil import utc_now


def session_path(cwd: Path) -> Path:
    return kx_dir(cwd) / "sessions" / "current.json"


def start_session(cwd: Path, *, mode: str = "strict", scope: str = "current_thread") -> dict[str, object]:
    require_project(cwd)
    data = {
        "ok": True,
        "mode": f"kodeximi_{mode}",
        "scope": scope,
        "codex_direct_execution": "deny_by_default" if mode == "strict" else "discouraged",
        "parallel_policy": "multi_root_only",
        "started_at": utc_now(),
    }
    write_json(session_path(cwd), data)
    return data


def status_session(cwd: Path) -> dict[str, object]:
    require_project(cwd)
    path = session_path(cwd)
    if not path.exists():
        return {"ok": True, "active": False}
    data = read_json(path)
    data["active"] = True
    return data


def stop_session(cwd: Path) -> dict[str, object]:
    require_project(cwd)
    path = session_path(cwd)
    if path.exists():
        path.unlink()
    return {"ok": True, "active": False}

