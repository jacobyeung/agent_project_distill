#!/bin/bash
# Orchestrator tick digest. Local commands only (no ssh, no git); state in /scratch/jjyeung/orch_n30/.tick/ on this node.
# Usage: tick.sh [--all] [--peek]
#   (a) event files new since the last tick (path + first 10 lines, 120 lines in all; events not shown stay new)
#   (b) lanes of LANES.txt: process running (checked on this node only), STATUS.md age (events/<lane>/STATUS.md,
#       or events/<lane without its trailing number>/ when the numbered folder does not exist)
#       default: lanes with a live local process or STATUS.md younger than 24 h; --all prints every lane
#   (c) this node: free /scratch, load, available RAM   (d) line 4 of the IO governor's STATE.md
#   --peek shows new events without marking them seen.
# Separate from evwait.sh: never reads or writes tools/seen.txt.
export B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
export TICK_STATE=${TICK_STATE:-/scratch/jjyeung/orch_n30/.tick}
export GOV_STATE=${GOV_STATE:-/data3/jjyeung/orch_n13_20261026/io_governor/STATE.md}
mkdir -p "$TICK_STATE" || exit 3
exec 9>"$TICK_STATE/lock"; flock -w 10 9 || { echo "tick.sh: another tick holds $TICK_STATE/lock" >&2; exit 4; }
PS_SNAPSHOT=$(ps -eo pid=,args= 2>/dev/null) OMP_NUM_THREADS=1 exec /usr/bin/python3 - "$@" <<'PY'
import os, sys, re, time, glob, subprocess
B = os.environ["B"]; ST = os.environ["TICK_STATE"]; GOV = os.environ["GOV_STATE"]
args = sys.argv[1:]; ALL = "--all" in args; PEEK = "--peek" in args
now = time.time(); host = os.uname()[1].split(".")[0]
SEEN = os.path.join(ST, "seen.txt"); LAST = os.path.join(ST, "last_tick")
stamp = re.compile(r"^\d{8}T\d{4,6}Z_")
first_run = not os.path.exists(SEEN)
seen = set()
if not first_run:
    with open(SEEN) as f: seen = set(l.rstrip("\n") for l in f)
last = None
if os.path.exists(LAST):
    with open(LAST) as f: last = f.read().strip()
print("TICK %s on %s (previous tick %s)" % (time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(now)), host, last or "none"))

# (a) new event files: stamp-named regular files directly under events/<lane>/
evs = []
for d in sorted(os.listdir(os.path.join(B, "events"))):
    p = os.path.join(B, "events", d)
    try: names = os.listdir(p)
    except OSError: continue
    for n in names:
        if stamp.match(n): evs.append((n, d + "/" + n))
evs.sort()
if first_run:
    # first tick: everything older than one hour counts as seen
    base = [r for _, r in evs if os.path.getmtime(os.path.join(B, "events", r)) < now - 3600]
    seen.update(base)
new = [r for _, r in evs if r not in seen]
print("\n(a) NEW EVENTS: %d" % len(new))
budget = 120; shown = []
for r in new:
    fp = os.path.join(B, "events", r)
    try:
        with open(fp, errors="replace") as f: head = [l.rstrip("\n")[:220] for _, l in zip(range(10), f)]
    except OSError: head = ["<unreadable>"]
    need = 1 + len(head)
    if need > budget: break
    print("== " + fp); [print("   " + l) for l in head]; budget -= need; shown.append(r)
if len(shown) < len(new):
    print("+ %d more new events not shown; they stay new for the next tick" % (len(new) - len(shown)))

# (b) lanes
lanes = []; byname = {}
with open(os.path.join(B, "tools", "LANES.txt")) as f:
    for l in f:
        parts = l.strip().split("|")
        if len(parts) != 3: continue
        if parts[0] in byname: lanes.remove(byname[parts[0]])
        byname[parts[0]] = tuple(parts); lanes.append(byname[parts[0]])
ps = os.environ.get("PS_SNAPSHOT", "").splitlines()
def running(lane, brief):
    pat_c = "distillation lane %s on node" % lane
    for l in ps:
        if ("devin" in l and ("--prompt-file " + brief) in l) or ("claude" in l and pat_c in l) or ("codex" in l and ("--label " + lane + " ") in l + " "):
            return l.split(None, 1)[0]
    return None
rows = []; quiet = 0
for lane, brief, lhost in lanes:
    ed = lane
    if not os.path.isdir(os.path.join(B, "events", ed)): ed = re.sub(r"_?\d+$", "", lane)
    sp = os.path.join(B, "events", ed, "STATUS.md")
    try: age = (now - os.path.getmtime(sp)) / 3600.0
    except OSError: age = None
    if lhost == host:
        pid = running(lane, brief); proc = ("run pid " + pid) if pid else "no proc"
    else:
        proc = "remote"
    active = proc.startswith("run") or (age is not None and age < 24)
    if ALL or active: rows.append((lane, lhost, proc, "-" if age is None else "%.1fh" % age))
    else: quiet += 1
print("\n(b) LANES (process checked on %s only; STATUS.md age from events/<lane>/)" % host)
w = max([len(r[0]) for r in rows] + [4])
for r in rows: print("  %-*s %-13s %-14s status %s" % (w, r[0], r[1], r[2], r[3]))
if quiet: print("  + %d lanes with no local process and STATUS.md older than 24 h (--all lists them)" % quiet)

# (c) node
def sh(c):
    try: return subprocess.check_output(c, shell=True, stderr=subprocess.STDOUT, timeout=4).decode(errors="replace").strip()
    except Exception as e: return "<%s failed: %s>" % (c, e)
print("\n(c) NODE %s" % host)
print("  /scratch: " + sh("df -h --output=avail,size,pcent /scratch | tail -n 1"))
print("  load: " + sh("cut -d' ' -f1-3 /proc/loadavg") + " (%s cores)" % os.cpu_count())
print("  RAM available: " + sh("free -g | awk '/^Mem:/{print $7\" GB of \"$2\" GB\"}'"))

# (d) governor
try:
    with open(GOV) as f: l4 = [l.rstrip("\n") for _, l in zip(range(4), f)]
    print("\n(d) GOVERNOR " + (l4[3] if len(l4) >= 4 else "<STATE.md has fewer than 4 lines>"))
except OSError as e:
    print("\n(d) GOVERNOR <unreadable: %s>" % e)

if not PEEK:
    seen.update(shown)
    tmp = SEEN + ".tmp"
    with open(tmp, "w") as f: f.write("".join(s + "\n" for s in sorted(seen)))
    os.replace(tmp, SEEN)
    with open(LAST, "w") as f: f.write(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)) + "\n")
PY
