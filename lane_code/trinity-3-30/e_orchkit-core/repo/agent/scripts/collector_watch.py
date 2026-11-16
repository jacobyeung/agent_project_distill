#!/usr/bin/env python
"""Collector watcher for the r1313 GT teacher run (REQ-20260917-232).

Reads only NFS marker files written by the watchdog and monitor that run on
trinity-3-23, so it needs no ssh. It prints one status line per check and
exits when something needs the orchestrator's attention, which fires a
background-task notification. Re-arm it after acting.

Exit codes
  1  regression: stale watchdog/monitor health, BLOCKED.json, controller or
     workers absent for three consecutive checks, or no new terminal for
     --stall-minutes
  2  watchdog event that needs a look (controller_exit, lock_stepdown,
     rate_limit_stepdown, watchdog_stopped)
  3  ramp step observed (resize_finished with a new worker count) - status note
  4  target reached (accepted >= --target from STATUS_v5.md)

Usage: python -B agent/scripts/collector_watch.py [--interval 60] [--stall-minutes 20]
Never deletes, writes, or signals anything.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import time

DATA = "/data2/jjyeung/agent_project_data/vsi_distill_training_20260917"
ORCH = "/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918"
TERMINALS = f"{DATA}/collection_gt_r1313/terminals"
RELAUNCH = f"{DATA}/runtime_control/gt_teacher_r1313/RELAUNCH_20260918"
OUT = f"{ORCH}/codex_r1313_watchdog_v5/out"
WD = os.environ.get("WATCHDOG_OUT", OUT)
WATCHDOG_HEALTH = f"{WD}/WATCHDOG_HEALTH.json"
MONITOR_HEALTH = f"{OUT}/HEALTH_v5.json"
EVENTS = f"{WD}/WATCHDOG_EVENTS.jsonl"
BLOCKED = f"{WD}/BLOCKED.json"
STATUS = f"{RELAUNCH}/STATUS_v5.md"
ALARM_EVENTS = {"controller_exit", "lock_stepdown", "rate_limit_stepdown", "watchdog_stopped"}


def now():
    return dt.datetime.now(dt.timezone.utc)


def age_minutes(path):
    try:
        return (time.time() - os.stat(path).st_mtime) / 60.0
    except OSError:
        return float("inf")


def load_json(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def count_terminals():
    try:
        return sum(1 for name in os.listdir(TERMINALS) if not name.startswith("."))
    except OSError:
        return -1


def event_count():
    try:
        with open(EVENTS, "rb") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


def new_events(since_line):
    out = []
    try:
        with open(EVENTS) as fh:
            for i, line in enumerate(fh):
                if i < since_line:
                    continue
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
    except OSError:
        pass
    return out


def accepted_from_status():
    try:
        text = open(STATUS).read()
    except OSError:
        return None, None
    m = re.search(r"accepted (\d+);", text)
    q = re.search(r"Questions/hour \(10/30/60 minutes\): (\{[^}]*\})", text)
    return (int(m.group(1)) if m else None), (q.group(1) if q else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--stall-minutes", type=int, default=20)
    ap.add_argument("--stale-minutes", type=int, default=6)
    ap.add_argument("--target", type=int, default=20000)
    ap.add_argument("--quiet", action="store_true", help="print a status line every 10 checks instead of every check")
    ap.add_argument("--no-exit-on-alarm", action="store_true", help="print alarm-class watchdog events and keep running")
    args = ap.parse_args()
    checks = 0

    seen_events = event_count()
    start_terms = count_terminals()
    last_terms = start_terms
    last_new_term = time.time()
    missing_controller = 0
    missing_workers = 0
    relaunch_checks = 0
    start = time.time()
    last_workers = None
    print(f"{now():%FT%TZ} watcher start terminals={start_terms} events_seen={seen_events}", flush=True)

    while True:
        time.sleep(args.interval)
        terms = count_terminals()
        if terms > last_terms:
            last_new_term = time.time()
        last_terms = terms
        wh = load_json(WATCHDOG_HEALTH) or {}
        mh = load_json(MONITOR_HEALTH) or {}
        controllers = len(mh.get("controllers", []) or [])
        workers = len(mh.get("workers", []) or [])
        phase = wh.get("phase")
        target = wh.get("target")
        wh_age = age_minutes(WATCHDOG_HEALTH)
        mh_age = age_minutes(MONITOR_HEALTH)
        elapsed_h = (time.time() - start) / 3600.0
        rate = (terms - start_terms) / elapsed_h if elapsed_h > 0.02 else float("nan")
        checks += 1
        if not args.quiet or checks % 10 == 0:
            print(
                f"{now():%FT%TZ} terminals={terms} (+{terms - start_terms}, {rate:.0f}/h) "
                f"controllers={controllers} workers={workers} target={target} phase={phase} "
                f"wd_age={wh_age:.1f}m mon_age={mh_age:.1f}m",
                flush=True,
            )

        if os.path.exists(BLOCKED):
            print(f"REGRESSION: BLOCKED.json present: {open(BLOCKED).read()[:400]}", flush=True)
            sys.exit(1)
        if wh_age > args.stale_minutes or mh_age > args.stale_minutes:
            print(f"REGRESSION: stale health files wd_age={wh_age:.1f}m mon_age={mh_age:.1f}m", flush=True)
            sys.exit(1)
        # The watchdog's own recovery (grace -> prepare_launch -> running) legitimately
        # has zero controllers and workers for a few minutes; only alarm if it drags on.
        relaunching = phase in ("grace", "prepare_launch")
        if relaunching:
            relaunch_checks = relaunch_checks + 1
            missing_controller = 0
            missing_workers = 0
            if relaunch_checks >= 15:
                print(f"REGRESSION: watchdog stuck in phase {phase} for {relaunch_checks} checks", flush=True)
                sys.exit(1)
        else:
            relaunch_checks = 0
            missing_controller = missing_controller + 1 if controllers == 0 else 0
            missing_workers = missing_workers + 1 if workers == 0 else 0
            # A freshly launched controller validates assets over NFS for several minutes
            # before its first worker appears, so tolerate a longer worker gap.
            if missing_controller >= 3 or missing_workers >= 8:
                print(f"REGRESSION: controllers={controllers} workers={workers} (controller gap>=3 or worker gap>=8 checks)", flush=True)
                sys.exit(1)
        if (time.time() - last_new_term) / 60.0 > args.stall_minutes:
            print(f"REGRESSION: no new terminal for {args.stall_minutes} min", flush=True)
            sys.exit(1)

        events = new_events(seen_events)
        seen_events += len(events)
        for ev in events:
            kind = ev.get("event")
            if kind in ("orphan_grace_check", "orphan_grace_started"):
                continue
            print(f"EVENT {ev.get('utc')} {kind} {json.dumps({k: v for k, v in ev.items() if k not in ('utc', 'event', 'identity', 'receipt')})[:300]}", flush=True)
            if kind in ALARM_EVENTS and not args.no_exit_on_alarm:
                sys.exit(2)
            if kind == "resize_finished" and ev.get("rc") == 0 and ev.get("workers") != last_workers:
                last_workers = ev.get("workers")
                if ev.get("workers") not in (None, 16) or elapsed_h > 0.1:
                    print(f"RAMP: workers now {ev.get('workers')}", flush=True)
                    if not args.no_exit_on_alarm:
                        sys.exit(3)

        accepted, qph = accepted_from_status()
        if accepted is not None and int(time.time()) % 600 < args.interval:
            print(f"STATUS accepted={accepted} questions/hour={qph}", flush=True)
        if accepted is not None and accepted >= args.target:
            print(f"TARGET REACHED accepted={accepted}", flush=True)
            sys.exit(4)


if __name__ == "__main__":
    main()
