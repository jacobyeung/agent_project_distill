#!/usr/bin/env python
"""Operator attestation of predecessor worker exits on an unreachable host.

The tolerant pool refuses to start while heartbeat or claim records from a
foreign host lack exit receipts (pool_harness/state.py require_drained). When
that host has crashed and cannot be inspected, the operator attests the exits
here. The script only creates files that do not exist yet (exclusive create),
never modifies or removes anything, and records the evidence next to the
receipts in OPERATOR_DECISION.md.

Usage:
  python -B tools/attest_foreign_host_exits.py --pool <pool_root> --host trinity-1-8 \
      --evidence "<one line>" [--evidence "<another>"] [--write]
Without --write it prints what it would do.
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

SCHEMA = "resizable-pool-exit-v1"


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", required=True)
    ap.add_argument("--host", required=True, help="the unreachable predecessor host")
    ap.add_argument("--evidence", action="append", default=[], help="one line of evidence; repeatable")
    ap.add_argument("--return-code", type=int, default=-9)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    pool = Path(args.pool)
    receipts = pool / "exit_receipts"
    workers = {}
    for directory in ("worker_starts", "heartbeats", "claims"):
        d = pool / directory
        if not d.is_dir():
            continue
        for p in d.glob("*.json"):
            rec = read_json(p)
            if not isinstance(rec, dict) or rec.get("host") != args.host:
                continue
            w = rec.get("worker_id")
            if not w:
                continue
            info = workers.setdefault(w, {"records": [], "last_wall_ns": 0, "pids": set()})
            info["records"].append(f"{directory}/{p.name}")
            info["last_wall_ns"] = max(info["last_wall_ns"], rec.get("wall_time_ns") or 0)
            if isinstance(rec.get("pid"), int):
                info["pids"].add(rec["pid"])

    now = dt.datetime.now(dt.timezone.utc)
    todo = []
    for w, info in sorted(workers.items()):
        if (receipts / f"{w}.json").is_file():
            continue
        m = re.search(r"-(\d+)-g\d+$", w)
        slot = int(m.group(1)) if m else -1
        last = dt.datetime.fromtimestamp(info["last_wall_ns"] / 1e9, dt.timezone.utc) if info["last_wall_ns"] else None
        todo.append((w, slot, last, info))
        last_text = f"{last:%FT%TZ}" if last else "unknown"
        print(f"{'WRITE' if args.write else 'DRY'} {w} slot={slot} last_activity={last_text} "
              f"records={len(info['records'])} pids={sorted(info['pids'])}")

    print(f"{len(workers)} {args.host} workers found, {len(todo)} lacking exit receipts")
    if not args.write or not todo:
        return 0

    decision = pool.parent / "OPERATOR_DECISION_foreign_host_exits.md"
    lines = [f"# Operator attestation of {args.host} worker exits ({now:%FT%TZ})", "",
             "Evidence:"] + [f"- {e}" for e in args.evidence] + ["", "Receipts written (exclusive create, no modification of existing files):"]
    written = 0
    for w, slot, last, info in todo:
        receipt = {
            "census": {"operator_attestation": True, "attested_utc": now.isoformat(),
                       "last_recorded_activity_utc": last.isoformat() if last else None,
                       "records": sorted(info["records"]), "recorded_pids": sorted(info["pids"]), "host": args.host},
            "reason": "worker_error",
            "return_code": args.return_code,
            "schema": SCHEMA,
            "slot": slot,
            "worker_id": w,
            "operator_attestation": {"evidence": args.evidence, "by": "distillation orchestrator (REQ-20260917-232)", "utc": now.isoformat()},
        }
        path = receipts / f"{w}.json"
        try:
            with path.open("x") as fh:
                fh.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        except FileExistsError:
            print(f"SKIP existing {path.name}")
            continue
        written += 1
        lines.append(f"- {path.name} slot={slot} last_activity={last.isoformat() if last else 'unknown'}")
    with decision.open("a") as fh:
        fh.write("\n".join(lines) + "\n\n")
    print(f"wrote {written} receipts; decision recorded at {decision}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
