"""Paired comparison of two arms on shared LIBERO episodes (pre-registered readout, design record 4.1 as revised with
vla_schema_v1). Episodes pair by (suite, category, task_id, trial = init state); only pairs both arms finished count.

For the pooled cell: n pairs, discordant counts b (A succeeds, B fails) and c (A fails, B succeeds), d = (b - c) / n in
points, the exact two-sided McNemar p on (b, c), a Wald interval from the discordances (se = sqrt(b + c - (b - c)^2/n)/n),
and the primary paired bootstrap: 10,000 resamples stratified by task (episodes resampled within each task), seed 0,
giving the 95% and 90% intervals; a bootstrap over whole tasks is reported as a sensitivity read. Outcome (design 4.1):
  GAIN          the 95% CI's lower bound > 0
  HARM          the 95% CI's upper bound < 0
  EQUIVALENT    the 90% CI lies inside (-3, +3)
  INCONCLUSIVE  otherwise
Validity (--blind, one or more prior dirs): an arm must beat every prior by >= 10 points with the 95% lower bound > 0.
A cell with fewer than 100 pairs is flagged TOO_FEW_PAIRS. Per-task rows are descriptive only.
Family (--family "A1,B1;A2,B2;..."; vla_schema_v2, design 4.1 attribution checks): the comparisons form one Holm family;
a member is GAIN iff its Holm-adjusted exact McNemar p < 0.05 and its 95% CI excludes 0 on the positive side, HARM
likewise on the negative side, EQUIVALENT iff its 90% CI lies inside +-3, INCONCLUSIVE otherwise.
usage: compare_arms.py A_DIR B_DIR [--suites s1,s2] [--blind BLIND_DIR[,DIR2]] [--family "A,B;..."] [--json OUT]
  A_DIR / B_DIR: a checkpoint's eval dir (e.g. runs/<id>/eval/step_10000); every <suite>/w*.jsonl below it is read."""
import argparse, collections, glob, json, os
import numpy as np


def load(d, suites):
    rows = {}
    for f in glob.glob(os.path.join(d, "**", "*.jsonl"), recursive=True):
        for line in open(f):
            r = json.loads(line)
            if suites and r["suite"] not in suites:
                continue
            key = (r["suite"], r.get("category") or "", r["task_id"], r["trial"])
            rows[key] = bool(r["success"])
    return rows


def boot_stratified(diff, groups, n_boot=10000, seed=0):
    """Resample episodes with replacement inside each task; the statistic is the pooled mean difference."""
    rng = np.random.default_rng(seed)
    s = np.zeros(n_boot)
    for g in np.unique(groups):
        m = diff[groups == g]
        s += m[rng.integers(0, len(m), (n_boot, len(m)))].sum(1)
    return s / len(diff) * 100


def boot_tasks(diff, groups, n_boot=10000, seed=0):
    rng = np.random.default_rng(seed)
    ug = np.unique(groups); members = [np.flatnonzero(groups == g) for g in ug]
    s = np.empty(n_boot)
    for i in range(n_boot):
        ix = np.concatenate([members[j] for j in rng.integers(0, len(ug), len(ug))])
        s[i] = diff[ix].mean() * 100
    return s


def mcnemar_exact(b, c):
    from math import factorial
    comb = lambda n_, k_: factorial(n_) // (factorial(k_) * factorial(n_ - k_))
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return float(min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n))


def outcome(ci95, ci90, n):
    if n < 100:
        return "TOO_FEW_PAIRS"
    if ci95[0] > 0:
        return "GAIN"
    if ci95[1] < 0:
        return "HARM"
    if ci90[0] > -3 and ci90[1] < 3:
        return "EQUIVALENT"
    return "INCONCLUSIVE"


