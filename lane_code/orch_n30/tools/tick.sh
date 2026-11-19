#!/bin/bash
# Orchestrator tick digest. Local commands only (no ssh, no git); state in /scratch/jjyeung/orch_n30/.tick/ on this node.
# Usage: tick.sh [--peek] [--lines N] [--max N] [--orch] [--all]
#   (a) event files new since the last tick, QUESTION and BLOCKER first: one header line (lane, kind, age, path) and the
#       first --lines lines (default 4, 200 chars each), --max lines in all (default 60). Events that do not fit stay new.
#       Skips *_ORCH_* files unless --orch; a basename copied into several lanes' folders prints once, naming the others.
#       The first tick (empty state) marks events older than 1 h seen and says how many.
#   (b) lanes of LANES.txt (last row per name) with a running process on this node, one line each, plus one line naming
#       lanes among LANES.txt's last 40 rows whose process is gone, whose STATUS.md is younger than 2 h and that have no
#       successor row (same name without its trailing number) after them.
#       --all lists every lane. STATUS.md age from events/<lane>/, or events/<lane without trailing number>/.
#   (c) this node: free /scratch, load, available RAM   (d) line 4 of the IO governor's STATE.md
#   --peek marks nothing seen. Never reads or writes tools/seen.txt (evwait.sh's).
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
ST=/scratch/jjyeung/orch_n30/.tick
if [[ -n "${TICK_STATE:-}" ]]; then  # tests only: a private directory under /scratch or /tmp, never under orch_n30/tools
  case "$(realpath -m "$TICK_STATE")" in /scratch/jjyeung/*|/tmp/*) ST=$(realpath -m "$TICK_STATE");; *) echo "tick.sh: TICK_STATE must be under /scratch/jjyeung or /tmp" >&2; exit 2;; esac
fi
case "$ST" in "$B"*) echo "tick.sh: refusing state dir inside $B" >&2; exit 2;; esac
mkdir -p "$ST" || exit 3
[[ -L "$ST" || -L "$ST/lock" || -L "$ST/seen.txt" || -L "$ST/last_tick" ]] && { echo "tick.sh: symlink in state dir $ST refused" >&2; exit 2; }
exec 9>>"$ST/lock"; flock -n 9 || { echo "tick.sh: another tick is running (lock $ST/lock)" >&2; exit 4; }
export B ST GOV_STATE=/data3/jjyeung/orch_n13_20261026/io_governor/STATE.md
OMP_NUM_THREADS=1 exec /usr/bin/python3 - "$@" <<'PY'
import os, sys, re, time, stat, subprocess, tempfile, signal
signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # a closed pipe ends the tick before any state is written
def _late(*_):
    sys.stdout.flush(); sys.stderr.write("tick.sh: over the 5 s budget (NFS slow?); nothing marked seen\n"); os._exit(5)
signal.signal(signal.SIGALRM, _late); signal.alarm(5)  # one deadline for the whole tick; state is written only after all output
B = os.environ["B"]; ST = os.environ["ST"]; GOV = os.environ["GOV_STATE"]
args = sys.argv[1:]
def opt(name, default):
    if name in args:
        try: return int(args[args.index(name) + 1])
        except (IndexError, ValueError): sys.exit("tick.sh: %s needs a number" % name)
    return default
PEEK = "--peek" in args; ALL = "--all" in args; ORCH = "--orch" in args
NLINES = opt("--lines", 4); NMAX = opt("--max", 60); WIDTH = 200
now = time.time(); host = os.uname()[1].split(".")[0]
SEEN = os.path.join(ST, "seen.txt"); LAST = os.path.join(ST, "last_tick")
stamp = re.compile(r"^(\d{8}T\d{4,6}Z)_([A-Z]+)_")
def age(sec):
    sec = max(0, sec)
    return "%dm" % (sec // 60) if sec < 5400 else "%.1fh" % (sec / 3600.0)
def clean(s):
    return "".join(c if (c >= " " and c != "\x7f") or c == "\t" else "?" for c in s)[:WIDTH]
def atomic_write(path, text):
    fd, tmp = tempfile.mkstemp(dir=ST, prefix=".tmp_")
    with os.fdopen(fd, "w") as f: f.write(text)
    os.replace(tmp, path)

first_run = not os.path.exists(SEEN); seen = set()
try:
    if not first_run:
        with open(SEEN) as f: seen = set(l.rstrip("\n") for l in f)
    last = open(LAST).read().strip() if os.path.exists(LAST) else None
except OSError as e:
    sys.exit("tick.sh: cannot read state in %s: %s" % (ST, e))
print("TICK %s on %s (previous tick %s)" % (time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(now)), host, last or "none"))

# (a) events: stamp-named regular files directly under events/<lane>/
shown = []
try:
    evs = []; ev_root = os.path.join(B, "events")
    for d in sorted(os.listdir(ev_root)):
        try: names = os.listdir(os.path.join(ev_root, d))
        except OSError: continue
        for n in names:
            m = stamp.match(n)
            if m: evs.append((m.group(1), m.group(2), d, n))
    def st_of(d, n):
        try:
            s = os.lstat(os.path.join(ev_root, d, n))
            return s if stat.S_ISREG(s.st_mode) else None
        except OSError: return None
    if first_run:
        old = [d + "/" + n for _, _, d, n in evs if (lambda s: s is not None and s.st_mtime < now - 3600)(st_of(d, n))]
        seen.update(old); print("(first tick: %d events older than 1 h marked seen)" % len(old))
    new = [e for e in evs if e[2] + "/" + e[3] not in seen]
    if not ORCH:
        orch = [e for e in new if e[1] == "ORCH"]; new = [e for e in new if e[1] != "ORCH"]; shown += [e[2] + "/" + e[3] for e in orch]
    groups = {}
    for e in new: groups.setdefault(e[3], []).append(e)
    order = {"QUESTION": 0, "BLOCKER": 1}
    keys = sorted(groups, key=lambda n: (order.get(groups[n][0][1], 2), n))
    print("\n(a) NEW EVENTS: %d files%s" % (len(new), "" if ORCH else " (ORCH files skipped; --orch shows them)"))
    budget = NMAX; printed = 0
    for n in keys:
        es = groups[n]; _, kind, lane, _ = es[0]; fp = os.path.join(ev_root, lane, n); s = st_of(lane, n)
        head = []
        if s is not None:
            try:
                with open(fp, "rb") as f: raw = f.read(8192)
                text = raw.decode("utf-8", "replace")
                head = [clean(l) for l in text.splitlines()[:NLINES]]
                if len(raw) == 8192 and len(text.splitlines()) < NLINES: head.append("[preview cut at 8 KB]")
            except OSError: s = None
        if s is None:
            print("  ! %s unreadable or not a regular file; stays new" % fp); continue
        need = 1 + len(head)
        if need > budget: break
        others = " (also in %s)" % ", ".join(e[2] for e in es[1:]) if len(es) > 1 else ""
        print("== %s %s %s %s%s" % (lane, kind, age(now - s.st_mtime), fp, others))
        for l in head: print("   " + l)
        budget -= need; printed += 1; shown += [e[2] + "/" + e[3] for e in es]
    if printed < len(keys):
        print("+ %d more new events not shown (--max raises the cap); they stay new" % (len(keys) - printed))
except OSError as e:
    print("(a) events unreadable: %s" % e)

# (b) lanes
try:
    lanes = {}; rows = []; bad = 0
    with open(os.path.join(B, "tools", "LANES.txt")) as f:
        for l in f:
            parts = [p.strip() for p in l.strip().split("|")]
            if not l.strip(): continue
            if len(parts) != 3 or not re.match(r"^[A-Za-z0-9_]+$", parts[0]) or not parts[1] or not parts[2]:
                bad += 1; continue
            lanes[parts[0]] = tuple(parts); rows.append(parts[0])
    recent = set(rows[-40:])
    try:
        ps = subprocess.check_output(["ps", "-eo", "pid=,args="], timeout=3).decode("utf-8", "replace").splitlines()
    except Exception as e:
        ps = None; print("(b) ps failed: %s" % e)
    procs = []
    for l in ps or []:
        p = l.split()
        if len(p) >= 2: procs.append((p[0], p[1:]))
    def running(lane, brief):
        for pid, a in procs:
            exe = os.path.basename(a[0])
            if exe == "devin" and any(a[i] == "--prompt-file" and a[i + 1] == brief for i in range(len(a) - 1)):
                return pid
            if exe == "claude" and ("lane %s on node" % lane) in " ".join(a):
                return pid
            if any(a[i] == "--label" and a[i + 1] == lane for i in range(len(a) - 1)) and any("codex" in x for x in a[:3]):
                return pid
        return None
    def status_age(lane):
        for d in (lane, re.sub(r"_?\d+$", "", lane)):
            try: return now - os.path.getmtime(os.path.join(B, "events", d, "STATUS.md"))
            except OSError: continue
        return None
    print("\n(b) LANES running on %s%s" % (host, "" if ps is not None else " (unknown: ps failed)"))
    dead = []; base = lambda x: re.sub(r"_?\d+$", "", x)
    later = {}
    for i, r in enumerate(rows): later[base(r)] = i
    for lane, (name, brief, lhost) in sorted(lanes.items(), key=lambda kv: rows.index(kv[0])):
        a = status_age(lane); pid = running(lane, brief) if lhost == host else None
        if pid: print("  %-16s pid %-8s status %s" % (lane, pid, "-" if a is None else age(a)))
        elif ALL: print("  %-16s %-13s %-8s status %s" % (lane, lhost, ("no proc" if ps is not None else "unknown") if lhost == host else "remote?", "-" if a is None else age(a)))
        elif (lane in recent and lhost == host and ps is not None and a is not None and a < 7200
              and later[base(lane)] == len(rows) - 1 - rows[::-1].index(lane)):  # no successor row after it
            dead.append("%s (status %s)" % (lane, age(a)))
    if dead: print("  GONE without process, STATUS < 2 h: " + ", ".join(dead))
    if bad: print("  (%d malformed LANES.txt rows ignored)" % bad)
except OSError as e:
    print("(b) lanes unreadable: %s" % e)

# (c) node
def sh(c):
    try: return subprocess.check_output(c, shell=True, stderr=subprocess.STDOUT, timeout=3).decode("utf-8", "replace").strip()
    except Exception as e: return "<%s failed: %s>" % (c, e)
print("\n(c) NODE %s: /scratch avail %s | load %s (%s cores) | RAM available %s" % (
    host, sh("df -h --output=avail,pcent /scratch | tail -n 1"), sh("cut -d' ' -f1-3 /proc/loadavg"),
    os.cpu_count(), sh("free -g | awk '/^Mem:/{print $7\" GB of \"$2}'")))

# (d) governor
try:
    with open(GOV, "rb") as f: l4 = [l.decode("utf-8", "replace").rstrip("\n") for _, l in zip(range(4), f)]
    print("(d) GOVERNOR " + (clean(l4[3]) if len(l4) >= 4 else "<STATE.md has fewer than 4 lines>"))
except OSError as e:
    print("(d) GOVERNOR <unreadable: %s>" % e)

sys.stdout.flush()
if not PEEK:
    seen.update(shown)
    atomic_write(SEEN, "".join(s + "\n" for s in sorted(seen)))
    atomic_write(LAST, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)) + "\n")
PY
