from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import doctor, init_project
from .errors import KodeXimiError
from .job import job_status, run_job
from .jsonio import print_json
from .review import decide
from .session import start_session, status_session, stop_session
from .task_spec import load_task_spec, validate_task_spec


def _cwd(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "cwd", None) or ".").resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kodeximi")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("--cwd")
    p_init.set_defaults(func=lambda a: init_project(_cwd(a)))

    p_doctor = sub.add_parser("doctor")
    p_doctor.add_argument("--cwd")
    p_doctor.set_defaults(func=lambda a: doctor(_cwd(a)))

    p_session = sub.add_parser("session")
    session_sub = p_session.add_subparsers(dest="session_command", required=True)
    p_session_start = session_sub.add_parser("start")
    p_session_start.add_argument("--cwd")
    p_session_start.add_argument("--mode", choices=["strict", "normal"], default="strict")
    p_session_start.add_argument("--scope", default="current_thread")
    p_session_start.set_defaults(func=lambda a: start_session(_cwd(a), mode=a.mode, scope=a.scope))
    p_session_status = session_sub.add_parser("status")
    p_session_status.add_argument("--cwd")
    p_session_status.set_defaults(func=lambda a: status_session(_cwd(a)))
    p_session_stop = session_sub.add_parser("stop")
    p_session_stop.add_argument("--cwd")
    p_session_stop.set_defaults(func=lambda a: stop_session(_cwd(a)))

    p_task = sub.add_parser("task")
    task_sub = p_task.add_subparsers(dest="task_command", required=True)
    p_task_validate = task_sub.add_parser("validate")
    p_task_validate.add_argument("--from-json", required=True)
    p_task_validate.set_defaults(func=lambda a: {"ok": True, "task_type": load_task_spec(Path(a.from_json)).task_type})

    p_job = sub.add_parser("job")
    job_sub = p_job.add_subparsers(dest="job_command", required=True)
    p_job_run = job_sub.add_parser("run")
    p_job_run.add_argument("--cwd")
    p_job_run.add_argument("--from-json", required=True)
    p_job_run.add_argument("--transport", choices=["fake", "kimi-wire"], default="fake")
    p_job_run.add_argument("--wait", action="store_true")
    p_job_run.set_defaults(func=lambda a: run_job(_cwd(a), load_task_spec(Path(a.from_json)), transport=a.transport))
    p_job_status = job_sub.add_parser("status")
    p_job_status.add_argument("job_id")
    p_job_status.add_argument("--cwd")
    p_job_status.set_defaults(func=lambda a: job_status(_cwd(a), a.job_id))

    p_review = sub.add_parser("review")
    review_sub = p_review.add_subparsers(dest="review_command", required=True)
    p_review_decide = review_sub.add_parser("decide")
    p_review_decide.add_argument("job_id")
    p_review_decide.add_argument("--cwd")
    p_review_decide.add_argument("--decision", required=True)
    p_review_decide.add_argument("--reason", default="")
    p_review_decide.add_argument("--reason-file")
    p_review_decide.set_defaults(func=lambda a: decide(_cwd(a), a.job_id, a.decision, a.reason, Path(a.reason_file) if a.reason_file else None))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = args.func(args)
        print_json(result)
        return 0 if result.get("ok", False) else 1
    except KodeXimiError as exc:
        print_json(exc.to_dict())
        return 1
    except Exception as exc:
        print_json({"ok": False, "error_code": "UNHANDLED_EXCEPTION", "message": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

