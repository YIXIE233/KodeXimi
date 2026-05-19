---
name: kodeximi-router
description: Use when a task may need Codex controller/reviewer routing plus Kimi CLI external worker execution, especially non-trivial work with long context, many files, external materials, structured inputs, code/script/test/config changes, generated artifacts, verification, logs, batch work, or explicit Kimi delegation.
---

# KodeXimi Router

Use this skill to keep Codex as controller/reviewer and Kimi CLI as external worker for bounded execution segments.

## Activation

Use for non-trivial work involving long context, many files, unclear scope, external materials, structured inputs, code/script/test/config changes, generated artifacts, verification, logs, batch work, or explicit Kimi delegation.

Do not trigger this skill only because a task is small. Trigger it when execution should be bounded, delegated, evidenced, or reviewed through the taskflow.

## Five laws

1. Codex scopes and reviews; Kimi executes.
2. Codex writes task/review control artifacts; Kimi writes execution evidence and allowed artifacts.
3. Unbounded, external, multi-source, or structured inputs must be scoped before execution; use a lightweight inventory/source summary when scope is unclear.
4. Kimi execution leaves evidence: RESULT always; VERIFY when commands, code, scripts, tests, data transforms, generated outputs, or other consequential results matter.
5. Codex Review is mandatory after Kimi work.

## Workflow

```text
User intent -> TASK -> optional PLAN -> Worker execution -> ARTIFACTS -> RESULT -> optional VERIFY -> Codex Review -> next user feedback
```

TASK is required for Kimi execution.

PLAN is required for risky, multi-step, external-exploration, shared-module, cross-file, irreversible, or uncertain execution work.

## Routing rules

- If the project has `.kodeximi/enabled`, prefer the taskflow for execution/code/batch work unless there is a clear reason not to.
- If the project is not enabled, use normal Codex behavior unless the user explicitly asks to use this taskflow.
- For unclear external or multi-source inputs, first produce a scope/inventory/source summary instead of executing broad exploration.
- For code, scripts, tests, configs, generated outputs, or data transformations, delegate execution to Kimi when taskflow is enabled, then review evidence and actual changes.
- Codex direct-edit of execution-plane files is allowed only for explicit user-authorized direct-edit, Kimi unavailable with user-confirmed exception, or isolated workflow experiments. Small scope is not an exception.

## Task package minimum

A Kimi TASK should include:

- goal;
- current task directory;
- allowed reads;
- allowed writes;
- forbidden paths;
- verification requirement;
- stdout/log rule;
- worker block;
- exact evidence paths for RESULT.md and VERIFY.md.

## Review checklist

After Kimi work, Codex should inspect:

- `RESULT.md`;
- `VERIFY.md` when required;
- logs when relevant;
- generated artifacts;
- `status.json`;
- Git status/diff/staged diff/untracked files when inside a Git repo;
- scope, forbidden paths, secrets, and unintended side effects.

## Non-goals

This skill is not a plugin, hook, MCP, ACP, Wire integration, queue, dashboard, worktree manager, or permission sandbox.
It does not install anything and does not replace `cli/kodeximi.ps1`, `TASK.md`, or Codex review.


