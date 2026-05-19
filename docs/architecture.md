# Architecture

## Overview

The KodeXimi is a lightweight coordination layer between:
- **Codex** (controller/reviewer, user-facing)
- **Kimi CLI** (external worker, execution plane)

## Components

### 1. Control Plane (Codex)
- Writes `TASK.md`, `PLAN.md`, review artifacts
- Delegates execution to Kimi via the CLI
- Reviews `RESULT.md` and `VERIFY.md` before accepting work

### 2. Execution Plane (Kimi)
- Reads `TASK.md` in a bounded work directory
- Produces execution artifacts, `RESULT.md`, and `VERIFY.md`
- Respects `allowed_reads`, `allowed_writes`, forbidden paths, and URL limits

### 3. CLI (`cli/kodeximi.ps1`)
- Entry point for human users and scripts
- Manages project workspaces, tasks, and batches
- Invokes Kimi with correct `--work-dir` and `--agent-file`
- Tracks status in `status.json`
- Provides `review-check` for evidence and Git review summaries

### 4. Templates (`templates/`)
- Standardized `TASK.md`, `RESULT.md`, `VERIFY.md`, `CODEX_REVIEW.md`
- Batch manifests and status tracking
- Ensure consistency across projects

### 5. Agents (`kimi/agents/`)
- `codex-worker.yaml`: Kimi agent manifest
- `codex-worker-system.md`: System prompt for Kimi workers

## Data Flow

```
User -> Codex -> TASK.md -> CLI -> Kimi -> RESULT.md/VERIFY.md -> Codex Review -> User
```

## Design Principles

- Minimal moving parts
- No external dependencies
- No persistent server or queue
- Plain text and JSON for all artifacts
- PowerShell 7+, UTF-8


## Project-local ON/OFF mode

The alpha demo has only two project modes:

- `OFF`: `.kodeximi/enabled` does not exist. Use normal Codex behavior.
- `ON`: `.kodeximi/enabled` exists. Codex may use the taskflow for execution/code/batch tasks.

This avoids relying on session memory. If context is compressed or a new window is opened, Codex can check the file.


## Enforcement boundary

The controller/worker split is a workflow convention, not a security boundary. Codex writes tasks and reviews evidence; Kimi executes bounded work. The taskflow makes work auditable but does not prevent an unrestricted CLI from acting outside the requested scope. Real safeguards require OS/container permissions, additional guards, or future hook/plugin enforcement.


## Review ownership

`RESULT.md` and `VERIFY.md` are worker evidence files. `CODEX_REVIEW.md` is controller-owned. Kimi must not create, fill, or overwrite review files. Codex writes review after inspecting worker evidence and actual artifacts.

## Git review model

The taskflow does not require Kimi to commit. The intended real-project loop is:

1. Start from a clean independent project Git root and baseline.
2. Kimi modifies only TASK-allowed files and writes task-local evidence.
3. Codex/human reviews `RESULT.md`, `VERIFY.md`, logs, `git status`, tracked diffs, staged diffs, and untracked files.
4. Codex/human accepts, asks for changes, reverts, or commits explicitly.

Task folders store evidence. Git stores the real project change history. They are complementary, not replacements for each other.




