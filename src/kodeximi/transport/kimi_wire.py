from __future__ import annotations

import json
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

from kodeximi.approval import decide_approval
from kodeximi.config import kx_dir
from kodeximi.path_policy import PathPolicy
from kodeximi.task_render import render_worker_prompt
from kodeximi.task_spec import TaskSpec
from kodeximi.transport.base import WorkerResult


class KimiWireTransport:
    name = "kimi-wire"

    def run(self, *, root: Path, attempt_dir: Path, spec: TaskSpec, job_id: str, attempt_no: int) -> WorkerResult:
        base = kx_dir(root)
        command = [
            "kimi",
            "--wire",
            "--work-dir",
            str(root),
            "--agent-file",
            str(base / "agents" / "kodeximi-worker.yaml"),
            "--skills-dir",
            str(base / "skills"),
            "--max-steps-per-turn",
            "20",
        ]
        wire_log = attempt_dir / "wire.jsonl"
        approvals_log = attempt_dir / "approval-decisions.jsonl"
        status_updates = 0
        prompt_id = f"kodeximi-prompt-{uuid.uuid4().hex}"
        initialize_id = f"kodeximi-init-{uuid.uuid4().hex}"
        prompt = render_worker_prompt(root=root, attempt_dir=attempt_dir, spec=spec, job_id=job_id, attempt_no=attempt_no)
        policy = PathPolicy(root, spec)
        started = time.monotonic()
        proc = subprocess.Popen(
            command,
            cwd=str(root),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        try:
            assert proc.stdin is not None
            assert proc.stdout is not None
            init = {
                "jsonrpc": "2.0",
                "id": initialize_id,
                "method": "initialize",
                "params": {
                    "protocol_version": "1.10",
                    "client": {"name": "kodeximi", "version": "0.1.0a0"},
                    "capabilities": {"supports_question": True},
                },
            }
            self._send(proc, init)
            initialized = False
            deadline = time.monotonic() + spec.attempt_timeout_seconds
            with wire_log.open("w", encoding="utf-8") as wire_fp, approvals_log.open("w", encoding="utf-8") as approval_fp:
                while time.monotonic() < deadline:
                    line = proc.stdout.readline()
                    if not line:
                        break
                    wire_fp.write(line)
                    wire_fp.flush()
                    try:
                        message = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if message.get("id") == initialize_id:
                        initialized = True
                        prompt_request = {"jsonrpc": "2.0", "id": prompt_id, "method": "prompt", "params": {"user_input": prompt}}
                        self._send(proc, prompt_request)
                        continue
                    if message.get("method") == "event":
                        params = message.get("params") or {}
                        if isinstance(params, dict) and params.get("type") == "StatusUpdate":
                            status_updates += 1
                        continue
                    if message.get("method") == "request":
                        params = message.get("params") or {}
                        response = self._handle_request(params, message.get("id"), root=root, policy=policy, attempt_dir=attempt_dir)
                        approval_fp.write(json.dumps(response, ensure_ascii=False) + "\n")
                        approval_fp.flush()
                        self._send(proc, response)
                        continue
                    if message.get("id") == prompt_id:
                        result = message.get("result") or {}
                        status = result.get("status") if isinstance(result, dict) else None
                        return WorkerResult(
                            status=str(status or "failed"),
                            result_path=attempt_dir / "RESULT.md",
                            usage_payload={
                                "transport": self.name,
                                "status_updates": status_updates,
                                "duration_ms": int((time.monotonic() - started) * 1000),
                                "initialized": initialized,
                            },
                        )
                return WorkerResult(status="timeout", usage_payload={"transport": self.name, "status_updates": status_updates})
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

    def _send(self, proc: subprocess.Popen[str], payload: dict[str, Any]) -> None:
        assert proc.stdin is not None
        proc.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        proc.stdin.flush()

    def _handle_request(self, params: Any, rpc_id: Any, *, root: Path, policy: PathPolicy, attempt_dir: Path) -> dict[str, object]:
        if not isinstance(params, dict):
            return {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32600, "message": "invalid request params"}}
        request_type = params.get("type")
        payload = params.get("payload") or {}
        if request_type == "ApprovalRequest" and isinstance(payload, dict):
            decision = decide_approval(root=root, policy=policy, attempt_dir=attempt_dir, payload=payload)
            return {"jsonrpc": "2.0", "id": rpc_id, "result": decision}
        if request_type == "QuestionRequest":
            request_id = payload.get("id") if isinstance(payload, dict) else ""
            return {"jsonrpc": "2.0", "id": rpc_id, "result": {"request_id": request_id, "answers": {}}}
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {"code": -32601, "message": f"unsupported KodeXimi wire request: {request_type}"},
        }

