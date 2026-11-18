"""D0 job B steps 1-3 gross-failure check (ORCH ruling 20261116T0731Z, replaces stop-rule item 4's loss check).
Usage: python3 -I early_loss_check_d0.py JOB METRICS ATTEMPT [VQA_REF]   (files metrics_<JOB>.jsonl, attempt_<JOB>.json)
Per step the four-rank mean of stream_means is used.
- Pose, pointing: ALARM if non-finite on any rank, or above 1.5 x max(step 544's steps 530-544) on two consecutive steps;
  outside the MAD bounds of BASELINE_530_544 but under that limit: WARN.
- VQA: ALARM if non-finite, if step 1 is above 1.5 x VQA_REF (the stage-2 CPU first-batch VQA loss; omitted -> not used),
  or if step 3 is more than 50% above step 1. Step 544's range is reported for information.
- Routing: exempt, reported (non-finite routing is reported as a WARN).
Verdicts: PASS (3 rows, no alarm) exit 0, PENDING exit 3, ALARM exit 2, ERROR (unreadable or structurally wrong input) exit 4."""
import json, math, sys
# m544 steps 530-544, four-rank means: median, MAD, min, max (work/BASELINE_530_544.json)
BASE = {"pose": dict(median=0.16716, lo=0.08358, hi=0.25074, min=0.14126, max=0.18167),
        "vqa": dict(median=0.10068, lo=0.03539, hi=0.16597, min=0.08971, max=0.11156),
        "routing": dict(median=0.0061, lo=-0.01836, hi=0.03056, min=0.00128, max=0.02045),
        "pointing": dict(median=0.51085, lo=0.25543, hi=0.76628, min=0.45303, max=0.5789)}
FIRST = 1
def finite(x): return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
def main(job, metrics, attempt, vqa_ref=None):
    out = dict(metrics=metrics, attempt=attempt, vqa_ref=vqa_ref, errors=[], alarms=[], warns=[], per_step={})
    if not job.isdigit() or not metrics.endswith(f"metrics_{job}.jsonl") or not attempt.endswith(f"attempt_{job}.json"):
        out["errors"].append("file names do not belong to job " + job)
    try: lines = open(metrics, "rb").read().split(b"\n")[:-1]  # an unterminated last line is an in-flight write
    except OSError: lines = []
    try:
        a = json.load(open(attempt))
        if a.get("first_step") != FIRST: out["warns"].append(f"attempt first_step {a.get('first_step')} != {FIRST}")
        if a.get("resume") not in (None, {}): out["warns"].append("attempt carries a resume pin")
        out["init_artifact"] = ((a.get("init") or {}).get("artifact") or {}).get("path")
    except OSError: out["warns"].append("attempt record absent")
    except (ValueError, AttributeError): out["errors"].append("attempt record unreadable")
    m = {}
    for n, line in enumerate(lines[:3]):
        want = FIRST + n
        try: r = json.loads(line); ranks = r["ranks"]
        except (ValueError, KeyError, TypeError): out["errors"].append(f"row {n} unreadable"); break
        if r.get("step") != want or not isinstance(ranks, list) or sorted(k.get("rank") for k in ranks) != [0, 1, 2, 3] \
                or any(k.get("step") != want for k in ranks):
            out["errors"].append(f"row {n}: step or ranks not {want} x 0-3"); break
        means = {}
        for st in BASE:
            v = [(k.get("stream_means") or {}).get(st) for k in ranks]
            if all(finite(x) for x in v): means[st] = sum(v) / 4
            elif st == "routing": out["warns"].append(f"step {want}: routing non-finite or missing")
            else: out["alarms"].append(f"step {want}: {st} non-finite or missing on a rank")
        sk = sum(len(k.get("skipped_microsteps") or []) for k in ranks)
        if sk: out["warns"].append(f"step {want}: {sk} skipped microsteps")
        m[want] = means
        out["per_step"][want] = dict(means={k: round(v, 5) for k, v in means.items()}, wall_seconds=ranks[0].get("wall_seconds"))
    for st in ("pose", "pointing"):
        lim = 1.5 * BASE[st]["max"]; over = [s for s in sorted(m) if st in m[s] and m[s][st] > lim]
        if any(s + 1 in over for s in over): out["alarms"].append(f"{st} above {lim:.5f} on two consecutive steps {over}")
        for s in sorted(m):
            if s in over: out["warns"].append(f"step {s}: {st} {m[s][st]:.5f} above {lim:.5f}")
            elif st in m[s] and not BASE[st]["lo"] <= m[s][st] <= BASE[st]["hi"]:
                out["warns"].append(f"step {s}: {st} {m[s][st]:.5f} outside MAD bounds [{BASE[st]['lo']}, {BASE[st]['hi']}]")
    v1, v3 = m.get(1, {}).get("vqa"), m.get(3, {}).get("vqa")
    if vqa_ref is not None and v1 is not None and v1 > 1.5 * vqa_ref:
        out["alarms"].append(f"step 1 VQA {v1:.5f} above 1.5 x stage-2 reference {vqa_ref:.5f}")
    if v1 is not None and v3 is not None and v3 > 1.5 * v1: out["alarms"].append(f"VQA rose >50% from step 1 {v1:.5f} to step 3 {v3:.5f}")
    out["reference"] = dict(BASE, pose_limit=1.5 * BASE["pose"]["max"], pointing_limit=1.5 * BASE["pointing"]["max"],
                            vqa_limit=None if vqa_ref is None else 1.5 * vqa_ref)
    out["verdict"] = "ALARM" if out["alarms"] else "ERROR" if out["errors"] else "PASS" if len(m) == 3 else "PENDING"
    print(json.dumps(out, sort_keys=True))
    return {"PASS": 0, "PENDING": 3, "ALARM": 2, "ERROR": 4}[out["verdict"]]
if __name__ == "__main__":
    try: sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else None))
    except Exception as exc:
        print(json.dumps(dict(verdict="ERROR", errors=[f"{type(exc).__name__}: {exc}"[:300]]))); sys.exit(4)
