# Alpha Notice

This repository is an alpha demo of a Codex-first, Kimi-worker CLI taskflow.

It is useful for trying the workflow, studying the file protocol, and running low-risk local experiments. It is not production-ready and is not a security sandbox.

Important boundaries:

- Kimi CLI runs with the current user's permissions.
- `allowed_reads` and `allowed_writes` are workflow instructions, not OS-enforced access control.
- `VERIFY.md` is worker evidence, not final proof.
- Codex/human review must inspect actual artifacts, logs, Git status/diff, and untracked files.
- The taskflow does not automatically stage, commit, push, revert, or clean Git changes.
- Batch/parallel execution is experimental.

For real projects, start from a clean independent project Git root and baseline, keep tasks small, and commit only after explicit review and acceptance.





