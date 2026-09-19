"""Attest worker death on this host; pool writers must be trusted."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys

from pool_harness.atomicfs import (
    StateError, canonical_bytes, publish_json_exclusive, read_json, safe_component,
)

SCHEMA = "pool-host-drain-attestation-v1"
REMOTE_SCHEMA = "pool-harness-remote-drain-attestation-v1"
RECORD_DIRS = ("worker_starts", "heartbeats", "claims")
SNAPSHOT_FIELDS = {"utc", "command", "stdout", "rc", "status"}
REMOTE_ASSERTIONS = {"evidence_status_pass", "evidence_hostname_matches",
                     "evidence_no_matches", "newest_record_before_evidence"}


def worker_identity(row):
    worker = safe_component(row.get("worker_id"), "worker_id")
    pid = row.get("pid")
    if type(pid) is not int or pid <= 0:
        raise StateError("drain attestation lacks a valid PID")
    ticks = row.get("start_ticks")
    if ticks is not None:
        if not (type(ticks) is int and ticks >= 0 or
                isinstance(ticks, str) and re.fullmatch(r"[0-9]+", ticks)):
            raise StateError("drain attestation has invalid start_ticks")
        ticks = str(int(ticks))
    return worker, pid, ticks


def verified_ns(value):
    if not isinstance(value, str):
        raise StateError("drain attestation lacks a UTC verified_at")
    try:
        stamp = datetime.fromisoformat(value)
    except ValueError as exc:
        raise StateError("drain attestation has invalid verified_at") from exc
    if stamp.utcoffset() != timedelta(0):
        raise StateError("drain attestation verified_at must be UTC")
    delta = stamp - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return ((delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds) * 1000


def load_snapshot_evidence(path, host):
    path = path.resolve()
    payload = path.read_bytes()
    snapshot = json.loads(payload)
    if not isinstance(snapshot, dict) or not SNAPSHOT_FIELDS <= set(snapshot):
        raise StateError("remote drain snapshot schema mismatch")
    if snapshot["status"] != "PASS" or type(snapshot["rc"]) is not int or snapshot["rc"] != 0:
        raise StateError("remote drain evidence did not pass")
    verified_ns(snapshot["utc"])
    stdout, command = snapshot["stdout"], snapshot["command"]
    if not isinstance(stdout, str) or not stdout.splitlines() or stdout.splitlines()[0] != host:
        raise StateError("remote drain evidence hostname mismatch")
    if stdout.splitlines() != [host, "pgrep_rc=1"]:
        raise StateError("remote drain evidence does not show only a no-match result")
    if (not isinstance(command, list) or not command
            or not all(isinstance(arg, str) and arg for arg in command)):
        raise StateError("remote drain evidence command schema mismatch")
    probe = re.match(
        r'''hostname\s*;\s*pgrep\s+-(?:af|fa)\s+(['"])([^'"\n]+)\1\s*;\s*'''
        r"pgrep_rc=\$\?\s*;\s*echo\s+pgrep_rc=\$pgrep_rc(?:\s*;|$)", command[-1].strip(),
    )
    patterns = set(probe.group(2).replace("[w]", "w").replace("[c]", "c").replace(r"\.", ".").split("|")) if probe else set()
    if not (patterns & {"collector/collect.py", "collect.py"}
            and patterns & {"watchdog_v5_remediation", "watchdog"}):
        raise StateError("remote drain evidence lacks a collector/watchdog pgrep result")
    return {"path": str(path), "sha256": hashlib.sha256(payload).hexdigest(),
            **{key: snapshot[key] for key in SNAPSHOT_FIELDS}}


def validate_attestation(value):
    remote = isinstance(value, dict) and value.get("schema") == REMOTE_SCHEMA
    fields = {"schema", "host", "verified_at", "verifier", "workers",
              "record_counts", "package_commit"}
    if remote:
        fields |= {"evidence", "assertions"}
    if (not isinstance(value, dict) or set(value) != fields
            or value["schema"] != (REMOTE_SCHEMA if remote else SCHEMA)):
        raise StateError("drain attestation schema mismatch")
    safe_component(value["host"], "host")
    stamp = verified_ns(value["verified_at"])
    verifier = value["verifier"]
    verifier_fields = {"pid", "uid", "argv", "python"} | ({"host"} if remote else set())
    if (not isinstance(verifier, dict) or set(verifier) != verifier_fields
            or type(verifier["pid"]) is not int or verifier["pid"] <= 0
            or type(verifier["uid"]) is not int or verifier["uid"] < 0
            or not isinstance(verifier["argv"], list) or not verifier["argv"]
            or not all(isinstance(arg, str) for arg in verifier["argv"])
            or not isinstance(verifier["python"], str) or not verifier["python"]):
        raise StateError("drain attestation verifier schema mismatch")
    if remote:
        safe_component(verifier["host"], "verifier host")
    counts = value["record_counts"]
    if (not isinstance(counts, dict) or set(counts) != set(RECORD_DIRS)
            or any(type(n) is not int or n < 0 for n in counts.values())):
        raise StateError("drain attestation record_counts schema mismatch")
    if not isinstance(value["package_commit"], str) or not re.fullmatch(r"[0-9a-f]{40}", value["package_commit"]):
        raise StateError("drain attestation package_commit schema mismatch")
    if not isinstance(value["workers"], list):
        raise StateError("drain attestation workers schema mismatch")
    identities = set()
    for row in value["workers"]:
        if (not isinstance(row, dict) or set(row) != {"worker_id", "pid", "start_ticks", "status"}
                or row["status"] != ("absent_in_evidence" if remote else "dead")):
            raise StateError("drain attestation worker schema mismatch")
        identity = worker_identity(row)
        if identity in identities:
            raise StateError("drain attestation repeats a worker identity")
        identities.add(identity)
    if len(identities) > sum(counts.values()):
        raise StateError("drain attestation census is inconsistent")
    if remote:
        assertions, evidence = value["assertions"], value["evidence"]
        if (not identities or not isinstance(assertions, dict) or set(assertions) != REMOTE_ASSERTIONS
                or any(flag is not True for flag in assertions.values())):
            raise StateError("remote drain attestation assertions or census mismatch")
        if (not isinstance(evidence, dict) or set(evidence) != SNAPSHOT_FIELDS | {"path", "sha256"}
                or not isinstance(evidence["path"], str) or not Path(evidence["path"]).is_absolute()
                or not isinstance(evidence["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", evidence["sha256"])
                or type(evidence["rc"]) is not int):
            raise StateError("remote drain attestation evidence schema mismatch")
        if load_snapshot_evidence(Path(evidence["path"]), value["host"]) != evidence:
            raise StateError("remote drain evidence snapshot digest or content mismatch")
        evidence_stamp = verified_ns(evidence["utc"])
        if evidence_stamp > stamp:
            raise StateError("remote drain evidence is later than verification")
        stamp = evidence_stamp
    return stamp, identities


def process_alive(pid, start_ticks):
    try:
        stat = (Path("/proc") / str(pid) / "stat").read_text()
    except FileNotFoundError:
        return False
    # comm can contain spaces and parentheses; fields after its final ')' start at state.
    fields = stat[stat.rindex(")") + 2:].split()
    if len(fields) < 20 or not fields[19].isdigit():
        raise StateError(f"cannot parse /proc/{pid}/stat")
    return fields[0] != "Z" and (start_ticks is None or fields[19] == start_ticks)


def attest(pool):
    host = safe_component(socket.gethostname(), "host")
    # Refuse an unavailable procfs instead of treating all missing entries as dead.
    if not process_alive(os.getpid(), None):
        raise StateError("cannot verify this host's procfs")
    identities = set()
    counts = dict.fromkeys(RECORD_DIRS, 0)
    for directory in RECORD_DIRS:
        for path in sorted((pool / directory).glob("*.json")):
            record = read_json(path)
            if not isinstance(record, dict):
                raise StateError(f"invalid worker record: {path}")
            if record.get("host") == host:
                identities.add(worker_identity(record))
                counts[directory] += 1
    stamp = datetime.now(timezone.utc).isoformat()
    workers, live = [], []
    for worker, pid, ticks in sorted(identities, key=lambda item: (item[0], item[1], item[2] or "")):
        if process_alive(pid, ticks):
            live.append({"worker_id": worker, "pid": pid, "start_ticks": ticks})
        workers.append({"worker_id": worker, "pid": pid, "start_ticks": ticks, "status": "dead"})
    if live:
        raise StateError("live workers prevent drain attestation: " + json.dumps(live, sort_keys=True))
    commit = subprocess.check_output(
        ["git", "-C", str(Path(__file__).resolve().parent), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    result = {"schema": SCHEMA, "host": host, "verified_at": stamp,
              "verifier": {"pid": os.getpid(), "uid": os.getuid(),
                           "argv": sys.argv, "python": sys.executable},
              "workers": workers, "record_counts": counts, "package_commit": commit}
    validate_attestation(result)
    return result


def attest_remote(pool, host, evidence_path, package_commit):
    host = safe_component(host, "host")
    evidence = load_snapshot_evidence(evidence_path, host)
    evidence_stamp = verified_ns(evidence["utc"])
    identities = set()
    counts = dict.fromkeys(RECORD_DIRS, 0)
    for directory in RECORD_DIRS:
        for path in sorted((pool / directory).glob("*.json")):
            record = read_json(path)
            if not isinstance(record, dict):
                raise StateError(f"invalid worker record: {path}")
            if record.get("host") == host:
                times = [record[key] for key in ("wall_time_ns", "claimed_wall_time_ns") if key in record]
                if any(type(stamp) is not int or stamp < 0 for stamp in times):
                    raise StateError("predecessor record has an invalid timestamp")
                if max([path.stat().st_mtime_ns, *times]) >= evidence_stamp:
                    raise StateError(f"predecessor record is not older than remote evidence: {path}")
                identities.add(worker_identity(record))
                counts[directory] += 1
    if not identities:
        raise StateError("remote drain attestation has no covered worker records")
    workers = [{"worker_id": worker, "pid": pid, "start_ticks": ticks, "status": "absent_in_evidence"}
               for worker, pid, ticks in sorted(identities, key=lambda item: (item[0], item[1], item[2] or ""))]
    result = {"schema": REMOTE_SCHEMA, "host": host, "verified_at": datetime.now(timezone.utc).isoformat(),
              "verifier": {"host": socket.gethostname(), "pid": os.getpid(), "uid": os.getuid(),
                           "argv": sys.argv, "python": sys.executable},
              "evidence": evidence, "workers": workers, "record_counts": counts,
              "package_commit": package_commit, "assertions": dict.fromkeys(REMOTE_ASSERTIONS, True)}
    validate_attestation(result)
    return result


def load_attestations(pool):
    result = []
    for path in sorted((pool / "host_attestations").glob("*.json")):
        try:
            payload = path.read_bytes()
            value = json.loads(payload)
            stamp, identities = validate_attestation(value)
        except (OSError, ValueError, StateError):
            # Invalid evidence never authorizes a foreign-host predecessor.
            continue
        result.append((path, value, stamp, identities, hashlib.sha256(payload).hexdigest()))
    return result


def covering_attestation(attestations, record, path):
    times = [record[key] for key in ("wall_time_ns", "claimed_wall_time_ns") if key in record]
    if any(type(stamp) is not int or stamp < 0 for stamp in times):
        raise StateError("predecessor record has an invalid timestamp")
    stamp = max(times) if times else path.stat().st_mtime_ns
    identity = worker_identity(record)
    for att_path, value, att_stamp, identities, digest in attestations:
        if value["host"] == record.get("host") and att_stamp > stamp and identity in identities:
            remote = value["schema"] == REMOTE_SCHEMA
            if remote and att_stamp <= path.stat().st_mtime_ns:
                continue
            covered = {"attestation": str(att_path), "sha256": digest, "host": value["host"],
                       "verified_at": value["verified_at"], "workers": []}
            if remote:
                covered.update(schema=REMOTE_SCHEMA, evidence_utc=value["evidence"]["utc"],
                               verifier={"host": value["verifier"]["host"]})
            return covered
    return None


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    remote = bool(argv and argv[0] == "remote")
    if remote:
        argv = argv[1:]
    parser = argparse.ArgumentParser(
        description="Attest predecessor drainage from a recorded process snapshot." if remote else __doc__,
        epilog="Use the remote subcommand for recorded evidence from another host.",
    )
    parser.add_argument("--pool", type=Path, required=True)
    parser.add_argument("--write", action="store_true", help="publish exclusively under pool/host_attestations")
    if remote:
        parser.add_argument("--host", required=True)
        parser.add_argument("--evidence", type=Path, required=True)
        parser.add_argument("--package-commit", required=True)
    args = parser.parse_args(argv)
    try:
        if not args.pool.is_dir():
            raise StateError(f"pool directory does not exist: {args.pool}")
        value = attest_remote(args.pool, args.host, args.evidence, args.package_commit) if remote else attest(args.pool)
        if args.write:
            separator = "__remote__" if remote else "__"
            path = args.pool / "host_attestations" / f"{value['host']}{separator}{value['verified_at']}.json"
            publish_json_exclusive(path, value)
        sys.stdout.write(canonical_bytes(value).decode("utf-8"))
    except (OSError, ValueError, StateError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"drain attestation refused: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
