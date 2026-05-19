# TASK: structured-input-discovery

## Goal
Read input/requirements.csv and produce a summary markdown file describing the requirements.

## Allowed reads
- TASK.md
- input/requirements.csv

## Allowed writes
- RESULT.md
- VERIFY.md
- requirements-summary.md
- logs/

## Forbidden paths
- ..
- ~/.env

## Verification required
- [x] requirements-summary.md must contain all rows from the CSV.

## Worker block
You are Kimi external worker.
Codex is controller/reviewer.
Follow TASK only.
Write RESULT.md.
Write VERIFY.md because this task involves data transformation and generated output.
Do not expand scope.
Keep stdout short; long logs go to logs/kimi.execute.*.log.


