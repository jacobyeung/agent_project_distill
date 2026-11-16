"""Nondeleting donor lease operations; Git metadata queries are deliberately disabled."""
import json
import os
import re
import socket
import sys
import tempfile
from datetime import datetime, timezone
from nondeleting_lifecycle import retire_path, fsync_dir, serialized_work

WORK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def agent_id():
    return os.environ['AGENT_ID']


def write_json(path, obj):
    directory = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(
        prefix=os.path.basename(path) + ".", suffix=".tmp", dir=directory, text=True
    )
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(obj, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        fsync_dir(directory)
    except BaseException:
        try:
            retire_path(tmp, missing_ok=True)
        except FileNotFoundError:
            pass
        raise


def read_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def validate_work_id(work_id):
    if not WORK_ID_RE.match(work_id):
        sys.exit(f"ERROR: invalid work_id {work_id!r} (allowed: [A-Za-z0-9._-], no '/' or spaces)")
    return work_id


class Coord:
    def __init__(self, root):
        self.root = root
        self.leases = os.path.join(root, "LEASES")
        self.completed = os.path.join(root, "COMPLETED")
        self.failed = os.path.join(root, "FAILED")
        self.status = os.path.join(root, "STATUS")
        self.queue = os.path.join(root, "RUN_QUEUE.jsonl")
        self.merge_lock = os.path.join(root, "MAIN_MERGE.lock")

    def ensure(self):
        for d in (self.leases, self.completed, self.failed, self.status):
            os.makedirs(d, exist_ok=True)
        if not os.path.exists(self.queue):
            open(self.queue, "a").close()

    def lease_dir(self, work_id):
        return os.path.join(self.leases, work_id + ".lock")

    def completed_dir(self, work_id):
        return os.path.join(self.completed, work_id + ".lock")

    def failed_dir(self, work_id):
        return os.path.join(self.failed, work_id + ".lock")

    def is_active(self, work_id):
        return os.path.isdir(self.lease_dir(work_id))

    def is_completed(self, work_id):
        return os.path.isdir(self.completed_dir(work_id))

    def is_failed(self, work_id):
        return os.path.isdir(self.failed_dir(work_id))

    def read_queue(self):
        rows = []
        if not os.path.exists(self.queue):
            return rows
        with open(self.queue) as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    rows.append(json.loads(ln))
                except json.JSONDecodeError:
                    pass
        return rows


@serialized_work
def do_claim(c, work_id, fields, force=False):
    """Atomic claim. Returns (won: bool, reason: str)."""
    validate_work_id(work_id)
    if force:
        sys.exit("ERROR: force claims are disabled in the lifecycle successor")
    if c.is_completed(work_id) and not force:
        return False, "already-completed"
    try:
        os.mkdir(c.lease_dir(work_id))  # <-- atomic coordination point
        fsync_dir(c.leases)
    except FileExistsError:
        return False, "lease-held"
    lease = {
        "work_id": work_id,
        "group_id": fields.get("group_id"),
        "agent_id": agent_id(),
        "pid": fields.get("pid") or os.getpid(),
        "host": socket.gethostname(),
        "branch": None,
        "commit": None,
        "command": fields.get("command"),
        "smoke": fields.get("smoke"),
        "started_at": now_iso(),
        "last_heartbeat": now_iso(),
        "status": "running",
    }
    for k in ("category", "exp_tag", "split", "seed", "config_hash", "source"):
        if fields.get(k) is not None:
            lease[k] = fields[k]
    write_json(os.path.join(c.lease_dir(work_id), "lease.json"), lease)
    return True, "claimed"


@serialized_work
def move_lease(c, work_id, dest_dir, **updates):
    src = c.lease_dir(work_id)
    if not os.path.isdir(src):
        sys.exit(f"ERROR: no active lease for {work_id}")
    lease = read_json(os.path.join(src, "lease.json"))
    if lease.get("agent_id") != agent_id():
        sys.exit("ERROR: terminal transition requires the lease owner")
    lease.update(updates)
    write_json(os.path.join(src, "lease.json"), lease)
    dst = os.path.join(dest_dir, work_id + ".lock")
    if os.path.isdir(dst):
        retire_path(dst)
    os.rename(src, dst)
    fsync_dir(dest_dir)
    fsync_dir(c.leases)
    return dst


@serialized_work
def cmd_heartbeat(c, a):
    src = c.lease_dir(a.work_id)
    lp = os.path.join(src, "lease.json")
    if not os.path.isdir(src):
        sys.exit(f"ERROR: no active lease for {a.work_id}")
    lease = read_json(lp)
    if lease.get("agent_id") != agent_id():
        sys.exit("ERROR: heartbeat requires the lease owner")
    lease["last_heartbeat"] = now_iso()
    if a.status:
        lease["status"] = a.status
    if a.note:
        lease["note"] = a.note
    write_json(lp, lease)
    print(f"HEARTBEAT {a.work_id} @ {lease['last_heartbeat']}")


def cmd_complete(c, a):
    move_lease(c, a.work_id, c.completed, status="completed",
               ended_at=now_iso(), result=a.result)
    print(f"COMPLETED {a.work_id}")


if __name__ == '__main__':
    import argparse
    from pathlib import Path
    from gt_scene_assets import DATA_ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--work-id', required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    if root != Path('/data2/jjyeung/agent_project/.coord') and not root.is_relative_to(DATA_ROOT / 'runtime_control/gt_teacher_r1313'):
        raise ValueError('lease heartbeat is outside the shared or fixture coordination namespace')
    validate_work_id(args.work_id)
    args.status, args.note = None, None
    cmd_heartbeat(Coord(str(root)), args)
