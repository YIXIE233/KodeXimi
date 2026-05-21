from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from kodeximi.task_spec import validate_task_spec
from kodeximi.transport.registry import get_transport


class TransportTests(unittest.TestCase):
    def test_fake_transport_writes_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            attempt_dir = Path(tmp)
            spec = validate_task_spec(
                {
                    "schema_version": "0.1",
                    "task_type": "code_edit",
                    "goal": "fake",
                    "write_policy": {
                        "modify_files": ["a.py"],
                        "create_files": [],
                        "delete_files": [],
                        "allow_globs": [],
                        "deny_globs": [],
                    },
                    "verification": {"commands": []},
                }
            )
            result = get_transport("fake").run(root=attempt_dir, attempt_dir=attempt_dir, spec=spec, job_id="job-test", attempt_no=1)
            self.assertEqual(result.status, "finished")
            self.assertEqual(result.usage_payload["transport"], "fake")
            self.assertTrue((attempt_dir / "RESULT.md").exists())

    def test_kimi_wire_transport_registered(self):
        self.assertEqual(get_transport("kimi-wire").name, "kimi-wire")


if __name__ == "__main__":
    unittest.main()
