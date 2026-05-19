# Alpha Limitations

This repository is a runnable prototype, not a stable product.

## Current limitations

- No OS-level sandbox.
- `allowed_reads` / `allowed_writes` are advisory.
- Kimi runs with user permissions.
- `VERIFY.md` is worker self-report and must be reviewed independently.
- Batch/parallel execution is experimental.
- `depends_on` is not a mature scheduler.
- Path conflict checks are best-effort.
- Git review support is read-only summary only; the taskflow does not manage staging, commits, branches, or rollbacks.
- No plugin, hook, MCP, Wire, ACP, worktree, daemon, dashboard, cancel, or resume.

## Recommended use

Use only on isolated demos or low-risk sandboxes. For real projects, start with a clean independent project Git root and baseline, small tasks, and independent review.





