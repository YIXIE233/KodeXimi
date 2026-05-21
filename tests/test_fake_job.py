from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


def run_cli(cwd: Path, *args: str) -> dict:
    env = dict(os.environ)
    proc = subprocess.run(
        [sys.executable, "-m", "kodeximi", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"stdout was not JSON: {proc.stdout}\nstderr={proc.stderr}") from exc
    if proc.returncode != 0:
        raise AssertionError(f"command failed: {data}\nstderr={proc.stderr}")
    return data


class FakeJobTests(unittest.TestCase):
    def test_fake_job_reaches_needs_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            subprocess.run(["git", "init"], cwd=str(project), check=True, capture_output=True)
            (project / "src").mkdir()
            (project / "src" / "a.py").write_text("print('ok')\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=str(project), check=True)
            subprocess.run(["git", "-c", "user.email=test@example.com", "-c", "user.name=Test", "commit", "-m", "init"], cwd=str(project), check=True, capture_output=True)
            run_cli(project, "init")
            spec = {
                "schema_version": "0.1",
                "task_type": "code_edit",
                "goal": "fake job",
                "write_policy": {
                    "modify_files": ["src/a.py"],
                    "create_files": [],
                    "delete_files": [],
                    "allow_globs": [],
                    "deny_globs": [],
                },
                "verification": {"commands": [{"id": "file_exists", "type": "file_exists", "path": "src/a.py"}]},
            }
            spec_path = project / "task.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            # init writes .gitignore and the TaskSpec lives outside .kodeximi in this test,
            # so commit both before the clean-worktree preflight.
            subprocess.run(["git", "add", ".gitignore"], cwd=str(project), check=True)
            subprocess.run(["git", "add", "task.json"], cwd=str(project), check=True)
            subprocess.run(["git", "-c", "user.email=test@example.com", "-c", "user.name=Test", "commit", "-m", "task"], cwd=str(project), check=True, capture_output=True)
            result = run_cli(project, "job", "run", "--from-json", str(spec_path))
            self.assertEqual(result["state"], "needs_review")
            attempt_dir = Path(result["attempt_dir"])
            self.assertTrue((attempt_dir / "EVIDENCE_DIGEST.md").exists())
            self.assertTrue((attempt_dir / "VERIFY.md").exists())


if __name__ == "__main__":
    unittest.main()
