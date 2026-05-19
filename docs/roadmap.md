# Roadmap

## Alpha (current demo)

- [x] Repo-local PowerShell 7 CLI wrapper.
- [x] Project-local ON/OFF marker: `.kodeximi/enabled`.
- [x] Kimi custom agent loaded via `--agent-file`.
- [x] Task templates and `status.json` tracking.
- [x] Task-local RESULT / VERIFY / logs.
- [x] CODEX_REVIEW ownership rule.
- [x] Basic validation and misplaced evidence detection.
- [x] `review-check` for evidence and Git review summaries.
- [x] Basic batch execution with best-effort write-set conflict checks.
- [x] Serial fallback when dependencies are present.
- [x] Example tasks: hello, single code change, batch, structured input.

## Beta candidates

- [ ] Stronger task schema validation.
- [ ] `RESULT.json` / `VERIFY.json` sidecars for machine-readable review.
- [ ] Better dependency-aware batch scheduler.
- [ ] Job registry such as `.kodeximi/jobs.jsonl`.
- [ ] Cancel/status/result commands for long-running jobs.
- [ ] Optional warning hooks for repeated protocol violations.
- [ ] CI examples for validating templates and CLI behavior.
- [ ] Cross-platform hardening beyond the current Windows-first demo.

## Later options

- [ ] Optional Git review branches or worktree mode.
- [ ] Optional hook/plugin enforcement for path boundaries, evidence existence, or crawl guards.
- [ ] Optional dashboard generated from task/job status.
- [ ] Remote worker dispatch.

## Non-goals for alpha

- No automatic staging or commits.
- No production security sandbox claim.
- No MCP / ACP / Wire integration.
- No persistent queue or database backend.
- No real-time multi-user collaboration.



