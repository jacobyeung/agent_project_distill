"""Night launcher and babysitter for the rung-1 arms on code-aws (trinity-0-13, python3.12).

Arms run at world 32 (one 4 x 8 H100 block each) in per-block chains from QUEUE_RUNG1.json. An arm starts only when
its estimated wall fits before the night's end (06:20 PT); otherwise it waits for the next night and is never started
truncated. A failed arm is recorded and never resubmitted here. When an arm publishes, its run is appended to the
awstrain lane's EVAL_QUEUE.json (the eval scheduler adds its VSI and VSTI cells).

usage: r1night.py plan        read DISTILL_NIGHT_SHARE; write the block chains (from the night dir's PLAN.json when it
                              exists, else the coded chains), SCHEDULE.json and NIGHT_TRAIN_RESERVE
       r1night.py tick        read the newest poll, decide, queue submissions and a status probe, run one driver poll;
                              prints the seconds until the next tick (60 while a started arm has no step yet, else 600)
Night dir: R1_NIGHT_DIR (default night/) holds NIGHT.json ({"start": ISO, "end": ISO}; default 10-27 18:30 to 10-28
06:20), PLAN.json, STATE.json, TICKS.log and the submitted specs.
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
NIGHT = Path(os.environ.get("R1_NIGHT_DIR") or HOME / "night")
STATE, TICKS = NIGHT / "STATE.json", NIGHT / "TICKS.log"
SHARE_FILE, RESERVE_FILE = LANES / "aws_reserve/DISTILL_NIGHT_SHARE", LANES / "aws_reserve/NIGHT_TRAIN_RESERVE"
EVAL_QUEUE = LANES / "awstrain_20261027/EVAL_QUEUE.json"
PY = "/home/jjyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3.12"
PT = ZoneInfo("America/Los_Angeles")
WINDOW = json.loads((NIGHT / "NIGHT.json").read_text()) if (NIGHT / "NIGHT.json").exists() else {}
START = datetime.fromisoformat(WINDOW.get("start", "2026-10-27T18:30")).replace(tzinfo=PT)
END = datetime.fromisoformat(WINDOW.get("end", "2026-10-28T06:20")).replace(tzinfo=PT)


def at(hhmm):
    """A not_before HH:MM of this night: the start's evening, or the next morning for hours before noon."""
    hour, minute = (int(part) for part in re.fullmatch(r"(\d{1,2}):(\d{2})", hhmm).groups())
    moment = START.replace(hour=hour, minute=minute)
    return moment + timedelta(days=1) if hour < 12 else moment
TRAINER = {"trainer_commit": "299b0c526e3663ff2a42a5c3a9113e9e0b8e4164",
           "runtime_record": "/opt/aws_incoming/01eefae1f0ae55ff3e17dc34bb0664417f27e269e8192ce554e9d2afd01a42ac.json"}
CLOSURE = "f344aa6ba407a39f5716fb665757007f0b62dd8ace1d397d1697dd11642a3890"
BASE = "/lustre/fsw/portfolios/av/users/jyeung/ap/59845bf9"
RUNS = BASE + "/d/orch/runs/aws128p_20261025"
STEPS = {"RG1_A1_S17": 1133, "RG1_A2_S17": 1133, "RG1_A3_S17": 1133, "RG1_C_S17": 115, "RG1_S_S17": 188,
         "RG1_A1S_S17": 1321, "A1H_S17": 1133, "RG1_A3_B128_S17": 2266, "RG1_A3_W64_S17": 1133,
         "RG1_A1S_W64_S17": 1321, "RG1_A1_W64_S18": 1133, "RG1_C_S18": 115, "SELF_V4_S18": 384, "SELF_V4_C_S18": 384,
         "RG1_X_S17_K200": 1133, "RG1_X_W64_S17_K200": 1133, "RG1_X_W64_S18_K200": 1133, "RG1_A1_S18_K200": 1133,
         "RG1_A1_W64_S18_K200": 1133, "RG1_A3_W64_S17_K200": 1133, "RG1_A1S_W64_S17_K200": 1321,
         "R27_A1_S17_K200": 1133, "R27_X_S17_K200": 1133}
