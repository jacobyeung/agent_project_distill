"""Early-loss rule for the LEG-S1 continuation: steps 545-547 against the journal of steps 530-544.
Usage: python3 -I early_loss_check.py METRICS_JSONL [FIRST_STEP=545]. Prints one JSON verdict: PENDING, PASS or ALARM."""
import json, math, os, statistics, sys
BASE = {  # four-rank mean of stream_means per step, steps 530-544 of metrics_169097.jsonl (median, MAD)
    "pose": (0.16716, 0.0092), "vqa": (0.10068, 0.00734), "routing": (0.0061, 0.00275), "pointing": (0.51085, 0.02317)}
def threshold(m, d): return max(0.5 * abs(m), 6 * 1.4826 * d, 1e-6)
def main(path, first=545):
    rows, problems = {}, []
    size = os.path.getsize(path) if os.path.exists(path) else 0
    if size:
        with open(path, "rb") as h:
            for line in h:
                try: r = json.loads(line)
                except ValueError: problems.append("unparseable line"); continue
                if r.get("step", 0) <= first + 2: rows[r["step"]] = r
    seen = sorted(rows)
    if seen and seen[0] != first: problems.append(f"first step {seen[0]} != {first}")
    per = {}
    for s in seen[:3]:
        r = rows[s]; ranks = r.get("ranks", [])
        if sorted(k.get("rank") for k in ranks) != [0, 1, 2, 3]: problems.append(f"step {s}: ranks {[k.get('rank') for k in ranks]}")
        if any(k.get("step") != s for k in ranks): problems.append(f"step {s}: rank step mismatch")
        means = {}
        for st in BASE:
            v = [k.get("stream_means", {}).get(st) for k in ranks]
            if any(x is None or not isinstance(x, (int, float)) or not math.isfinite(x) for x in v): problems.append(f"step {s}: {st} nonfinite/missing"); continue
            means[st] = sum(v) / len(v)
        skipped = sum(len(k.get("skipped_microsteps", [])) for k in ranks)
        if skipped: problems.append(f"step {s}: {skipped} skipped microsteps")
        per[s] = dict(means=means, wall_seconds=ranks[0].get("wall_seconds") if ranks else None, skipped=skipped)
    out = dict(path=path, bytes=size, steps=seen[:3], per_step=per, problems=problems)
    if problems: out["verdict"] = "ALARM"
    elif len(seen) < 3: out["verdict"] = "PENDING"
    else:
        cmp = {}
        for st, (m, d) in BASE.items():
            med = statistics.median(per[s]["means"][st] for s in seen[:3]); t = threshold(m, d)
            cmp[st] = dict(median3=round(med, 5), baseline=m, threshold=round(t, 5), ok=abs(med - m) <= t)
        out["compare"] = cmp; out["verdict"] = "PASS" if all(c["ok"] for c in cmp.values()) else "ALARM"
    print(json.dumps(out, sort_keys=True))
if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 545)
