# BATCH: batch-independent-code

## Goal
Run two independent code-quality tasks in parallel: lint-style check and docstring audit on sample files.

## Tasks
- task-lint/
- task-docs/

## Constraints
- Max parallel: 2
- Overlapping writes: disallowed

## Worker block
You are Kimi external worker.
Codex is controller/reviewer.
Follow each TASK only.
Write RESULT.md for each task.
Write VERIFY.md when commands, code, scripts, tests, generated outputs, or data transforms are involved.
Do not expand scope.
Keep stdout short; long logs go to logs/kimi.execute.*.log.


