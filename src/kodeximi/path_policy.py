from __future__ import annotations

import fnmatch
from pathlib import Path

from .errors import BoundaryViolation
from .task_spec import TaskSpec


HARD_DENY_GLOBS = [
    ".git/**",
    ".kodeximi/**",
    ".env",
    ".env.*",
    "**/*.key",
    "**/*.pem",
    "**/secrets/**",
]


def rel_path(root: Path, path: str | Path) -> str:
    candidate = (root / Path(path)).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    try:
        relative = candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise BoundaryViolation(f"path escapes project root: {path}") from exc
    return relative.as_posix()


def _match_any(path: str, patterns: list[str]) -> bool:
    normalized = path.replace("\\", "/")
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in patterns)


class PathPolicy:
    def __init__(self, root: Path, spec: TaskSpec):
        self.root = root.resolve()
        wp = spec.write_policy
        self.modify_files = {rel_path(self.root, item) for item in wp.get("modify_files", [])}
        self.create_files = {rel_path(self.root, item) for item in wp.get("create_files", [])}
        self.delete_files = {rel_path(self.root, item) for item in wp.get("delete_files", [])}
        self.allow_globs = list(wp.get("allow_globs", []))
        self.deny_globs = HARD_DENY_GLOBS + list(wp.get("deny_globs", []))

    def check_write(self, path: str | Path) -> str:
        relative = rel_path(self.root, path)
        if _match_any(relative, self.deny_globs):
            raise BoundaryViolation(f"write denied by hard deny policy: {relative}")
        if relative in self.modify_files or relative in self.create_files or _match_any(relative, self.allow_globs):
            return relative
        raise BoundaryViolation(f"write outside write_policy: {relative}")

