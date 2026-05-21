# Command Protocol

All KodeXimi CLI commands should emit strict JSON on stdout.

Use:

```powershell
kodeximi init
kodeximi doctor
kodeximi session start --mode strict
kodeximi task validate --from-json task.json
kodeximi job run --from-json task.json --wait
kodeximi job status job-xxxxxxxx
kodeximi review decide job-xxxxxxxx --decision accepted --reason-file CODEX_REVIEW.md
```

`review decide --decision rework` records the rework decision but does not automatically run another attempt.

