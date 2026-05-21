# v0.1 Fake Code Edit Example

This example demonstrates the v0.1 Python runtime flow with `FakeTransport`.

It does not call Kimi. It verifies:

- TaskSpec v0.1 shape.
- `job run` reaches `needs_review`.
- runtime-generated `VERIFY.md`.
- evidence digest and review package.

Run from a temporary copy or a clean git repository:

```powershell
$env:PYTHONPATH = "C:\path\to\KodeXimi\src"
python -m kodeximi init
python -m kodeximi session start --mode strict
python -m kodeximi job run --from-json examples\v0.1-fake-code-edit\task.json --wait
```

