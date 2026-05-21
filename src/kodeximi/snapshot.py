from __future__ import annotations

import subprocess
from pathlib import Path

from .errors import DirtyWorktree, RootLocked


def run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")


def is_git_repo(root: Path) -> bool:
    proc = run_git(root, ["rev-parse", "--is-inside-work-tree"])
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def git_status(root: Path) -> str:
    proc = run_git(root, ["status", "--porcelain=v1"])
    return proc.stdout


def require_clean_worktree(root: Path) -> None:
    if not is_git_repo(root):
        raise DirtyWorktree("KodeXimi v0.1 requires a git repository for snapshot-backed direct mode.")
    status = git_status(root)
    ignored = [line for line in status.splitlines() if ".kodeximi/" not in line]
    if ignored:
        raise DirtyWorktree("worktree must be clean before running a job")


def acquire_root_lock(kx_dir: Path, job_id: str) -> Path:
    lock = kx_dir / "run.lock"
    try:
        fd = lock.open("x", encoding="utf-8")
    except FileExistsError as exc:
        raise RootLocked(f"root is already locked: {lock}") from exc
    with fd:
        fd.write(job_id + "\n")
    return lock


def release_root_lock(lock: Path | None) -> None:
    if lock and lock.exists():
        lock.unlink()


def write_pre_status(root: Path, attempt_dir: Path) -> None:
    attempt_dir.mkdir(parents=True, exist_ok=True)
    (attempt_dir / "pre_status.txt").write_text(git_status(root), encoding="utf-8")
    head = run_git(root, ["rev-parse", "HEAD"])
    (attempt_dir / "base_head.txt").write_text(head.stdout.strip() + "\n", encoding="utf-8")


def write_post_diff(root: Path, attempt_dir: Path) -> None:
    (attempt_dir / "post_status.txt").write_text(git_status(root), encoding="utf-8")
    diff = run_git(root, ["diff", "--binary"])
    (attempt_dir / "patch.diff").write_text(diff.stdout, encoding="utf-8")
    name_status = run_git(root, ["diff", "--name-status"])
    changed = []
    for line in name_status.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            changed.append({"status": parts[0], "path": parts[-1]})
    import json

    (attempt_dir / "changed-files.json").write_text(json.dumps(changed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

