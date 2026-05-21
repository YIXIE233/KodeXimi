# Alpha Notice

This repository contains two tracks:

1. The legacy PowerShell alpha demo of a Codex-first, Kimi-worker file taskflow.
2. The new Python v0.1 runtime under `src/kodeximi`, which is being implemented as the first strict-session KodeXimi runtime.

It is useful for trying the workflow, studying the file protocol, and running low-risk local experiments. It is not production-ready and is not a security sandbox.

Important boundaries:

- Kimi CLI runs with the current user's permissions.
- `allowed_reads` and `allowed_writes` are workflow instructions, not OS-enforced access control.
- `VERIFY.md` is worker evidence, not final proof.
- Codex/human review must inspect actual artifacts, logs, Git status/diff, and untracked files.
- The taskflow does not automatically stage, commit, push, revert, or clean Git changes.
- Legacy batch/parallel execution is experimental and is not part of the Python v0.1 same-root runtime.

Python v0.1 deliberately starts with single-root, single-active-job execution. Multi-root parallelism is allowed only when each root owns its own `.kodeximi` state.

For real projects, start from a clean independent project Git root and baseline, keep tasks small, and commit only after explicit review and acceptance.




