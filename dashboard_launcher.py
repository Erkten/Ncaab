#!/usr/bin/env python3
"""Safe launcher: keep the local Streamlit dashboard updated from approved GitHub main.

Run from the existing project folder:
    python3 Ncaab_latest/dashboard_launcher.py

Requires the already-cloned Ncaab_latest Git repository next to app.py.
Does not upload any local files, data, or credentials.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime

REPOSITORY = "https://github.com/Erkten/Ncaab.git"
UPDATE_INTERVAL_SECONDS = 300
KEEP_BACKUPS = 20


def say(message: str) -> None:
    print("[Dashboard] " + message, flush=True)


def capture(args: list[str], *, cwd: Path | None = None, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        args, cwd=str(cwd) if cwd else None, text=True,
        capture_output=True, timeout=timeout, check=False,
    )


def safe_update(repo: Path, project: Path) -> bool:
    """Fetch only main, validate new app.py and atomically replace with backup."""
    target = project / "app.py"
    source = repo / "app.py"
    if not (repo / ".git").exists():
        say("Git clone not found; keeping the local app unchanged.")
        return False

    remote = capture(["git", "-C", str(repo), "remote", "get-url", "origin"])
    if remote.returncode != 0 or remote.stdout.strip().rstrip("/") not in (
        REPOSITORY, "git@github.com:Erkten/Ncaab.git",
    ):
        say("Unexpected Git origin. Skipping update for safety.")
        return False

    branch = capture(["git", "-C", str(repo), "branch", "--show-current"])
    if branch.returncode != 0 or branch.stdout.strip() != "main":
        say("The clone is not on main; skipping update for safety.")
        return False

    status = capture(["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=no"])
    if status.returncode != 0 or status.stdout.strip():
        say("GitHub clone has local modifications; skipping update to protect them.")
        return False

    fetch = capture(["git", "-C", str(repo), "pull", "--ff-only", "origin", "main"], timeout=90)
    if fetch.returncode:
        say("Cannot reach/update GitHub right now; launching the existing app. " +
            (fetch.stderr or fetch.stdout).strip()[-240:])
        return False
    if not source.is_file():
        say("Updated clone has no app.py; leaving the running app intact.")
        return False

    candidate = source.read_bytes()
    try:
        compile(candidate, str(target), "exec")
    except (SyntaxError, ValueError) as exc:
        say(f"Downloaded Python file failed syntax validation: {exc}. No changes applied.")
        return False

    current = target.read_bytes() if target.exists() else b""
    if current == candidate:
        return True

    backup_dir = project / "dashboard_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    if target.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        digest = hashlib.sha256(current).hexdigest()[:10]
        backup_path = backup_dir / f"app_{timestamp}_{digest}.py"
        shutil.copy2(target, backup_path)
        say(f"Previous app saved in {backup_path.name}")

    # Save in the same directory and rename atomically. This works even
    # while Streamlit is running; Streamlit's normal source watcher reloads it.
    fd, temporary = tempfile.mkstemp(prefix=".app_next_", suffix=".py", dir=project)
    try:
        with os.fdopen(fd, "wb") as file:
            file.write(candidate)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    say("Updated app.py from GitHub main.")
    backups = sorted(backup_dir.glob("app_*.py"), key=lambda p: p.stat().st_mtime, reverse=True)
    for older in backups[KEEP_BACKUPS:]:
        older.unlink(missing_ok=True)
    return True


def main() -> int:
    repo = Path(__file__).resolve().parent
    project = repo.parent
    if not (project / "app.py").exists():
        say(f"Expected app.py in {project}; nothing was changed.")
        return 1

    say("Checking GitHub and creating backups before any update...")
    try:
        safe_update(repo, project)
    except (OSError, subprocess.TimeoutExpired) as exc:
        say(f"Update unavailable: {exc}. Keeping the local app.")

    command = [sys.executable, "-m", "streamlit", "run", str(project / "app.py")]
    if capture([sys.executable, "-c", "import streamlit"], timeout=15).returncode:
        streamlit = shutil.which("streamlit")
        if streamlit:
            command = [streamlit, "run", str(project / "app.py")]
        else:
            say("Streamlit not installed in this Python environment.")
            return 1

    say("Starting Streamlit at http://localhost:8501")
    say("While this launcher stays running it checks GitHub every 5 minutes.")
    try:
        app = subprocess.Popen(command, cwd=str(project))
    except OSError as exc:
        say(f"Could not start Streamlit: {exc}")
        return 1
    try:
        while True:
            try:
                return app.wait(timeout=UPDATE_INTERVAL_SECONDS)
            except subprocess.TimeoutExpired:
                try:
                    safe_update(repo, project)
                except (OSError, subprocess.TimeoutExpired) as exc:
                    say(f"Update unavailable: {exc}. Existing app is unaffected.")
    except KeyboardInterrupt:
        say("Stopping Streamlit...")
        app.terminate()
        try:
            app.wait(timeout=8)
        except subprocess.TimeoutExpired:
            app.kill()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