SECONDS = {"RG1_A3_S17": 19.5, "RG1_S_S17": 18.0, "A1H_S17": 18.5, "RG1_A3_B128_S17": 11.0,
           "RG1_A3_W64_S17": 11.0, "RG1_A1S_W64_S17": 11.0, "RG1_A1_W64_S18": 11.0,
           "RG1_X_W64_S17_K200": 11.0, "RG1_X_W64_S18_K200": 11.0, "RG1_A1_W64_S18_K200": 11.0,
           "RG1_A3_W64_S17_K200": 11.0, "RG1_A1S_W64_S17_K200": 11.0, "RG1_A1_S18_K200": 22.0,
           "R27_A1_S17_K200": 22.0, "R27_X_S17_K200": 22.0}  # defaults; others 17.5 (27B: 19.9 s at world 16 x 4 rows)
NODES = {"RG1_A3_W64_S17": 8, "RG1_A1S_W64_S17": 8, "RG1_A1_W64_S18": 8, "RG1_X_W64_S17_K200": 8,
         "RG1_X_W64_S18_K200": 8, "RG1_A1_W64_S18_K200": 8, "RG1_A3_W64_S17_K200": 8, "RG1_A1S_W64_S17_K200": 8,
         "R27_A1_S17_K200": 8, "R27_X_S17_K200": 8}  # nodes of 8 GPUs per arm; others 4
SINGLE = {"SELF_V4_S18": 4, "SELF_V4_C_S18": 4}  # one-node arms: GPUs (world 4, the self-trace pair's frozen recipe)


def block_gpus(b):
    arm = b["current"]["arm"] if b.get("current") else b["chain"][min(b["next"], len(b["chain"]) - 1)]
    return SINGLE.get(arm) or 8 * NODES.get(arm, 4)
TAG = {"RG1_A1_S17": "a1", "RG1_A2_S17": "a2", "RG1_A3_S17": "a3", "RG1_C_S17": "c", "RG1_S_S17": "s",
       "RG1_A1S_S17": "m", "A1H_S17": "h", "RG1_A3_B128_S17": "a3b", "RG1_A3_W64_S17": "a3w",
       "RG1_A1S_W64_S17": "mw", "RG1_A1_W64_S18": "a1w", "RG1_C_S18": "c18", "SELF_V4_S18": "sv18", "SELF_V4_C_S18": "svc18",
       "RG1_X_S17_K200": "x", "RG1_X_W64_S17_K200": "xw", "RG1_X_W64_S18_K200": "xw18", "RG1_A1_S18_K200": "a118",
       "RG1_A1_W64_S18_K200": "a1w18", "RG1_A3_W64_S17_K200": "a3wk", "RG1_A1S_W64_S17_K200": "mwk",
       "R27_A1_S17_K200": "g27", "R27_X_S17_K200": "x27"}
# Arms another lane owns run on their own trainer tree (QUEUE_RUNG1.json entry: trainer_commit, runtime_record).
OWN_TRAINER = {"A1H_S17": {"trainer_commit": "f69509db55cb3e659c456ad31a2e760254062123",
                           "runtime_record": "/opt/aws_incoming/94cbc8a43483a8b50d3784c9182cb6c926394f100a36199f1caae7755f15ef40.json"}}
# Arms on another tree of this lane (the 8-node branch), scored through EVAL_QUEUE.json like the others.
T8 = {"trainer_commit": "9596b114e5fd08dede4fa6a97ea983e9e3987332",
      "runtime_record": "/opt/aws_incoming/0ffa741b7029208750f1befe8c09395407e66e44e385a163fa0578b9086f5c00.json"}
ARM_TRAINER = {arm: T8 for arm in NODES}  # every world-64 arm (and the 27B pair) runs on the 8-node branch
STUDENT_HEX = {"R27_A1_S17_K200": "7177656e33365f323762", "R27_X_S17_K200": "7177656e33365f323762"}  # spec student_hex
# Retired arms are never submitted, resumed or planned (A1H_S17: heads harmful, step-500 VSI 23.7 vs A1's 51.2).
RETIRED = {"A1H_S17"}
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


def chains(share):
    """[(chain, not_before HH:MM or None), ...] per 32-GPU block, in the coordinator's order for the night's share."""
    a1, a2, a3, c, s, m, h = ("RG1_A1_S17", "RG1_A2_S17", "RG1_A3_S17", "RG1_C_S17", "RG1_S_S17", "RG1_A1S_S17",
                              "A1H_S17")
    if share >= 168:
        # USER ruling 10-27: wave 1 A1, A3, A2, A1H (128); the checker holds 24 until about 21:20, then a fifth block
        # runs C and S. A1S needs about 6.5 h at world 32 after wave 1 and the trainer caps world at 32, so it waits.
        return [([a1], None), ([a3], None), ([a2], None), ([h], None), ([c, s], "20:50")]
    if share >= 110:
        return [([a1, a2], None), ([a3, c, s], None), ([h], None)]
    if share >= 78:
        return [([a1, a2], None), ([a3, c, s], None)]  # A1H and A1S wait for the next night
    return [([a1, a3, c], None)]


