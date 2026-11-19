"""Publish prepared evidence and wait for an independently authored receipt."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import random
import resource
import signal
import stat
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from z import load, seal, write

CAP = 2_000_000
V_CAP = 50_000_000
STREAMS = ("pose", "vqa", "routing", "pointing")
NAMES = dict(zip(STREAMS, ("e0.json", "e1.json", "e2.json", "e3.json")))


def encoded(v):
    return (json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def put(path, raw):
    path = Path(path)
    temp = path.with_name(path.name + ".part")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW
    fd = os.open(temp, flags, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, path)


def stamp():
    return datetime.now(timezone.utc).isoformat()


def location(kit, root, job):
    target = Path(load(kit / "k/p.json")["n_root"])
    if not target.is_absolute() or ".." in target.parts or not job.replace("_", "").isalnum():
        raise ValueError("R1_REVIEW_FILE_UNUSABLE")
    live = target / "o" / job / "live"
    review = target / "n_r" / "review.json"
    for p in (live,):
        if any(v.is_symlink() for v in (p, *p.parents)):
            raise ValueError("R1_REVIEW_FILE_UNUSABLE")
        if any(p.resolve().is_relative_to(v.resolve()) for v in (kit, root / "kit", root / "h")):
            raise ValueError("R1_REVIEW_FILE_UNUSABLE")
    live.mkdir(parents=True, exist_ok=True, mode=0o700)
    return live, review


def receipt_bytes(path):
    """Open the owner-private directory and leaf without following symlinks."""
    if any(p.is_symlink() for p in (path.parent, *path.parent.parents)):
        raise ValueError("R1_REVIEW_FILE_UNUSABLE")
    try:
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except FileNotFoundError:
        return None
    except OSError:
        raise ValueError("R1_REVIEW_FILE_UNUSABLE") from None
    try:
        ds = os.fstat(fd)
        if ds.st_uid != os.getuid() or stat.S_IMODE(ds.st_mode) != 0o700:
            raise ValueError("R1_REVIEW_FILE_UNUSABLE")
        try:
            leaf = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        except FileNotFoundError:
            return None
        except OSError:
            raise ValueError("R1_REVIEW_FILE_UNUSABLE") from None
        with os.fdopen(leaf, "rb") as f:
            fs = os.fstat(f.fileno())
            if not stat.S_ISREG(fs.st_mode) or stat.S_IMODE(fs.st_mode) != 0o600 or fs.st_uid != os.getuid() or fs.st_size > CAP:
                raise ValueError("R1_REVIEW_FILE_UNUSABLE")
            raw = f.read(CAP + 1)
            after = os.fstat(f.fileno())
            if len(raw) > CAP or (fs.st_size, fs.st_mtime_ns, fs.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                raise ValueError("R1_REVIEW_FILE_UNUSABLE")
            return raw
    finally:
        os.close(fd)


def strip_frames(value):
    if isinstance(value, dict):
        return {k: strip_frames(v) for k, v in value.items() if k not in
                {"frames", "partner_frames", "frame_indices", "frame_index", "timestamps", "timestamp", "partner_frame_indices", "partner_timestamps"}}
    if isinstance(value, list):
        return [strip_frames(v) for v in value]
    return value


def reasoning(row):
    if "reasoning" in row:
        value = row["reasoning"]
        return value if isinstance(value, str) else ""
    value = row.get("target", row.get("suffix", ""))
    if not isinstance(value, str) or "<think>" not in value or "</think>" not in value:
        return ""
    return value.split("<think>", 1)[1].split("</think>", 1)[0]


def form(row):
    # routing.form is copied from the canonical trace producer; answer_form
    # selects routed/direct encoding in Rows.get. Report absence explicitly.
    for field, value in (("routing.form", row.get("routing", {}).get("form")),
                         ("form", row.get("form")), ("answer_form", row.get("answer_form"))):
        if value is not None:
            return field, str(value)
    return "not_recorded", "not_recorded"


def evidence(cfg, rooms, live):
    from student_pilot.carrier_c1_run import Rows
    from student_pilot.p3_provenance import pinned
    import torch
    torch.set_num_threads(8)
    if torch.get_num_interop_threads() != 1:
        torch.set_num_interop_threads(1)
    receipt = load(pinned(cfg["preparation"]))
    reader = Rows(receipt, None)
    payloads = {}
    counts = {}
    started = time.monotonic()
    try:
        for stream in STREAMS:
            total = reader.count(stream)
            if stream in reader.mixes:
                ids = [tuple(v) for v in reader.mixes[stream].order]
                connections = {str(k): v.conn for k, v in enumerate(reader.mixes[stream].sources)}
            else:
                ids = list(reader.indices.get(stream, range(total)))
                connections = {"0": reader.connections[stream]}
            if len(ids) != total or len(set(ids)) != total or total < 40:
                raise ValueError("R1_REVIEW_STORE_UNUSABLE")
            selected = random.Random(20261119).sample(sorted(ids), 40)
            wanted = set(selected)
            examples = {}
            types = Counter()
            forms = Counter()
            empty = 0
            databases = []
            for key, connection in connections.items():
                database = Path(next(r[2] for r in connection.execute("PRAGMA database_list") if r[1] == "main"))
                databases.append(dict(source=key, path=str(database), sha256=sha(database), bytes=database.stat().st_size))
            for offset, row_id in enumerate(ids):
                row, _ = reader.row(stream, offset)
                types[str(row.get("routing", {}).get("question_type", row.get("question_type", "not_recorded")))] += 1
                field, value = form(row)
                forms[(field, value)] += 1
                empty += not bool(reasoning(row).strip())
                if row_id in wanted:
                    examples[row_id] = dict(row_id=row_id, row=strip_frames(row))
            counts[stream] = dict(rows=total, answer_only=empty)
            payloads[NAMES[stream]] = encoded(dict(stream=stream, databases=databases, admitted_rows=total,
                question_types=dict(sorted(types.items())), answer_only=empty,
                reasoning_field="reasoning when present; otherwise target/suffix <think> body; missing body counts empty",
                trace_forms=[dict(field=f, value=v, rows=n) for (f, v), n in sorted(forms.items())],
                trace_form_basis="routing.form is canonical producer form; form is the stored trace form; answer_form selects native encoding; absent fields are not_recorded",
                sample_seed=20261119, sample=[examples[i] for i in selected]))
    finally:
        reader.close()
    raw = Path(rooms).read_bytes()
    payloads["e4.json"] = raw
    payloads["e5.json"] = encoded(dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw)))
    if sum(map(len, payloads.values())) >= CAP:
        raise ValueError("R1_REVIEW_EVIDENCE_TOO_LARGE")
    for name, raw in payloads.items():
        put(live / name, raw)
    if any(v["answer_only"] for v in counts.values()):
        raise ValueError("R1_ANSWER_ONLY_ROWS")
    return dict(counts=counts, bytes=sum(map(len, payloads.values())), seconds=time.monotonic() - started)


def sync_preparation(cfg, root, name):
    from student_pilot.p3_provenance import pinned
    receipt = load(pinned(cfg["preparation"]))
    receipt["r1_training"] = cfg["r1_training"]
    cfg["preparation"] = write(root / name, receipt)


def run(kit, root, config, job, *, interval=30):
    live, review_path = location(kit, root, job)
    value = None
    def interrupted(signum, frame):
        raise ValueError("R1_REVIEW_INTERRUPTED")
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGUSR1, interrupted)
    try:
        if config.stat().st_size > V_CAP:
            raise ValueError("R1_REVIEW_CONFIG_TOO_LARGE")
        cfg = load(config)
        sys.path.insert(0, str(root / "p/s"))
        from student_pilot.carrier_c1_run import identity
        value = identity(cfg)
        raw = config.read_bytes()
        if len(raw) > V_CAP:
            raise ValueError("R1_REVIEW_CONFIG_TOO_LARGE")
        put(live / "v.json", raw)
        put(live / "identity.txt", (value + "\n").encode())
        evidence(cfg, root / "rooms.json", live)
        bound = load(kit / "k/a.json")["review_wait_seconds"]
        if type(bound) is not int or not 0 < bound <= 7200:
            raise ValueError("R1_REVIEW_FILE_UNUSABLE")
        now = datetime.now(timezone.utc)
        deadline = time.monotonic() + bound
        put(live / "WAITING_REVIEW.json", encoded(dict(utc=now.isoformat(), identity=value,
            v_sha256=hashlib.sha256(raw).hexdigest(), deadline_utc=(now + timedelta(seconds=bound)).isoformat())))
        while True:
            if time.monotonic() >= deadline:
                raise ValueError("R1_REVIEW_TIMEOUT")
            # Recheck all path ancestors on every poll.
            location(kit, root, job)
            review_raw = receipt_bytes(review_path)
            if review_raw is not None:
                try:
                    review = json.loads(review_raw)
                except (ValueError, UnicodeError):
                    raise ValueError("R1_REVIEW_FILE_UNUSABLE") from None
                if not isinstance(review, dict) or set(review) - {"verdict", "config_identity", "evidence"} or ("evidence" in review and not isinstance(review["evidence"], dict)):
                    raise ValueError("R1_REVIEW_FILE_UNUSABLE")
                if review.get("verdict") != "PASS":
                    raise ValueError("R1_REVIEW_NOT_PASS")
                if review.get("config_identity") != value:
                    raise ValueError("R1_REVIEW_IDENTITY_DIFFERS")
                if sha(config) != hashlib.sha256(raw).hexdigest():
                    raise ValueError("R1_REVIEW_IDENTITY_DIFFERS")
                pin = root / "p/rv.json"
                put(pin, review_raw)
                review_sha = hashlib.sha256(review_raw).hexdigest()
                cfg["r1_training"]["review"] = dict(path=str(pin), sha256=review_sha)
                sync_preparation(cfg, root / "p", "pr.json")
                if identity(cfg) != value:
                    raise ValueError("R1_REVIEW_IDENTITY_DIFFERS")
                put(config, encoded(cfg))
                put(live / "REVIEW_ACCEPTED.json", encoded(dict(utc=stamp(), identity=value, review_sha256=review_sha)))
                return 0
            time.sleep(min(interval, max(0, deadline - time.monotonic())))
    except (ValueError, OSError, KeyError, TypeError) as error:
        code = str(error) if str(error).startswith("R1_") else "R1_REVIEW_FILE_UNUSABLE"
        put(live / "REVIEW_REFUSED.json", encoded(dict(utc=stamp(), identity=value, refusal=code)))
        print(code, flush=True)
        return 1


def main():
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    limit = min(v for v in (soft, hard, 19_000_000_000) if v > 0)
    resource.setrlimit(resource.RLIMIT_AS, (limit, hard))
    kit = Path(__file__).resolve().parents[1]
    seal(kit)
    if len(sys.argv) == 4 and sys.argv[1] == "--live":
        print(location(kit, Path(sys.argv[2]), sys.argv[3])[0])
        return 0
    if len(sys.argv) != 4:
        raise ValueError("R1_REVIEW_FILE_UNUSABLE")
    return run(kit, Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])


if __name__ == "__main__":
    raise SystemExit(main())
