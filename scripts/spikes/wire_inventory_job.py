from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"


def run(root: Path, *args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "kodeximi", *args],
        cwd=str(root),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )


def main() -> int:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC)
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        subprocess.run(["git", "init"], cwd=str(project), check=True, capture_output=True)
        (project / "README.md").write_text("# KodeXimi wire inventory smoke\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=str(project), check=True)
        subprocess.run(
            ["git", "-c", "user.email=test@example.com", "-c", "user.name=Test", "commit", "-m", "init"],
            cwd=str(project),
            check=True,
            capture_output=True,
        )
        init = run(project, "init", env=env)
        if init.returncode != 0:
            print(init.stdout)
            print(init.stderr, file=sys.stderr)
            return init.returncode
        subprocess.run(["git", "add", ".gitignore"], cwd=str(project), check=True)
        subprocess.run(
            ["git", "-c", "user.email=test@example.com", "-c", "user.name=Test", "commit", "-m", "kodeximi-init"],
            cwd=str(project),
            check=True,
            capture_output=True,
        )
        spec = {
            "schema_version": "0.1",
            "task_type": "inventory",
            "goal": "Write RESULT.md listing README.md as a candidate file. Do not edit business files.",
            "write_policy": {"modify_files": [], "create_files": [], "delete_files": [], "allow_globs": [], "deny_globs": []},
            "verification": {"commands": []},
            "limits": {"attempt_timeout_seconds": 120, "max_attempts": 1},
        }
        spec_path = project / "task.json"
        spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
        subprocess.run(["git", "add", "task.json"], cwd=str(project), check=True)
        subprocess.run(
            ["git", "-c", "user.email=test@example.com", "-c", "user.name=Test", "commit", "-m", "task"],
            cwd=str(project),
            check=True,
            capture_output=True,
        )
        job = run(project, "job", "run", "--from-json", str(spec_path), "--transport", "kimi-wire", "--wait", env=env)
        print(job.stdout)
        if job.stderr:
            print(job.stderr, file=sys.stderr)
        return job.returncode


if __name__ == "__main__":
    raise SystemExit(main())

