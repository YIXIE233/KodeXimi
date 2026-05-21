from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from kodeximi.approval import decide_approval
from kodeximi.path_policy import PathPolicy
from kodeximi.task_spec import validate_task_spec


class ApprovalTests(unittest.TestCase):
    def policy(self, root: Path) -> PathPolicy:
        spec = validate_task_spec(
            {
                "schema_version": "0.1",
                "task_type": "code_edit",
                "goal": "edit allowed",
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
        return PathPolicy(root, spec)

    def test_approval_allows_result_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            attempt_dir = root / ".kodeximi" / "tasks" / "job" / "attempts" / "001"
            attempt_dir.mkdir(parents=True)
            result = decide_approval(
                root=root,
                policy=self.policy(root),
                attempt_dir=attempt_dir,
                payload={"id": "1", "sender": "WriteFile", "description": f"`{attempt_dir / 'RESULT.md'}`"},
            )
            self.assertEqual(result["response"], "approve")

    def test_approval_rejects_shell(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            attempt_dir = root / ".kodeximi" / "tasks" / "job" / "attempts" / "001"
            result = decide_approval(
                root=root,
                policy=self.policy(root),
                attempt_dir=attempt_dir,
                payload={"id": "1", "sender": "Shell", "description": "`pytest`"},
            )
            self.assertEqual(result["response"], "reject")

    def test_approval_rejects_out_of_policy_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            attempt_dir = root / ".kodeximi" / "tasks" / "job" / "attempts" / "001"
            result = decide_approval(
                root=root,
                policy=self.policy(root),
                attempt_dir=attempt_dir,
                payload={"id": "1", "sender": "WriteFile", "description": "`src/other.py`"},
            )
            self.assertEqual(result["response"], "reject")


if __name__ == "__main__":
    unittest.main()