def checker_gpus(share):
    return 24 if share >= 168 else 8


def plan():
    share = int(re.match(r"\s*([0-9]+)", SHARE_FILE.read_text())[1])
    plan_file = NIGHT / "PLAN.json"
    if plan_file.exists():
        # Blocks from the night's plan: chain, not_before, after_block, after_submitted_block, resume_run with
        # remaining_steps, hold (released when the arm's admission appears on code-aws).
        spec = json.loads(plan_file.read_text())
        keys = ("not_before", "after_block", "after_submitted_block", "resume_run", "remaining_steps", "hold")
        block_list = [dict({key: item[key] for key in keys if key in item}, chain=item["chain"], next=0, current=None,
                           history=[]) for item in spec["blocks"]]
        block_list = [dict(b, not_before=b.get("not_before")) for b in block_list]
        checker = spec.get("checker_gpus", checker_gpus(share))
    else:
        block_list = [{"chain": chain, "not_before": start, "next": 0, "current": None, "history": []}
                      for chain, start in chains(share)]
        checker = checker_gpus(share)
    for b in block_list:
        unknown = [arm for arm in b["chain"] if arm not in STEPS or arm not in TAG or arm in RETIRED]
        if unknown:
            raise SystemExit(f"unknown arms in the plan: {unknown}")
    plan_blocks = [(b["chain"], b["not_before"]) for b in block_list]
    blocks = len(plan_blocks)
    state = {"share": share, "blocks": block_list,
             "measured_s_per_step": {}, "eval_added": [], "created": now().isoformat(timespec="seconds"),
             # Arms submitted only once their CPU admission is on code-aws (preps still running by day).
             "await_admission": json.loads(plan_file.read_text()).get("await_admission", []) if plan_file.exists() else [],
             "admitted": []}
    if STATE.exists():
        old = json.loads(STATE.read_text())
        if any(b.get("current") for b in old["blocks"]):
            raise SystemExit("a night plan with started arms exists; refusing to replace it")
    save(state)
    schedule = json.loads((HOME / "SCHEDULE.json").read_text())
    lane_gpus = min(share, sum(block_gpus(b) for b in block_list if not b.get("after_block")))
    schedule = [row for row in schedule if row["from"] < START.strftime("%Y-%m-%dT%H:%M")]
    schedule += [{"from": START.strftime("%Y-%m-%dT%H:%M"), "total": share, "lane": lane_gpus,  # never above the share
                  "why": f"night: rung-1 launch, {blocks} blocks (DISTILL_NIGHT_SHARE {share})"},
                 {"from": END.strftime("%Y-%m-%dT%H:%M"), "total": 16, "lane": 0,
                  "why": f"day: rung-1 arms end by {END.strftime('%H:%M')}"}]
    (HOME / "SCHEDULE.json").write_text(json.dumps(schedule, indent=1) + "\n")
    reserve = min(share, sum(block_gpus(b) for b in block_list if not b.get("not_before") and b.get("after_block") is None)
                  + checker)
    write_int(RESERVE_FILE, reserve)
    log(f"plan share={share} blocks={blocks} chains={[(b['chain'], b['not_before']) for b in state['blocks']]} "
        f"reserve={reserve}")
    print(json.dumps(state["blocks"], indent=1))


def estimate_minutes(arm, state):
    seconds = state["measured_s_per_step"].get(arm)
    if seconds is None:
        base = [v for k, v in state["measured_s_per_step"].items() if k in ("RG1_A1_S17", "RG1_A2_S17")]
        seconds = (max(base) if base else 17.5) * (SECONDS.get(arm, 17.5) / 17.5)
        w64 = [v for k, v in state["measured_s_per_step"].items() if NODES.get(k) == 8]
        if NODES.get(arm) == 8:
            seconds = max(w64) if w64 else SECONDS[arm]
        if arm == "RG1_A3_B128_S17" and "RG1_A2_S17" in state["measured_s_per_step"]:
            seconds = state["measured_s_per_step"]["RG1_A2_S17"] * 0.68  # 4 rows per GPU instead of 8, longer targets
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


