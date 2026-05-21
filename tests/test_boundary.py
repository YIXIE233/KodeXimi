from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from kodeximi.job import audit_changed_files
from kodeximi.snapshot import collect_changed_files, write_post_diff
from kodeximi.task_spec import validate_task_spec


def commit_all(project: Path, message: str) -> None:
    subprocess.run(["git", "add", "."], cwd=str(project), check=True)
    subprocess.run(
        ["git", "-c", "user.email=test@example.com", "-c", "user.name=Test", "commit", "-m", message],
        cwd=str(project),
        check=True,
        capture_output=True,
    )


class BoundaryTests(unittest.TestCase):
    def test_changed_files_include_untracked_and_boundary_audit_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            subprocess.run(["git", "init"], cwd=str(project), check=True, capture_output=True)
            (project / "src").mkdir()
            (project / "src" / "allowed.py").write_text("print('ok')\n", encoding="utf-8")
            commit_all(project, "init")

            (project / "src" / "allowed.py").write_text("print('changed')\n", encoding="utf-8")
            (project / "unexpected.py").write_text("print('bad')\n", encoding="utf-8")

            changed = collect_changed_files(project)
            self.assertIn({"status": "M", "path": "src/allowed.py"}, changed)
            self.assertIn({"status": "??", "path": "unexpected.py"}, changed)

            spec = validate_task_spec(
                {
                    "schema_version": "0.1",
                    "task_type": "code_edit",
                    "goal": "edit only allowed",
                    "write_policy": {
                        "modify_files": ["src/allowed.py"],
                        "create_files": [],
                        "delete_files": [],
                        "allow_globs": [],
                        "deny_globs": [],
                    },
                    "verification": {"commands": []},
                }
            )
            attempt_dir = project / ".kodeximi" / "tasks" / "job-test" / "attempts" / "001"
            attempt_dir.mkdir(parents=True)
            changed_from_diff = write_post_diff(project, attempt_dir)
            violations = audit_changed_files(project, spec, changed_from_diff, attempt_dir)
            self.assertEqual(len(violations), 1)
            self.assertEqual(violations[0]["path"], "unexpected.py")
            saved = json.loads((attempt_dir / "boundary-violations.json").read_text(encoding="utf-8"))
            self.assertEqual(saved[0]["path"], "unexpected.py")


if __name__ == "__main__":
    unittest.main()

