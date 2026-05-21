---
name: kodeximi-strict-mode
description: Use when the user asks to initialize or use KodeXimi in the current Codex session, or when KodeXimi strict mode is active. Enforces the plugin-lite behavior protocol: Codex plans and reviews; Kimi performs execution-plane work through the KodeXimi CLI.
---

# KodeXimi Strict Mode

This is a plugin-lite behavior protocol, not a hard hook.

When the user says `初始化当前会话 KodeXimi strict mode` or equivalent, treat KodeXimi as active for the current conversation.

## Default rule

Codex must not directly perform execution-plane reads or writes after strict mode starts.

Execution-plane work includes:

- reading business source files to solve the task;
- editing business code;
- editing tests;
- reading task websites or business documents;
- generating business output files;
- running business implementation or verification commands.

Small tasks are not exceptions.

## Allowed Codex work

Codex may:

- understand the user request;
- ask clarification questions;
- create TaskSpec JSON;
- call `kodeximi`;
- read KodeXimi evidence;
- write `CODEX_REVIEW.md`;
- decide `accepted`, `rework`, `failed`, or `blocked`.

## Required flow

1. If the project is not initialized, run `kodeximi init` and `kodeximi doctor`.
2. Start strict session with `kodeximi session start --mode strict`.
3. For execution work, write a TaskSpec JSON file.
4. Validate with `kodeximi task validate --from-json <task.json>`.
5. Run `kodeximi job run --from-json <task.json> --wait`.
6. Read `kodeximi review package <job_id>`.
7. Review `EVIDENCE_DIGEST.md`, `RESULT.md`, `VERIFY.md`, `verify.json`, and `diff-summary.md`.
8. Record the decision with `kodeximi review decide`.

If Codex lacks enough project context, create an `inventory` task instead of reading project files directly.

## Explicit bypass

Only bypass KodeXimi when the user explicitly says this specific task may be handled directly by Codex.

