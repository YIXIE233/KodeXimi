# KodeXimi v0.1 Architecture

KodeXimi v0.1 is a Codex-first local delegation runtime.

The v0.1 shape is deliberately narrow:

- Codex controls planning and review.
- Kimi CLI performs one bounded worker attempt.
- KodeXimi records state, enforces write boundaries, runs runtime verification, and packages evidence.
- Codex decides `accepted`, `rework`, `failed`, or `blocked`.

This is not a step-level model router, not a multi-agent OS, and not a full security sandbox.

## v0.1 scope

Included:

- Python CLI runtime.
- Project `init` and `doctor`.
- Strict session mode.
- Codex plugin-lite protocol.
- TaskSpec v0.1 validation.
- Single root, single active job.
- Snapshot-backed direct project mode.
- Runtime-generated `VERIFY.md` and `verify.json`.
- Evidence digest, diff summary, patch, and observed usage.
- Review decision recording.

Excluded:

- Same-root batch parallelism.
- Full materialized workspace.
- Codex hard hooks.
- Kimi hooks.
- Kimi Shell access.
- Dashboard and HTML reports.

## Strict session rule

After the user initializes KodeXimi strict mode in a Codex conversation, Codex must not directly perform execution-plane reads or writes, regardless of task size.

Execution-plane work includes reading business source files, editing code, editing tests, reading task websites/documents, generating business outputs, and running business verification.

Codex may still perform control-plane work: understand the user request, ask clarification questions, create TaskSpec JSON, call the KodeXimi CLI, read KodeXimi evidence, write `CODEX_REVIEW.md`, and decide the review outcome.

Smallness is not an exception. Explicit user override is the only exception.

## Runtime flow

```text
User request
  -> Codex TaskSpec
  -> KodeXimi preflight + snapshot
  -> Kimi worker attempt
  -> KodeXimi runtime verification
  -> KodeXimi evidence package
  -> Codex review
  -> accepted / rework / failed / blocked
```

## Parallel policy

v0.1 forbids same-root parallel jobs. A project root has a `.kodeximi/run.lock`; only one active job may run in that root.

Multi-root parallelism is allowed when the user explicitly requests it. Each root must have an independent `.kodeximi` state directory, evidence package, and root lock.

