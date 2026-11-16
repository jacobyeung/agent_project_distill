import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def activity(directory):
    root = Path(directory)
    paths = {path for pattern in ("*.json", "*.jsonl", "checkpoint_*/*", "checkpoint_*/shards/*",
                                  "m*/*", "m*/full_weights/*") for path in root.glob(pattern)}
    values = []
    for path in sorted(paths):
        try:
            if path.is_file() and not path.is_symlink():
                stat = path.stat()
                values.append((str(path.relative_to(root)), stat.st_size, stat.st_mtime_ns))
        except FileNotFoundError:
            continue
    return values


def terminate(child, sig):
    if child.poll() is not None:
        return
    pending, owned = [child.pid], []
    while pending:
        pid = pending.pop()
        owned.append(pid)
        try:
            pending.extend(map(int, Path(f"/proc/{pid}/task/{pid}/children").read_text().split()))
        except FileNotFoundError:
            continue
    for pid in reversed(owned):
        try:
            os.kill(pid, sig)
        except ProcessLookupError:
            continue


def normalize(settings=None):
    settings = {} if settings is None else settings
    if not isinstance(settings, dict) or set(settings) - {
            "startup_seconds", "idle_seconds", "checkpoint_grace_seconds", "poll_seconds"}:
        raise ValueError("Unknown stall guard setting")
    startup = settings.get("startup_seconds", 3600)
    idle = settings.get("idle_seconds", 1200)
    grace = settings.get("checkpoint_grace_seconds", 600)
    poll = settings.get("poll_seconds", 10)
    if any(type(value) not in (int, float) or not math.isfinite(value) or value <= 0
           for value in (startup, idle, grace, poll)):
        raise ValueError("Stall guard intervals must be finite and positive")
    return startup, idle, grace, poll


def supervise(child, directory, relay, settings=None):
    startup, idle, grace, poll = normalize(settings)
    prior, started = activity(directory), time.monotonic()
    attempts = {row for row in prior if row[0].startswith("attempt_") and row[0].endswith(".json")}
    own_attempt = "attempt_"+os.environ["SLURM_JOB_ID"]+".json" if os.environ.get("SLURM_JOB_ID") else None
    steady = any(row[0] == own_attempt for row in attempts)
    last = started
    while child.poll() is None:
        try:
            return child.wait(timeout=poll)
        except subprocess.TimeoutExpired:
            current = activity(directory)
            now = time.monotonic()
            current_attempts = {row for row in current if row[0].startswith("attempt_") and row[0].endswith(".json")}
            if not steady and current_attempts-attempts:
                steady, last = True, now
            if current != prior:
                prior, last = current, now
            if now-(last if steady else started) <= (idle if steady else startup):
                continue
        print(json.dumps(dict(event="stall_guard", status="STALLED", pid=child.pid,
                              phase="steady" if steady else "startup", startup_seconds=startup,
                              idle_seconds=idle, checkpoint_grace_seconds=grace)), file=sys.stderr, flush=True)
        relay(child.pid)
        try:
            child.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            terminate(child, signal.SIGTERM)
            try:
                child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                terminate(child, signal.SIGKILL)
                child.wait()
        return 124
    return child.returncode
