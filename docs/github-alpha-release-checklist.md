# GitHub Alpha Release Checklist

This checklist is for publishing the alpha demo as a small, honest, runnable project.

## Positioning

- [ ] Repository title and README say **Alpha Demo**.
- [ ] README says this is a Codex-first, Kimi-worker taskflow.
- [ ] README does not claim this is a mature multi-agent platform.
- [ ] README does not claim this is a security sandbox.
- [ ] `ALPHA_NOTICE.md` is present and linked from README.

## Public safety wording

- [ ] `allowed_reads` / `allowed_writes` are described as advisory workflow instructions.
- [ ] Kimi is described as running with current user permissions.
- [ ] `VERIFY.md` is described as worker evidence, not final proof.
- [ ] Git review is described as reviewer-owned.
- [ ] No automatic `git add`, `git commit`, `git push`, rollback, or cleanup is promised.

## Repo hygiene

- [ ] No personal absolute paths appear in README, docs, templates, examples, or scripts.
- [ ] `.gitignore` is present.
- [ ] Example data is synthetic and safe to publish.
- [ ] Runtime logs in examples are either intentionally kept as sample evidence or removed before release.
- [ ] No `.env`, credentials, tokens, database strings, or private URLs are present.
- [ ] No generated business output from real projects is included.

## Smoke checks

Run from repo root:

```powershell
.\scripts\doctor.ps1
.\scripts\verify-install.ps1
.\cli\kodeximi.ps1 validate .\examples\hello-worker
.\cli\kodeximi.ps1 review-check .\examples\hello-worker -Project .
```

Expected:

- `doctor: OK`
- `verify-install: OK`
- `validate: OK`
- `review-check` prints evidence status and Git review state.

## First release scope

Include:

- [ ] `cli/kodeximi.ps1`
- [ ] `kimi/agents/`
- [ ] `templates/`
- [ ] `docs/`
- [ ] `scripts/doctor.ps1`
- [ ] `scripts/verify-install.ps1`
- [ ] `scripts/install.ps1` and `scripts/uninstall.ps1` as optional helpers
- [ ] `examples/`
- [ ] `ALPHA_NOTICE.md`
- [ ] `LICENSE`

Do not add before first alpha release:

- [ ] Global auto-enable behavior.
- [ ] Hooks/plugins/MCP/ACP/Wire/worktree/dashboard.
- [ ] Automatic commits.
- [ ] Production security claims.
- [ ] Complex multi-worker queue semantics.

## Suggested first commit message

```text
Initial alpha demo for KodeXimi
```





