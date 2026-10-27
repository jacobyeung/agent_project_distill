"""Night launcher and babysitter for the rung-1 arms on code-aws (trinity-0-13, python3.12).

Arms run at world 32 (one 4 x 8 H100 block each) in per-block chains from QUEUE_RUNG1.json. An arm starts only when
its estimated wall fits before the night's end (06:20 PT); otherwise it waits for the next night and is never started
truncated. A failed arm is recorded and never resubmitted here. When an arm publishes, its run is appended to the
awstrain lane's EVAL_QUEUE.json (the eval scheduler adds its VSI and VSTI cells).

usage: r1night.py plan        read DISTILL_NIGHT_SHARE; write the block chains, SCHEDULE.json and NIGHT_TRAIN_RESERVE
       r1night.py tick        read the newest poll, decide, queue submissions and a status probe, run one driver poll;
                              prints the seconds until the next tick (60 while a started arm has no step yet, else 600)
State: night/STATE.json; log: night/TICKS.log.
"""
import json
import math
import os
import re
import secrets
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

HOME = Path(__file__).resolve().parent.parent
LANES = HOME.parent
TOOLS = HOME / "tools"
NIGHT = HOME / "night"
STATE, TICKS = NIGHT / "STATE.json", NIGHT / "TICKS.log"
SHARE_FILE, RESERVE_FILE = LANES / "aws_reserve/DISTILL_NIGHT_SHARE", LANES / "aws_reserve/NIGHT_TRAIN_RESERVE"
EVAL_QUEUE = LANES / "awstrain_20261027/EVAL_QUEUE.json"
PY = "/home/jjyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3.12"
PT = ZoneInfo("America/Los_Angeles")
END = datetime(2026, 10, 28, 6, 20, tzinfo=PT)
TRAINER = {"trainer_commit": "299b0c526e3663ff2a42a5c3a9113e9e0b8e4164",
           "runtime_record": "/opt/aws_incoming/01eefae1f0ae55ff3e17dc34bb0664417f27e269e8192ce554e9d2afd01a42ac.json"}
CLOSURE = "1e909863b74bd95eb0c36e957ea88fd7b51befb43a902ca975b643bd5e157c3d"
BASE = "/lustre/fsw/portfolios/av/users/jyeung/ap/59845bf9"
RUNS = BASE + "/d/orch/runs/aws128p_20261025"
STEPS = {"RG1_A1_S17": 1133, "RG1_A2_S17": 1133, "RG1_A3_S17": 1133, "RG1_C_S17": 115, "RG1_S_S17": 188,
         "RG1_A1S_S17": 1321}
SECONDS = {"RG1_A3_S17": 19.5, "RG1_S_S17": 18.0}  # default s/step before measurement; others 17.5
TAG = {"RG1_A1_S17": "a1", "RG1_A2_S17": "a2", "RG1_A3_S17": "a3", "RG1_C_S17": "c", "RG1_S_S17": "s",
       "RG1_A1S_S17": "m"}
