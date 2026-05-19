# Security Model and Limitations

## Executive summary

This alpha demo is not a security sandbox.

It provides a file-based workflow protocol for making delegated work visible and reviewable. It does not enforce operating-system permissions, filesystem isolation, network isolation, or command allowlists.

## What is advisory only

The following fields are conventions for Codex/Kimi coordination and review:

- `allowed_reads`
- `allowed_writes`
- `forbidden_paths`
- `verify_required`
- `conflict_policy`

They are not enforced by the OS. Kimi CLI runs with the current user's permissions.

## What the taskflow actually does

- Creates task and batch folders.
- Invokes Kimi with a task-local working directory and a custom agent file.
- Redirects stdout/stderr to task-local logs.
- Checks whether task-local `RESULT.md` and `VERIFY.md` exist.
- Updates `status.json`.
- Reports likely misplaced `RESULT.md` / `VERIFY.md` files.
- Provides `review-check` to summarize task evidence and Git review state without staging or committing files.

## What it does not do

- It does not sandbox Kimi.
- It does not prevent Kimi from reading or writing files at the OS level.
- It does not block web access at the network level.
- It does not enforce `allowed_writes` with ACLs.
- It does not replace Codex review, human review, tests, or CI.
- It does not automatically stage, commit, push, revert, or clean Git changes.

## Git boundary

Kimi workers should not run `git add`, `git commit`, `git push`, `git reset`, `git checkout`, `git switch`, or `git clean` by default. Reviewers should use Git status/diff/untracked file listing to inspect changes, then explicitly decide whether to accept, revert, stage, or commit.

## `--yolo` warning

The alpha wrapper uses automated Kimi invocation for demo convenience. Treat this as risky on real projects. Do not use this taskflow on production or sensitive repositories unless you add external safeguards and review every change.

## Verification warning

`VERIFY.md` is worker-supplied evidence, not final proof. Codex or a human reviewer should independently inspect changed files and re-run important commands before accepting work.




