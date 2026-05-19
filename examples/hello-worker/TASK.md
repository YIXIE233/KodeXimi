# TASK: hello-worker

## Current task directory
`examples/hello-worker/`

Evidence files are task-local:
- `RESULT.md`
- `VERIFY.md`
- `logs/`

## Goal
Verify the KodeXimi can execute a minimal task and produce task-local RESULT.md and VERIFY.md.

## Allowed reads
- TASK.md

## Allowed writes
- RESULT.md
- VERIFY.md
- logs/

## Forbidden paths
- Any write outside the current task directory.
- Real websites or network calls.
- Databases, notifications, secrets, .env, credentials.

## Verification required
- [x] RESULT.md must be present and non-empty.
- [x] VERIFY.md must include Shell, CWD, exact command actually run or explain if no command was run, exit code, stdout/stderr summary, and verdict.

## Worker block
You are Kimi external worker.
Codex is controller/reviewer.
Follow TASK only.
Write RESULT.md in this task directory.
Write VERIFY.md in this task directory.
Do not expand scope.
Keep stdout short; long logs go to task-local logs/.