OVERHEAD_MIN = 20  # startup (image, venv, admission, memory probe) plus finalize and publication
TERMINAL = ("COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "NODE_FAIL", "OUT_OF_MEMORY", "PREEMPTED", "DEADLINE")


def now():
    return datetime.now(PT)


def log(text):
    NIGHT.mkdir(exist_ok=True)
    with TICKS.open("a") as stream:
        stream.write(f"{now().isoformat(timespec='seconds')} {text}\n")


def save(state):
    tmp = STATE.with_name(STATE.name + ".next")
    tmp.write_text(json.dumps(state, indent=1, sort_keys=True) + "\n")
    os.replace(tmp, STATE)


def write_int(path, value):
    tmp = path.with_name(path.name + ".next")
    tmp.write_text(f"{value}\n")
    os.replace(tmp, path)


def chains(blocks):
    a1, a2, a3, c, s, m = "RG1_A1_S17", "RG1_A2_S17", "RG1_A3_S17", "RG1_C_S17", "RG1_S_S17", "RG1_A1S_S17"
    if blocks >= 4:
        return [[a1, c, s], [a3], [a2], [m]]
    if blocks == 3:
        return [[a1, a2], [a3, c, s], [m]]
    if blocks == 2:
        return [[a1, a2], [a3, c, s]]
    return [[a1, a3, c]]


def plan():
    share = int(re.match(r"\s*([0-9]+)", SHARE_FILE.read_text())[1])
    blocks = max(1, min(4, (share - 14) // 32))
    checker = 24 if share >= 168 else 8
    state = {"share": share, "blocks": [{"chain": chain, "next": 0, "current": None, "history": []}
                                         for chain in chains(blocks)],
             "measured_s_per_step": {}, "eval_added": [], "created": now().isoformat(timespec="seconds")}
    if STATE.exists():
        old = json.loads(STATE.read_text())
        if any(b.get("current") for b in old["blocks"]):
            raise SystemExit("a night plan with started arms exists; refusing to replace it")
    save(state)
    schedule = json.loads((HOME / "SCHEDULE.json").read_text())
    schedule = [row for row in schedule if row["from"] < "2026-10-27T18:30"]
    schedule += [{"from": "2026-10-27T18:30", "total": share, "lane": 32 * blocks,
                  "why": f"night: rung-1 launch, {blocks} blocks of 32 GPUs (DISTILL_NIGHT_SHARE {share})"},
                 {"from": "2026-10-28T06:20", "total": 16, "lane": 0, "why": "day: rung-1 arms end by 06:20"}]
    (HOME / "SCHEDULE.json").write_text(json.dumps(schedule, indent=1) + "\n")
    write_int(RESERVE_FILE, 32 * blocks + checker)
    log(f"plan share={share} blocks={blocks} chains={[b['chain'] for b in state['blocks']]} reserve={32 * blocks + checker}")
    print(json.dumps(state["blocks"], indent=1))


def estimate_minutes(arm, state):
    seconds = state["measured_s_per_step"].get(arm)
    if seconds is None:
        base = [v for k, v in state["measured_s_per_step"].items() if k in ("RG1_A1_S17", "RG1_A2_S17")]
        seconds = (max(base) if base else 17.5) * (SECONDS.get(arm, 17.5) / 17.5)
    return OVERHEAD_MIN + STEPS[arm] * seconds / 60


def parse_poll(text):
    """slurm id -> state, and per-name probe lines from the newest poll file."""
    states = {}
    sacct = text.partition("=== SACCT")[2].partition("=== LOGS")[0]
    for line in sacct.splitlines():
        parts = line.split("|")
        if len(parts) >= 3 and parts[0].isdigit():
            states[parts[0]] = parts[2].split()[0]
    probes = {}
    for match in re.finditer(r"^R1PROBE (\S+) steps=(\d+) mean=(\S+) last=(\S+) published=(\d)$", text, re.M):
        name, steps, mean, last, published = match.groups()
        probes[name] = {"steps": int(steps), "mean": None if mean == "-" else float(mean),
                        "last": last, "published": published == "1"}
    return states, probes


def queue_submission(arm, minutes, state):
    run = f"r1{TAG[arm]}_{secrets.token_hex(4)}"
    spec = dict(TRAINER, phase="mntrain", efa=True, argv=[arm, run, 0],
                purpose=f"rung-1 arm {arm}: full run, world 32 over EFA, ends by 06:20 PT")
    path = NIGHT / f"SPEC_{run}.json"
    path.write_text(json.dumps(spec, indent=1, sort_keys=True) + "\n")
    digest = subprocess.check_output([PY, "-B", str(TOOLS / "r1actions.py"), "spec", str(path)], text=True).strip()
    limit_min = min(math.ceil(minutes + 30), int((END - now()).total_seconds() // 60) - 2)
    limit = f"{limit_min // 60}:{limit_min % 60:02d}:00"
    env = dict(os.environ, R1_DEADLINE=END.strftime("%Y-%m-%dT%H:%M:%S"))
    name = subprocess.check_output([PY, "-B", str(TOOLS / "r1actions.py"), "sbatchmn", CLOSURE, digest, "4", limit, "-"],
                                   text=True, env=env).strip()
    return {"arm": arm, "run": run, "name": name, "spec_sha256": digest, "limit": limit, "job": None,
            "queued": now().isoformat(timespec="seconds"), "estimate_min": round(minutes)}


def ledger_job(name):
    jobs = None
    for line in (LANES / "aws_reserve/AWS_JOB_LEDGER.jsonl").read_text().splitlines():
        if name in line:
            entry = json.loads(line)
            if entry.get("opaque_name") == name and entry.get("slurm_job_id"):
                jobs = str(entry["slurm_job_id"])
    return jobs


def tick():
    state = json.loads(STATE.read_text())
    polls = sorted((HOME / "polls").glob("poll_*.txt"))
    states, probes = parse_poll(polls[-1].read_text()) if polls else ({}, {})
    waiting_steps = False
    for block in state["blocks"]:
        cur = block["current"]
        if cur and not cur["job"]:
            cur["job"] = ledger_job(cur["name"])
        if cur and cur["job"]:
            slurm = states.get(cur["job"], "UNKNOWN")
            probe = probes.get(cur["name"], {})
            cur["slurm_state"], cur["steps"] = slurm, probe.get("steps", cur.get("steps", 0))
            if probe.get("mean") and probe.get("steps", 0) >= 5:
                state["measured_s_per_step"][cur["arm"]] = probe["mean"]
                if cur["arm"] in ("RG1_A1_S17", "RG1_A2_S17"):
                    state["measured_s_per_step"].setdefault("RG1_A1_S17", probe["mean"])
            if cur.get("first_step") is None and probe.get("steps", 0) >= 1:
                cur["first_step"] = now().isoformat(timespec="seconds")
                log(f"{cur['arm']} job {cur['job']} first steps landed (steps={probe['steps']} last={probe.get('last')})")
            if slurm == "RUNNING" and probe.get("steps", 0) == 0:
                waiting_steps = True
            if slurm in TERMINAL:
                cur["published"] = probe.get("published", False)
                cur["ended"] = now().isoformat(timespec="seconds")
                log(f"{cur['arm']} job {cur['job']} ended {slurm} steps={cur['steps']} published={cur['published']}")
                if slurm == "COMPLETED" and cur["published"] and cur["run"] not in state["eval_added"]:
                    queue = json.loads(EVAL_QUEUE.read_text())
                    queue.append({"run": cur["run"], "job": int(cur["job"])})
                    tmp = EVAL_QUEUE.with_name(EVAL_QUEUE.name + ".next")
                    tmp.write_text(json.dumps(queue, indent=1) + "\n")
                    os.replace(tmp, EVAL_QUEUE)
                    state["eval_added"].append(cur["run"])
                    log(f"EVAL_QUEUE += {cur['run']} job {cur['job']}")
                block["history"].append(cur)
                block["current"] = None
        elif cur and not cur["job"]:
            waiting_steps = True
        if block["current"] is None and block["next"] < len(block["chain"]):
            arm = block["chain"][block["next"]]
            minutes = estimate_minutes(arm, state)
            left = (END - now()).total_seconds() / 60
            if now() < datetime(2026, 10, 27, 18, 30, tzinfo=PT):
                continue
            if minutes + 5 <= left:
                block["current"] = queue_submission(arm, minutes, state)
                block["next"] += 1
                waiting_steps = True
                log(f"queued {arm} as {block['current']['name']} run {block['current']['run']} "
                    f"estimate {minutes:.0f} min, {left:.0f} min left")
            elif block.get("deferred") != arm:
                block["deferred"] = arm
                log(f"{arm} waits for the next night: estimate {minutes:.0f} min, {left:.0f} min left")
    active = sum(32 for b in state["blocks"] if b["current"])
    pending_work = any(b["current"] or (b["next"] < len(b["chain"]) and b.get("deferred") != b["chain"][b["next"]])
                       for b in state["blocks"])
    if not pending_work:
        write_int(RESERVE_FILE, 24 if state["share"] >= 168 else 8)
    save(state)
    # Status probe for the current arms (job log steps, mean step seconds, publication), run in this poll.
    targets = " ".join(f'{c["name"]}:{c["job"]}:{c["run"]}' for c in (b["current"] for b in state["blocks"])
                       if c and c.get("job"))
    lines = [f"python3 - {BASE} {RUNS} {targets or 'none'} <<'PY'",
             "import glob, json, os, sys",
             "base, runs = sys.argv[1:3]",
             "for item in sys.argv[3:]:",
             "    if item == 'none':",
             "        continue",
             "    name, job, run = item.split(':')",
             "    rows = {}",
             "    for path in glob.glob(f'{base}/l/{name}_{job}.log'):",
             "        for line in open(path, errors='replace'):",
             "            if '\"optimizer_step\"' in line and '{' in line:",
             "                try:",
             "                    row = json.loads(line[line.index('{'):])",
             "                except ValueError:",
             "                    continue",
             "                rows[row['optimizer_step']] = row",
             "    ordered = [rows[k] for k in sorted(rows)]",
             "    tail = [r['step_seconds'] for r in ordered[2:]][-50:]",
             "    mean = round(sum(tail) / len(tail), 2) if tail else '-'",
             "    last = ordered[-1]['optimizer_step'] if ordered else '-'",
             "    published = int(os.path.exists(f'{runs}/{run}/attempt-{job}-0/publication/PUBLISHED.json'))",
             "    print(f'R1PROBE {name} steps={len(ordered)} mean={mean} last={last} published={published}')",
             "PY"]
    probe = NIGHT / "probe.sh"
    probe.write_text("\n".join(lines) + "\n")
    subprocess.check_output([PY, "-B", str(TOOLS / "r1actions.py"), "sh", "n_probe", str(probe)], text=True)
    result = subprocess.run([PY, "-B", str(TOOLS / "r1aws.py"), "run"], capture_output=True, text=True,
                            env=dict(os.environ, R1_MIN_INTERVAL="55"), timeout=900)
    for f in (HOME / "actions/pending").glob("a_*n_probe.json"):
        f.rename(HOME / "actions/sent" / f.name)  # one probe per tick, whatever its exit code
    log("poll: " + " ".join(result.stdout.split()[:6]) + f" active={active}")
    print(60 if waiting_steps else 600)


if __name__ == "__main__":
    {"plan": plan, "tick": tick}[sys.argv[1]]()