def compare(A, B):
    keys = sorted(set(A) & set(B))
    x = np.array([A[k] for k in keys]); y = np.array([B[k] for k in keys]); n = len(keys)
    if n == 0:
        return {"pairs": 0}
    b, c = int((x & ~y).sum()), int((~x & y).sum())
    d = (b - c) / n * 100
    se = np.sqrt(max(b + c - (b - c) ** 2 / n, 0)) / n * 100
    groups = np.array([f"{k[0]}|{k[1]}|{k[2]}" for k in keys])
    diff = x.astype(float) - y.astype(float)
    sb, tb = boot_stratified(diff, groups), boot_tasks(diff, groups)
    ci95 = [float(np.percentile(sb, 2.5)), float(np.percentile(sb, 97.5))]
    ci90 = [float(np.percentile(sb, 5)), float(np.percentile(sb, 95))]
    res = {"pairs": n, "rate_a": float(x.mean() * 100), "rate_b": float(y.mean() * 100), "b_a_only": b, "c_b_only": c,
           "discordance": (b + c) / n, "diff_points": d, "mcnemar_exact_p": mcnemar_exact(b, c),
           "ci95_boot_stratified": ci95, "ci90_boot_stratified": ci90, "ci95_wald": [d - 1.96 * se, d + 1.96 * se],
           "ci95_boot_tasks": [float(np.percentile(tb, 2.5)), float(np.percentile(tb, 97.5))], "outcome": outcome(ci95, ci90, n)}
    per = collections.defaultdict(lambda: [0, 0, 0])
    for k, xi, yi in zip(keys, x, y):
        p = per[f"{k[0]}:{k[2]}"]; p[0] += int(xi); p[1] += int(yi); p[2] += 1
    res["per_task_descriptive"] = {k: {"a": v[0], "b": v[1], "n": v[2]} for k, v in sorted(per.items())}
    return res


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i]); adj = [0.0] * len(ps); run = 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - r) * ps[i])); adj[i] = run
    return adj


def family(pairs, suites):
    rows = [compare(load(a, suites), load(b, suites)) for a, b in pairs]
    adj = holm([r["mcnemar_exact_p"] for r in rows])
    out = []
    for (a, b), r, p in zip(pairs, rows, adj):
        lo, hi = r["ci95_boot_stratified"]; e = r["ci90_boot_stratified"]
        name = ("TOO_FEW_PAIRS" if r["pairs"] < 100 else "GAIN" if p < 0.05 and lo > 0 else "HARM" if p < 0.05 and hi < 0
                else "EQUIVALENT" if e[0] > -3 and e[1] < 3 else "INCONCLUSIVE")
        out.append({"a": a, "b": b, "pairs": r["pairs"], "diff_points": r["diff_points"], "ci95": [lo, hi], "ci90": e,
                    "mcnemar_p": r["mcnemar_exact_p"], "holm_p": p, "outcome": name})
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("a"); ap.add_argument("b")
    ap.add_argument("--suites", default="")
    ap.add_argument("--blind", default="", help="comma list of blind-prior eval dirs: each arm must beat every prior by >= 10 points, 95% LB > 0")
    ap.add_argument("--json", default="")
    ap.add_argument("--family", default="", help='extra Holm family: "A1,B1;A2,B2;..." (the positional pair is not included)')
    a = ap.parse_args()
    suites = set(a.suites.split(",")) if a.suites else set()
    if a.family:
        fam = family([tuple(x.split(",")) for x in a.family.split(";") if x], suites)
        for f in fam:
            print(f"family {f['a']} - {f['b']}: d {f['diff_points']:+.1f}  95% {f['ci95']}  Holm p {f['holm_p']:.4g} -> {f['outcome']}")
    A, B = load(a.a, suites), load(a.b, suites)
    res = {"a": a.a, "b": a.b, "suites": sorted(suites) or "all", "pooled": compare(A, B)}
    for bd in [x for x in a.blind.split(",") if x]:
        Z = load(bd, suites)
        for name, X in (("a", A), ("b", B)):
            v = compare(X, Z)
            res.setdefault("validity", []).append({"arm": name, "prior": bd, "pairs": v.get("pairs"), "diff_points": v.get("diff_points"),
                                                   "ci95": v.get("ci95_boot_stratified"),
                                                   "passes": v.get("pairs", 0) >= 100 and v.get("diff_points", -1e9) >= 10 and v["ci95_boot_stratified"][0] > 0})
    if a.family:
        res["family"] = fam
    p = res["pooled"]
    print(f"pairs {p.get('pairs')}  A {p.get('rate_a', 0):.1f}%  B {p.get('rate_b', 0):.1f}%  d {p.get('diff_points', 0):+.1f} pts  "
          f"95% CI {p.get('ci95_boot_stratified')}  90% CI {p.get('ci90_boot_stratified')}  McNemar p {p.get('mcnemar_exact_p')}  -> {p.get('outcome')}")
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1)
