# TASK: single-code-change

## Goal
Make a small, safe change to src/sample.py (e.g., add a docstring or a constant) and verify the file is still syntactically valid.

## Allowed reads
- TASK.md
- src/sample.py

## Allowed writes
- src/sample.py
- RESULT.md
- VERIFY.md
- logs/

## Forbidden paths
- ..
- ~/.env

## Verification required
- [x] Python syntax must be valid after change.

## Worker block
You are Kimi external worker.
Codex is controller/reviewer.
Follow TASK only.
Write RESULT.md.
Write VERIFY.md because this task involves code changes and command verification.
Do not expand scope.
Keep stdout short; long logs go to logs/kimi.execute.*.log.


