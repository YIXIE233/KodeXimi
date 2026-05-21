from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_cli(cwd: Path, *args: str) -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "kodeximi", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"stdout was not JSON: {proc.stdout}\nstderr={proc.stderr}") from exc
    if proc.returncode != 0:
        raise AssertionError(f"command failed: {data}\nstderr={proc.stderr}")
    return data


class SessionCliTests(unittest.TestCase):
    def test_init_and_strict_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            subprocess.run(["git", "init"], cwd=str(project), check=True, capture_output=True)
            data = run_cli(project, "init")
            self.assertTrue(data["ok"])
            data = run_cli(project, "session", "start")
            self.assertEqual(data["codex_direct_execution"], "deny_by_default")
            status = run_cli(project, "session", "status")
            self.assertTrue(status["active"])


if __name__ == "__main__":
    unittest.main()

