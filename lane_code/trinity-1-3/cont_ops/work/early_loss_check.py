"""Rule E (gross-loss alarm) for the LEG-S1 continuation: the new attempt's first three metrics rows against steps 530-544.
Usage: python3 -I early_loss_check.py JOB METRICS ATTEMPT  (files must be metrics_<JOB>.jsonl and attempt_<JOB>.json)
Prints one JSON verdict and exits 0 PASS, 3 PENDING, 2 ALARM. It is a secondary alarm, never proof of restore equality."""
import json, math, os, statistics, sys
# Four-rank mean of stream_means per step, steps 530-544 (median, MAD), computed on Orchard from the full
# metrics_169097.jsonl: 544 rows, 86,552,359 B, sha256 607fc9f232a967bb28097829ad9a84914f62507a37b6cae7e983a43f41c3449f.
BASE = {"pose": (0.16716301260748878, 0.00920307805063203), "vqa": (0.10068363906293598, 0.007336297720929252),
        "routing": (0.006104939058303671, 0.002742238399111585), "pointing": (0.5108491749192581, 0.02316714090966343)}
FIRST, MANIFEST_A = 545, "0450e3a3c0265131175d4751329eba9f4605a5f391450a0c98b4e6fdefddc31c"
CHECKPOINT_A = "checkpoint_000544_16d2a80ac22a411f8442277a87b53738"
def threshold(m, d): return max(0.5 * abs(m), 6 * 1.4826 * d, 1e-6)
def finite(x): return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
def attempt_problems(path):
    try: raw = open(path).read()
    except OSError: return None  # not yet persisted
    try: a = json.loads(raw)
    except ValueError: return ["attempt record unparseable"]
    if not isinstance(a, dict): return ["attempt record is not an object"]
    out = []
    if a.get("first_step") != FIRST: out.append(f"attempt first_step {a.get('first_step')} != {FIRST}")
    pin = a.get("resume")
    if (not isinstance(pin, dict) or set(pin) != {"path", "sha256"} or pin.get("sha256") != MANIFEST_A
            or not isinstance(pin.get("path"), str) or not pin["path"].endswith("/" + CHECKPOINT_A + "/complete.json")):
        out.append("attempt resume pin is not {path: .../%s/complete.json, sha256: %s}" % (CHECKPOINT_A, MANIFEST_A[:12]))
    return out
def main(job, metrics, attempt):
    if not job.isdigit() or os.path.basename(metrics) != f"metrics_{job}.jsonl" or os.path.basename(attempt) != f"attempt_{job}.json":
        print(json.dumps(dict(verdict="ALARM", problems=["file names do not belong to job " + job]))); return 2
    try: return evaluate(metrics, attempt)
    except Exception as exc:  # any malformed record is an alarm, never a crash
        print(json.dumps(dict(verdict="ALARM", problems=[f"malformed input: {type(exc).__name__}: {exc}"[:300]]))); return 2
def evaluate(metrics, attempt):
    problems, rows, partial = [], [], False
    try: lines = open(metrics, "rb").read().split(b"\n")
    except OSError: lines = []
    complete, tail = lines[:-1], lines[-1] if lines else b""
    partial = bool(tail.strip())  # an unterminated last line is an in-flight write, not evidence
    for n, line in enumerate(complete[:3]):
        try: r = json.loads(line)
        except ValueError: problems.append(f"row {n}: unparseable complete line"); continue
        rows.append(r)
    ap = attempt_problems(attempt)
    if ap is None: ap = [] if not rows else ["metrics present but attempt record missing"]
    problems += ap
    per = {}
    for n, r in enumerate(rows):
        want = FIRST + n
        if not isinstance(r, dict) or r.get("step") != want: problems.append(f"row {n}: step {r.get('step') if isinstance(r, dict) else None} != {want}"); continue
        ranks = r.get("ranks")
        if (not isinstance(ranks, list) or len(ranks) != 4 or not all(isinstance(k, dict) for k in ranks)
                or sorted(k.get("rank") for k in ranks) != [0, 1, 2, 3]):
            problems.append(f"step {want}: ranks not exactly 0-3"); continue
        if any(k.get("step") != want for k in ranks): problems.append(f"step {want}: rank step mismatch")
        means = {}
        for st in BASE:
            v = [(k.get("stream_means") or {}).get(st) for k in ranks]
            if not all(finite(x) for x in v): problems.append(f"step {want}: {st} missing or nonfinite"); continue
            means[st] = sum(v) / 4
        skipped = sum(len(k.get("skipped_microsteps") or []) for k in ranks)
        if skipped: problems.append(f"step {want}: {skipped} skipped microsteps")
        per[want] = dict(means=means, wall_seconds=ranks[0].get("wall_seconds"))
    out = dict(metrics=metrics, attempt=attempt, rows_read=len(rows), partial_tail=partial, per_step=per, problems=problems)
    if problems: out["verdict"] = "ALARM"
    elif len(rows) < 3: out["verdict"] = "PENDING"
    else:
        cmp = {}
        for st, (m, d) in BASE.items():
            med = statistics.median(per[s]["means"][st] for s in sorted(per)); t = threshold(m, d)
            cmp[st] = dict(median3=round(med, 5), baseline=m, threshold=round(t, 5), ok=abs(med - m) <= t)
        out["compare"] = cmp; out["verdict"] = "PASS" if all(c["ok"] for c in cmp.values()) else "ALARM"
    print(json.dumps(out, sort_keys=True))
    return {"PASS": 0, "PENDING": 3, "ALARM": 2}[out["verdict"]]
if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
