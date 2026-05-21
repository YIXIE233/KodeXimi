from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .jsonio import write_json
from .store import Store


KODEXIMI_DIR = ".kodeximi"


DEFAULT_CONFIG = """# KodeXimi v0.1 project config
enabled = true
default_session_mode = "strict"
max_attempts_default = 2
attempt_timeout_seconds_default = 900
verification_timeout_seconds_default = 120
parallel_policy = "multi_root_only"
"""


WORKER_AGENT = """version: 1
agent:
  name: kodeximi-worker
  system_prompt_path: ./kodeximi-worker-system.md
  # v0.1 uses explicit tool allowlisting. Shell and web tools are intentionally absent.
  tools:
    - "kimi_cli.tools.file:ReadFile"
    - "kimi_cli.tools.file:Glob"
    - "kimi_cli.tools.file:Grep"
    - "kimi_cli.tools.file:WriteFile"
    - "kimi_cli.tools.file:StrReplaceFile"
"""


WORKER_SYSTEM = """# KodeXimi Worker

You are the subordinate execution worker for KodeXimi.

Rules:
- Do not decide that the task is accepted.
- Do not edit KodeXimi control-plane files.
- Only modify files allowed by the rendered TASK.
- Write RESULT.md in the current attempt directory.
- Do not write VERIFY.md; runtime verification is produced by KodeXimi.
- If scope is insufficient, write Open Issues in RESULT.md instead of expanding scope.
"""


def project_dir(cwd: Path) -> Path:
    return cwd.resolve()


def kx_dir(cwd: Path) -> Path:
    return project_dir(cwd) / KODEXIMI_DIR


def require_project(cwd: Path) -> Path:
    root = project_dir(cwd)
    if not (root / KODEXIMI_DIR / "config.toml").exists():
        from .errors import ProjectNotInitialized

        raise ProjectNotInitialized("Run `kodeximi init` in this project first.")
    return root


def init_project(cwd: Path) -> dict[str, object]:
    root = project_dir(cwd)
    base = kx_dir(root)
    (base / "tasks").mkdir(parents=True, exist_ok=True)
    (base / "logs").mkdir(parents=True, exist_ok=True)
    (base / "sessions").mkdir(parents=True, exist_ok=True)
    (base / "skills").mkdir(parents=True, exist_ok=True)
    (base / "agents").mkdir(parents=True, exist_ok=True)
    config_path = base / "config.toml"
    if not config_path.exists():
        config_path.write_text(DEFAULT_CONFIG, encoding="utf-8")
    (base / "agents" / "kodeximi-worker.yaml").write_text(WORKER_AGENT, encoding="utf-8")
    (base / "agents" / "kodeximi-worker-system.md").write_text(WORKER_SYSTEM, encoding="utf-8")
    gitignore = root / ".gitignore"
    marker = ".kodeximi/"
    if gitignore.exists():
        text = gitignore.read_text(encoding="utf-8")
        if marker not in text.splitlines():
            gitignore.write_text(text.rstrip() + "\n" + marker + "\n", encoding="utf-8")
    else:
        gitignore.write_text(marker + "\n", encoding="utf-8")
    Store(base / "kodeximi.sqlite").init_schema()
    return {"ok": True, "project_root": str(root), "kodeximi_dir": str(base)}


def doctor(cwd: Path, *, wire_smoke: bool = False) -> dict[str, object]:
    root = project_dir(cwd)
    base = kx_dir(root)
    checks: list[dict[str, object]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    add("project_initialized", (base / "config.toml").exists(), str(base / "config.toml"))
    kimi = shutil.which("kimi")
    add("kimi_cli", kimi is not None, kimi or "not found")
    pwsh = shutil.which("pwsh")
    add("pwsh", pwsh is not None, pwsh or "not found")
    git = shutil.which("git")
    add("git", git is not None, git or "not found")
    if git:
        proc = subprocess.run([git, "-C", str(root), "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
        add("git_repo", proc.returncode == 0 and proc.stdout.strip() == "true", proc.stderr.strip())
    add("worker_agent", (base / "agents" / "kodeximi-worker.yaml").exists(), str(base / "agents" / "kodeximi-worker.yaml"))
    add("sqlite", (base / "kodeximi.sqlite").exists(), str(base / "kodeximi.sqlite"))
    result: dict[str, object] = {"ok": all(bool(item["ok"]) for item in checks if item["name"] != "kimi_cli"), "checks": checks}
    if wire_smoke and kimi:
        from .wire_smoke import smoke_system_kimi

        smoke = smoke_system_kimi(root, kimi)
        result["wire_smoke"] = smoke
        result["ok"] = bool(result["ok"]) and bool(smoke.get("ok"))
    return result
