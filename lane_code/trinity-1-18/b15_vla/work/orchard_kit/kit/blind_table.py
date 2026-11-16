"""Table of the visually blind priors: success per cell with a Wilson 95% interval, per-task rates, and episode counts.
usage: blind_table.py BLIND_DIR [OUT.json]   (cells = subdirectories holding w*.jsonl)"""
import collections, glob, json, math, os, sys


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round(100 * (c - h) / d, 1), round(100 * (c + h) / d, 1)]


root = sys.argv[1]; res = {}
for d in sorted(glob.glob(os.path.join(root, "*"))):
    rows = []
    for f in glob.glob(os.path.join(d, "w*.jsonl")):
        for l in open(f):
            try:
                rows.append(json.loads(l))
            except ValueError:
                pass  # a line cut by a failed write
    if not rows or os.path.basename(d).startswith("smoke"):
        continue
    k = sum(r["success"] for r in rows); n = len(rows)
    per = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        per[r["task_id"]][0] += r["success"]; per[r["task_id"]][1] += 1
    res[os.path.basename(d)] = {"episodes": n, "success": k, "rate": round(100 * k / n, 1), "wilson95": wilson(k, n),
                                "tasks": len(per), "per_task_rate": {str(t): round(100 * v[0] / v[1], 1) for t, v in sorted(per.items())},
                                "mean_steps_success": round(sum(r["steps"] for r in rows if r["success"]) / max(k, 1), 1)}
print(f"{'cell':45s} {'episodes':>8s} {'success':>8s} {'rate':>6s}  wilson95")
for c, v in res.items():
    print(f"{c:45s} {v['episodes']:8d} {v['success']:8d} {v['rate']:6.1f}  {v['wilson95']}")
if len(sys.argv) > 2:
    json.dump(res, open(sys.argv[2], "w"), indent=1)
