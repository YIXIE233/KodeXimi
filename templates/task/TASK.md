# TASK: {{TASK_NAME}}

## Goal
<!-- One-sentence description of what this task should accomplish. -->

## Current task directory
Current task directory: {{TASK_DIR}}

Evidence files are always task-local:

- `{{TASK_DIR}}\RESULT.md` must be written in the current task directory.
- `{{TASK_DIR}}\VERIFY.md` must be written in the current task directory when required.
- `{{TASK_DIR}}\CODEX_REVIEW.md` is Codex-owned and must not be created, edited, overwritten, or filled by Kimi.
- `{{TASK_DIR}}\logs\` must be task-local.

Even if commands are run from a project root or sandbox root, write evidence files back to the current task directory. Do not write `RESULT.md` or `VERIFY.md` to the project root, sandbox root, output root, or any other directory.

## Codex-owned files

Kimi must not create, edit, overwrite, or fill `CODEX_REVIEW.md`. If it already exists, leave it unchanged. Codex writes review files after reading RESULT.md, VERIFY.md, logs, and actual artifacts.

## Allowed reads
- TASK.md
- <!-- List files/directories Kimi may read. -->

## Allowed writes
- RESULT.md
- VERIFY.md
- logs/
- <!-- List execution artifacts Kimi may write. Use explicit paths. -->

## Git rules
- Do not run `git add`, `git commit`, `git push`, `git reset`, `git checkout`, `git switch`, `git clean`, or other history/index/destructive Git commands unless this TASK explicitly allows that exact command.
- Read-only Git commands such as `git status`, `git diff`, and `git log` are allowed only if this TASK explicitly asks for Git inspection.
- Codex/human review decides whether to stage, commit, revert, or clean files after reviewing RESULT.md, VERIFY.md, logs, and actual changes.

## Forbidden paths
- <!-- Explicitly disallowed paths (e.g., secrets, .env, parent project config). -->

## Verification required
- [ ] <!-- Check if VERIFY.md is required and what it should cover. -->

## Worker block
You are Kimi external worker.
Codex is controller/reviewer.
Follow TASK only.
Write RESULT.md in this current task directory.
Write VERIFY.md in this current task directory because this task involves <!-- commands / code / scripts / tests / generated outputs / data transformation -->.
Do not create or edit CODEX_REVIEW.md.
Do not run Git stage/commit/push/reset/checkout/clean commands.
Do not expand scope.
Keep stdout short; long logs go to task-local logs/.


