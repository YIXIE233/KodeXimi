# Codex Agents Snippet

This repository is a generic Codex-first taskflow. Codex stays as controller/reviewer; Kimi CLI is used as an external worker for bounded execution segments.

## Recommended Codex Configuration

When using this taskflow, configure Codex with these norms:

1. **Controller Role**: Codex turns user intent into bounded task packages and reviews evidence before acceptance. Kimi performs execution-plane work only inside the TASK boundary.
2. **Delegation Rule**: Use the router skill (`skills/kodeximi-router`) for non-trivial work: long context, many files, external materials, structured inputs, code/script/test/config changes, generated artifacts, verification, logs, batch work, or explicit Kimi delegation.
3. **Five Laws**:
   - Codex scopes and reviews; Kimi executes.
   - Codex writes task/review control artifacts; Kimi writes execution evidence and allowed artifacts.
   - Unbounded, external, multi-source, or structured inputs must be scoped before execution; use a lightweight inventory/source summary when scope is unclear.
   - Kimi leaves evidence: `RESULT.md` always; `VERIFY.md` when commands, code, scripts, tests, data transforms, generated outputs, or other consequential results matter.
   - Codex Review is mandatory after Kimi work.
4. **Worker Block**: Every `TASK.md` should end with a worker block reminding Kimi of its role, scope boundary, evidence paths, and `RESULT.md` / `VERIFY.md` requirements.

## Quick Invocation

From a task directory, the CLI invokes Kimi roughly like:

```powershell
kimi --work-dir <taskDir> --agent-file <repo>/kimi/agents/codex-worker.yaml ...
```

See `kimi/agents/codex-worker.yaml` and `kimi/agents/codex-worker-system.md` for the worker agent configuration.

## Project-local taskflow mode

KodeXimi is opt-in by file:

- If `.kodeximi/enabled` exists at the project root, treat the taskflow as ON for execution/code/batch tasks.
- If `.kodeximi/enabled` does not exist, treat the taskflow as OFF and use normal Codex behavior.
- Do not infer ON from conversation memory alone.


