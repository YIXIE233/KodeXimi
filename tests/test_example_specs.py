from __future__ import annotations

import unittest
from pathlib import Path

from kodeximi.task_spec import load_task_spec


ROOT = Path(__file__).resolve().parents[1]


class ExampleSpecTests(unittest.TestCase):
    def test_v01_fake_code_edit_task_is_valid(self):
        spec = load_task_spec(ROOT / "examples" / "v0.1-fake-code-edit" / "task.json")
        self.assertEqual(spec.task_type, "code_edit")


if __name__ == "__main__":
    unittest.main()

