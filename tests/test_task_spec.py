from __future__ import annotations

import unittest

from kodeximi.errors import TaskSpecInvalid
from kodeximi.task_spec import validate_task_spec


class TaskSpecTests(unittest.TestCase):
    def base_spec(self):
        return {
            "schema_version": "0.1",
            "task_type": "code_edit",
            "goal": "edit one file",
            "write_policy": {
                "modify_files": ["src/a.py"],
                "create_files": [],
                "delete_files": [],
                "allow_globs": [],
                "deny_globs": [],
            },
            "verification": {"commands": [{"id": "exists", "type": "file_exists", "path": "src/a.py"}]},
        }

    def test_valid_spec(self):
        spec = validate_task_spec(self.base_spec())
        self.assertEqual(spec.task_type, "code_edit")

    def test_rejects_root_modify(self):
        data = self.base_spec()
        data["write_policy"]["modify_files"] = ["."]
        with self.assertRaises(TaskSpecInvalid):
            validate_task_spec(data)

    def test_rejects_shell_string_command(self):
        data = self.base_spec()
        data["verification"]["commands"] = [{"id": "bad", "type": "python_pytest", "command": "python -m pytest"}]
        with self.assertRaises(TaskSpecInvalid):
            validate_task_spec(data)

    def test_inventory_rejects_business_writes(self):
        data = self.base_spec()
        data["task_type"] = "inventory"
        data["write_policy"]["modify_files"] = ["src/a.py"]
        with self.assertRaises(TaskSpecInvalid):
            validate_task_spec(data)

    def test_inventory_allows_no_business_writes(self):
        data = self.base_spec()
        data["task_type"] = "inventory"
        data["write_policy"]["modify_files"] = []
        data["verification"]["commands"] = []
        spec = validate_task_spec(data)
        self.assertEqual(spec.task_type, "inventory")


if __name__ == "__main__":
    unittest.main()
