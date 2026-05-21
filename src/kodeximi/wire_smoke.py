from __future__ import annotations

import json
import queue
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Any


def kimi_info(kimi_executable: str = "kimi") -> dict[str, str | None]:
    proc = subprocess.run([kimi_executable, "info"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
    text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    return {
        "returncode": str(proc.returncode),
        "kimi_cli_version": _match(text, r"kimi-cli version:\s*([^\r\n]+)"),
        "agent_spec_versions": _match(text, r"agent spec versions:\s*([^\r\n]+)"),
        "wire_protocol": _match(text, r"wire protocol:\s*([^\r\n]+)"),
        "python_version": _match(text, r"python version:\s*([^\r\n]+)"),
    }


def _match(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None


def _readline_worker(stream: Any, out: queue.Queue[str | None]) -> None:
    try:
        out.put(stream.readline())
    except Exception:
        out.put(None)


def run_wire_initialize(
    command: list[str],
    *,
    cwd: Path,
    timeout_seconds: float = 15.0,
    protocol_version: str | None = None,
) -> dict[str, object]:
    request = {
        "jsonrpc": "2.0",
        "id": "kodeximi-init-1",
        "method": "initialize",
        "params": {
            "protocol_version": protocol_version or "1.10",
            "client": {"name": "kodeximi", "version": "0.1.0a0"},
            "capabilities": {"supports_question": True},
        },
    }
    started = time.monotonic()
    proc = subprocess.Popen(
        command,
        cwd=str(cwd),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    stdout_queue: queue.Queue[str | None] = queue.Queue(maxsize=1)
    stderr_queue: queue.Queue[str | None] = queue.Queue(maxsize=1)
    try:
        assert proc.stdin is not None
        proc.stdin.write(json.dumps(request, ensure_ascii=False) + "\n")
        proc.stdin.flush()
        assert proc.stdout is not None
        assert proc.stderr is not None
        threading.Thread(target=_readline_worker, args=(proc.stdout, stdout_queue), daemon=True).start()
        threading.Thread(target=_readline_worker, args=(proc.stderr, stderr_queue), daemon=True).start()
        try:
            line = stdout_queue.get(timeout=timeout_seconds)
        except queue.Empty:
            line = None
        duration_ms = int((time.monotonic() - started) * 1000)
        if not line:
            stderr_line = None
            try:
                stderr_line = stderr_queue.get_nowait()
            except queue.Empty:
                pass
            return {
                "ok": False,
                "error_code": "WIRE_INIT_TIMEOUT",
                "message": "no initialize response before timeout",
                "duration_ms": duration_ms,
                "stderr_line": stderr_line,
            }
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            return {
                "ok": False,
                "error_code": "WIRE_NON_JSON_RESPONSE",
                "message": "wire response was not JSON",
                "duration_ms": duration_ms,
                "raw_line": line,
            }
        if "result" in payload:
            return {"ok": True, "duration_ms": duration_ms, "response": payload}
        error = payload.get("error") or {}
        if error.get("code") == -32601:
            return {
                "ok": True,
                "duration_ms": duration_ms,
                "response": payload,
                "compatibility": "initialize_not_supported",
            }
        return {"ok": False, "error_code": "WIRE_INIT_ERROR", "duration_ms": duration_ms, "response": payload}
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            try:
                if stream:
                    stream.close()
            except Exception:
                pass


def smoke_system_kimi(cwd: Path, kimi_executable: str = "kimi") -> dict[str, object]:
    info = kimi_info(kimi_executable)
    protocol = info.get("wire_protocol")
    result = run_wire_initialize([kimi_executable, "--wire"], cwd=cwd, protocol_version=protocol if isinstance(protocol, str) else None)
    return {"ok": bool(result.get("ok")), "kimi_info": info, "wire_initialize": result}