def queue_submission(arm, minutes, state, run=None):
    run = run or (f"aws128_t1_ST9_s18_k{secrets.token_hex(3)}" if arm in SINGLE  # the self-trace family's run naming
                  else f"r1{TAG[arm]}_{secrets.token_hex(4)}")
    trainer = {} if arm in SINGLE else (OWN_TRAINER.get(arm) or ARM_TRAINER.get(arm) or TRAINER)  # SINGLE: closure default
    # A unique submission field keeps a resubmission (e.g. a resume of the same run) from hashing to a dead job's name.
    trainer = dict(trainer, submission=secrets.token_hex(4))
    if arm in STUDENT_HEX:
        trainer["student_hex"] = STUDENT_HEX[arm]
    world = SINGLE.get(arm) or 8 * NODES.get(arm, 4)
    spec = dict(trainer, phase="mntrain", efa=arm not in SINGLE, argv=[arm, run, 0],
                purpose=f"rung-1 arm {arm}: full run, world {world} over EFA, ends by {END.strftime('%H:%M')} PT")
    path = NIGHT / f"SPEC_{run}.json"
    path.write_text(json.dumps(spec, indent=1, sort_keys=True) + "\n")
    digest = subprocess.check_output([PY, "-B", str(TOOLS / "r1actions.py"), "spec", str(path)], text=True).strip()
    # The limit is the time left to 06:20 (the deadline also enforces it): a slower-than-estimated arm still gets to its
    # final checkpoint and publication if the night allows, instead of timing out at an estimate-based limit.
    # Slurm refuses a job whose expected start plus its limit passes the deadline, so the limit may shrink to the
    # time-min (estimate plus 15 min) to fit; a start that leaves less than that removes the job instead of truncating.
    limit_min = int((END - now()).total_seconds() // 60) - 5
    floor_min = min(limit_min, math.ceil(minutes + 15))
    limit = f"{limit_min // 60}:{limit_min % 60:02d}:00"
    env = dict(os.environ, R1_DEADLINE=END.strftime("%Y-%m-%dT%H:%M:%S"),
               R1_TIME_MIN=f"{floor_min // 60}:{floor_min % 60:02d}:00")
    if arm in SINGLE:
        env.update(R1_GPN=str(SINGLE[arm]), R1_CPUS="32", R1_MEM="256G")
    name = subprocess.check_output([PY, "-B", str(TOOLS / "r1actions.py"), "sbatchmn", CLOSURE, digest,
                                    str(1 if arm in SINGLE else NODES.get(arm, 4)), limit, "-"],
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
    text = polls[-1].read_text() if polls else ""
    states, probes = parse_poll(text)
    refused = set(re.findall(r"^SBATCH_REPLY (\S+) sbatch: error", text, re.M))
    admitted = set(re.findall(r"^R1ADMITTED (\S+)$", text, re.M))
    state.setdefault("admitted", [])
    for arm in sorted(admitted - set(state["admitted"])):
        state["admitted"].append(arm)
        log(f"{arm} admitted on code-aws")
    margins = re.findall(r"^R1MARGIN (\d+) (\d+)$", text, re.M)
    tenth, ours = (int(margins[-1][0]), int(margins[-1][1])) if margins else (None, None)

    def margin_ok(gpus):
        # Priority project (23:5x PT): no new job while the account's running GPUs sit fewer than ~80 below the
        # 10th-largest user's; the new job's GPUs count as if running.
        return tenth is not None and tenth - (ours + gpus) >= 80
    totals = re.findall(r"^R1TOTAL (\d+)$", text, re.M)
    project_total = int(totals[-1]) if totals else None
    waiting_steps = False
    for block in state["blocks"]:
        cur = block["current"]
        if cur and not cur["job"]:
            cur["job"] = ledger_job(cur["name"])
        if cur and not cur["job"] and cur["name"] in refused:
            # Slurm refused the submission (nothing runs): record it and let the arm be queued again, twice at most.
            log(f"{cur['arm']} submission {cur['name']} refused by sbatch; requeue")
            block.setdefault("refusals", []).append(cur)
            block["current"] = None
            if len(block["refusals"]) <= 2:
                block["next"] -= 1
            cur = None
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
            if slurm not in TERMINAL and probe.get("steps", 0) == 0:  # pending or starting: check every minute
                waiting_steps = True
            if slurm in TERMINAL:
                cur["published"] = probe.get("published", False)
                cur["ended"] = now().isoformat(timespec="seconds")
                log(f"{cur['arm']} job {cur['job']} ended {slurm} steps={cur['steps']} published={cur['published']}")
                # Head-trained arms are scored on their owner lane's harness, not through EVAL_QUEUE.json.
                if (slurm == "COMPLETED" and cur["published"] and cur["run"] not in state["eval_added"]
                        and cur["arm"] not in OWN_TRAINER):
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
        if block.get("hold") and block["next"] < len(block["chain"]) and block["chain"][block["next"]] in admitted:
            block["hold"] = False
            log(f"{block['chain'][block['next']]} admitted on code-aws; block released")
        if block["current"] is None and block["next"] < len(block["chain"]) and block.get("hold"):
            continue  # its next arm is still being prepared; the block's GPUs stay reserved for it
        first = block.get("after_submitted_block")
        lead = state["blocks"][first] if first is not None else None
        if (block["current"] is None and lead is not None and not (lead["current"] or {}).get("job")
                and not lead["history"] and not lead.get("deferred")):
            continue  # keeps the coordinator's order: that block's arm is submitted first unless it cannot fit
        after = block.get("after_block")
        if block["current"] is None and after is not None and (state["blocks"][after]["current"]
                                                               or state["blocks"][after]["next"] < len(state["blocks"][after]["chain"])):
            continue  # starts only once that block's arms have ended (capacity plan)
        if block["current"] is None and block["next"] < len(block["chain"]):
            arm = block["chain"][block["next"]]
            if arm in RETIRED:
                block["next"] += 1
                log(f"{arm} is retired; skipped")
                continue
            if arm in state.get("await_admission", []) and arm not in state["admitted"]:
                if block.get("admission_wait") != arm:
                    block["admission_wait"] = arm
                    log(f"{arm} waits for its CPU admission on code-aws")
                continue
            minutes = estimate_minutes(arm, state)
            resume = block.get("resume_run") if block["next"] == 0 else None  # only a block's first arm resumes
            if resume:  # an interrupted run resumes from its checkpoint: only the remaining steps
                minutes = OVERHEAD_MIN + (minutes - OVERHEAD_MIN) * block["remaining_steps"] / STEPS[arm]
            left = (END - now()).total_seconds() / 60
            if now() < START:
                continue
            if block.get("not_before") and now() < at(block["not_before"]):
                # Start early when 32 GPUs are free under the share right now (training has first claim).
                if project_total is None or project_total + block_gpus(block) > state["share"]:
                    continue
                log(f"block {block['chain']} opens early: {project_total} GPUs in use of {state['share']}")
                block["not_before"] = None
            if minutes + 5 <= left and not margin_ok(block_gpus(block)):
                if block.get("margin_wait") != arm:
                    block["margin_wait"] = arm
                    log(f"{arm} waits: account {ours} running GPUs vs 10th user {tenth} (needs a margin of 80)")
                continue
            if minutes + 5 <= left:
                block["current"] = queue_submission(arm, minutes, state, resume)
                block["next"] += 1
                waiting_steps = True
                log(f"queued {arm} as {block['current']['name']} run {block['current']['run']} "
                    f"estimate {minutes:.0f} min, {left:.0f} min left")
            elif block.get("deferred") != arm:
                block["deferred"] = arm
                log(f"{arm} waits for the next night: estimate {minutes:.0f} min, {left:.0f} min left")
    active = sum(block_gpus(b) for b in state["blocks"] if b["current"])

    def open_block(b):
        started = not b.get("not_before") or now() >= at(b["not_before"])
        waiting = (b["next"] < len(b["chain"]) and b.get("deferred") != b["chain"][b["next"]]
                   and not b.get("hold"))  # a held arm reserves its GPUs only once released (just before submitting)
        after = b.get("after_block")
        if not b["current"] and after is not None:  # reserved only once the block it follows has ended
            prior = state["blocks"][after]
            started = started and not prior["current"] and prior["next"] >= len(prior["chain"])
        return bool(b["current"]) or (started and waiting)

    # Training GPUs the eval scheduler must leave free (coordinator 23:41 PT): the training jobs in the queue (running or
    # pending in Slurm) plus the next arm about to be submitted, only while it fits the share; evals fill the rest.
    in_queue = sum(block_gpus(b) for b in state["blocks"] if b["current"] and b["current"].get("job")
                   and b["current"].get("slurm_state", "PENDING") not in TERMINAL)
    about = [block_gpus(b) for b in state["blocks"]
             if (b["current"] and not b["current"].get("job")) or (not b["current"] and open_block(b))]
    held = in_queue + (about[0] if about and in_queue + about[0] <= state["share"] else 0)
    wave1 = ([state["blocks"][i] for i in state["wave1_blocks"]] if "wave1_blocks" in state
             else [b for b in state["blocks"] if not b.get("not_before")])
    if (now() >= START and now() < END and wave1
            and not any(open_block(b) for b in wave1)):
        held += 48  # the open-model cascade's GPUs once wave 1 has ended (coordinator)
    held = min(held, state["share"])
    write_int(RESERVE_FILE, held)
    save(state)
    parked, pending = HOME / "actions/margin_hold", HOME / "actions/pending"
    parked.mkdir(exist_ok=True)
    if tenth is not None:
        for f in sorted(pending.glob("g_*sbatchmn_*.json")):
            if not margin_ok(int(json.loads(f.read_text()).get("gpus", 32))):
                f.rename(parked / f.name)
                log(f"parked {f.name}: margin {tenth - ours} below 80 + job")
        for f in sorted(parked.glob("g_*sbatchmn_*.json")):
            if margin_ok(int(json.loads(f.read_text()).get("gpus", 32))):
                f.rename(pending / f.name)
                log(f"released {f.name}: margin {tenth - ours}")
    # Status probe for the current arms (job log steps, mean step seconds, publication), run in this poll.
    targets = " ".join(f'{c["name"]}:{c["job"]}:{c["run"]}' for c in (b["current"] for b in state["blocks"])
                       if c and c.get("job"))
    lines = [f"python3 - {BASE} {RUNS} {targets or 'none'} <<'PY'",
             "import glob, json, os, re, sys",
             "base, runs = sys.argv[1:3]",
             "for item in sys.argv[3:]:",
             "    if item == 'none':",
             "        continue",
             "    name, job, run = re.fullmatch(r'([^:]+):([^:]+):(.+)', item).groups()",
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
             "PY",
             "F=" + RUNS + "/frozen",
             "for a in " + (" ".join(sorted({b["chain"][b["next"]] for b in state["blocks"]
                                            if b.get("hold") and b["next"] < len(b["chain"])}
                                           | (set(state.get("await_admission", [])) - set(state.get("admitted", [])))))
                            or "none") + "; do",
             "  [ -f $F/$a/ADMISSION.json ] && grep -q CPU_ADMISSION_OK $F/$a/ADMISSION.json && echo R1ADMITTED $a",
             "done; true",
             "export PATH=/cm/shared/apps/slurm/current/bin:$PATH",
             "squeue -h -t R -o '%u|%b|%D' | python3 -c \"import re,sys,collections; c=collections.Counter(); "
             "[c.update({m.group(1): int(m.group(2)) * int(m.group(3))}) for m in (re.fullmatch(r'([^|]+)[|].*?gpu(?::[A-Za-z0-9_-]+)?:([0-9]+)[|]([0-9]+)', l.strip()) for l in sys.stdin) if m]; "
             "top=sorted(c.values(), reverse=True); print('R1MARGIN', top[9] if len(top) > 9 else 0, c.get('jyeung', 0))\"",
             "squeue -h -u jyeung -t R,PD,CF -o '%j|%b|%D' | python3 -c \"import re,sys; print('R1TOTAL', sum(int(m.group(2)) * int(m.group(3)) for m in (re.fullmatch(r'(a15_cot_ap[^|]*)[|].*?gpu(?::[A-Za-z0-9_-]+)?:([0-9]+)[|]([0-9]+)', l.strip()) for l in sys.stdin) if m))\""]
    probe = NIGHT / "probe.sh"
    probe.write_text("\n".join(lines) + "\n")
    subprocess.check_output([PY, "-B", str(TOOLS / "r1actions.py"), "sh", "n_probe", str(probe)], text=True)
    result = subprocess.run([PY, "-B", str(TOOLS / "r1aws.py"), "run"], capture_output=True, text=True,
                            env=dict(os.environ, R1_MIN_INTERVAL="55"), timeout=900)
    for f in (HOME / "actions/pending").glob("a_*n_probe.json"):
        f.rename(HOME / "actions/sent" / f.name)  # one probe per tick, whatever its exit code
    log("poll: " + " ".join(result.stdout.split()[:6]) + f" rc={result.returncode} active={active}"
        + ("" if result.stdout.strip() else " stderr: " + " ".join(result.stderr.split()[-30:])))
    print(60 if waiting_steps else 600)


if __name__ == "__main__":
    {"plan": plan, "tick": tick}[sys.argv[1]]()
