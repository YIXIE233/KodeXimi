from __future__ import annotations


class KodeXimiError(Exception):
    """Base error with a stable machine-readable code."""

    code = "KODEXIMI_ERROR"

    def __init__(self, message: str, *, field: str | None = None):
        super().__init__(message)
        self.message = message
        self.field = field

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {"ok": False, "error_code": self.code, "message": self.message}
        if self.field:
            data["field"] = self.field
        return data


class TaskSpecInvalid(KodeXimiError):
    code = "TASKSPEC_INVALID"


class TaskSpecMissing(KodeXimiError):
    code = "TASKSPEC_MISSING"


class ProjectNotInitialized(KodeXimiError):
    code = "PROJECT_NOT_INITIALIZED"


class DirtyWorktree(KodeXimiError):
    code = "DIRTY_WORKTREE"


class RootLocked(KodeXimiError):
    code = "ROOT_LOCKED"


class VerificationUnsupported(KodeXimiError):
    code = "VERIFICATION_COMMAND_UNSUPPORTED"


class VerificationTimeout(KodeXimiError):
    code = "VERIFICATION_TIMEOUT"


class BoundaryViolation(KodeXimiError):
    code = "BOUNDARY_VIOLATION"
