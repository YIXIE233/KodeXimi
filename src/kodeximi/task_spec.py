from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import TaskSpecInvalid
from .jsonio import read_json


SUPPORTED_TASK_TYPES = {"code_edit", "inventory"}
SUPPORTED_VERIFICATION_TYPES = {"python_pytest", "python_script", "file_exists", "git_diff_stat"}


@dataclass(frozen=True)
class TaskSpec:
    raw: dict[str, Any]

    @property
    def task_type(self) -> str:
        return str(self.raw["task_type"])

    @property
    def goal(self) -> str:
        return str(self.raw["goal"])

    @property
    def write_policy(self) -> dict[str, Any]:
        return dict(self.raw.get("write_policy") or {})

    @property
    def verification(self) -> dict[str, Any]:
        return dict(self.raw.get("verification") or {"commands": []})

    @property
    def max_attempts(self) -> int:
        return int((self.raw.get("limits") or {}).get("max_attempts", 2))

    @property
    def attempt_timeout_seconds(self) -> int:
        return int((self.raw.get("limits") or {}).get("attempt_timeout_seconds", 900))


def load_task_spec(path: Path) -> TaskSpec:
    data = read_json(path)
    return validate_task_spec(data)


def validate_task_spec(data: Any) -> TaskSpec:
    if not isinstance(data, dict):
        raise TaskSpecInvalid("TaskSpec must be a JSON object.")
    if data.get("schema_version") != "0.1":
        raise TaskSpecInvalid("schema_version must be '0.1'.", field="schema_version")
    task_type = data.get("task_type")
    if task_type not in SUPPORTED_TASK_TYPES:
        raise TaskSpecInvalid(f"task_type must be one of {sorted(SUPPORTED_TASK_TYPES)}.", field="task_type")
    if not str(data.get("goal") or "").strip():
        raise TaskSpecInvalid("goal must be non-empty.", field="goal")
    wp = data.get("write_policy")
    if not isinstance(wp, dict):
        raise TaskSpecInvalid("write_policy must be an object.", field="write_policy")
    for key in ("modify_files", "create_files", "delete_files", "allow_globs", "deny_globs"):
        value = wp.get(key, [])
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise TaskSpecInvalid(f"write_policy.{key} must be a string list.", field=f"write_policy.{key}")
    if any(item in {"", ".", "./"} for item in wp.get("modify_files", [])):
        raise TaskSpecInvalid("modify_files cannot contain project root.", field="write_policy.modify_files")
    commands = (data.get("verification") or {}).get("commands", [])
    if not isinstance(commands, list):
        raise TaskSpecInvalid("verification.commands must be a list.", field="verification.commands")
    seen: set[str] = set()
    for index, command in enumerate(commands):
        if not isinstance(command, dict):
            raise TaskSpecInvalid("verification command must be an object.", field=f"verification.commands[{index}]")
        command_id = command.get("id")
        if not isinstance(command_id, str) or not command_id:
            raise TaskSpecInvalid("verification command id must be non-empty.", field=f"verification.commands[{index}].id")
        if command_id in seen:
            raise TaskSpecInvalid("verification command id must be unique.", field=f"verification.commands[{index}].id")
        seen.add(command_id)
        command_type = command.get("type")
        if command_type not in SUPPORTED_VERIFICATION_TYPES:
            raise TaskSpecInvalid(f"unsupported verification type: {command_type}", field=f"verification.commands[{index}].type")
        if command_type in {"python_pytest", "python_script"}:
            argv = command.get("argv")
            if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
                raise TaskSpecInvalid("argv must be a non-empty string list.", field=f"verification.commands[{index}].argv")
    return TaskSpec(data)

