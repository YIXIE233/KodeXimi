from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any

from .errors import VerificationTimeout, VerificationUnsupported


def _truncate(text: str, max_bytes: int) -> str:
    data = text.encode("utf-8", errors="replace")
    if len(data) <= max_bytes:
        return text
    head = data[: max_bytes // 2].decode("utf-8", errors="replace")
    tail = data[-max_bytes // 2 :].decode("utf-8", errors="replace")
    return head + f"\n...[truncated {len(data) - max_bytes} bytes]...\n" + tail


def run_verification(root: Path, attempt_dir: Path, commands: list[dict[str, Any]]) -> dict[str, Any]:
    logs_dir = attempt_dir / "verification"
    logs_dir.mkdir(parents=True, exist_ok=True)
    results = []
    conclusion = "pass"
    for command in commands:
        command_type = command["type"]
        command_id = command["id"]
        timeout = int(command.get("timeout_seconds", 120))
        started = time.monotonic()
        if command_type == "file_exists":
            path = root / command["path"]
            ok = path.exists()
            result = {"id": command_id, "type": command_type, "exit_code": 0 if ok else 1, "passed": ok, "path": command["path"]}
        elif command_type in {"python_pytest", "python_script", "git_diff_stat"}:
            argv = command.get("argv")
            if command_type == "git_diff_stat":
                argv = ["git", "-C", str(root), "diff", "--stat"]
            if not isinstance(argv, list):
                raise VerificationUnsupported(f"verification command {command_id} missing argv")
            try:
                proc = subprocess.run(
                    argv,
                    cwd=str(root / command.get("cwd", ".")),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout,
                    shell=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise VerificationTimeout(f"verification command timed out: {command_id}") from exc
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
            (logs_dir / f"{command_id}.stdout.log").write_text(stdout, encoding="utf-8")
            (logs_dir / f"{command_id}.stderr.log").write_text(stderr, encoding="utf-8")
            expected = int(command.get("expected_exit_code", 0))
            result = {
                "id": command_id,
                "type": command_type,
                "argv": argv,
                "exit_code": proc.returncode,
                "expected_exit_code": expected,
                "passed": proc.returncode == expected,
                "stdout_excerpt": _truncate(stdout, int(command.get("stdout_max_bytes", 20000))),
                "stderr_excerpt": _truncate(stderr, int(command.get("stderr_max_bytes", 20000))),
            }
        else:
            raise VerificationUnsupported(f"unsupported verification command type: {command_type}")
        result["duration_ms"] = int((time.monotonic() - started) * 1000)
        if not result["passed"]:
            conclusion = "fail"
        results.append(result)
    return {"conclusion": conclusion, "commands": results}


def write_verify_files(attempt_dir: Path, verify: dict[str, Any]) -> None:
    import json

    (attempt_dir / "verify.json").write_text(json.dumps(verify, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# VERIFY", "", f"Conclusion: {verify['conclusion']}", ""]
    for command in verify["commands"]:
        lines.append(f"## {command['id']}")
        lines.append("")
        lines.append(f"- Type: `{command['type']}`")
        lines.append(f"- Exit code: `{command.get('exit_code')}`")
        lines.append(f"- Passed: `{command.get('passed')}`")
        if command.get("stdout_excerpt"):
            lines.append("")
            lines.append("### stdout excerpt")
            lines.append("```text")
            lines.append(str(command["stdout_excerpt"]))
            lines.append("```")
        if command.get("stderr_excerpt"):
            lines.append("")
            lines.append("### stderr excerpt")
            lines.append("```text")
            lines.append(str(command["stderr_excerpt"]))
            lines.append("```")
        lines.append("")
    (attempt_dir / "VERIFY.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

