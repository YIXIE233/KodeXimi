# Command Protocol

All KodeXimi CLI commands should emit strict JSON on stdout.

Use:

```powershell
kodeximi init
kodeximi doctor
kodeximi doctor --wire-smoke
kodeximi session start --mode strict
kodeximi task validate --from-json task.json
kodeximi job run --from-json task.json --wait
kodeximi job status job-xxxxxxxx
kodeximi review package job-xxxxxxxx
kodeximi review decide job-xxxxxxxx --decision accepted --reason-file CODEX_REVIEW.md
kodeximi review decide job-xxxxxxxx --decision rework --reason-file CODEX_REVIEW.md
kodeximi job rerun job-xxxxxxxx --wait
kodeximi job cancel job-xxxxxxxx
```

`review decide --decision rework` records the rework decision but does not automatically run another attempt.

`job cancel` is for active jobs. It returns `JOB_NOT_ACTIVE` for jobs already waiting for review or in a terminal state.
