"""k6tk runner (tokens only). usage:
  k6run.py vlist SHARD NSH            -> archive member names for this video shard
  k6run.py a|v SHARD NSH PAR LOCALDIR -> decode into LOCALDIR/store, results LOCALDIR/out.jsonl
Workers wa.py / wd.py are the k5f2 builders, unchanged."""
import gzip, json, os, sys
B = os.path.dirname(os.path.abspath(__file__))
F = os.path.dirname(B)
sys.path.insert(0, B)
plan = json.load(gzip.open(F + "/plan/PLAN.json.gz", "rt"))
kind, shard, nsh = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
if kind == "vlist":
    for t in sorted(plan["v"])[shard::nsh]:
        print(plan["v"][t]["n"])
    sys.exit(0)
par, L = sys.argv[4], sys.argv[5]
store = L + "/store"
os.makedirs(store, exist_ok=True)
if kind == "a":
    sub = {t: plan["a"][t] for t in sorted(plan["a"])[shard::nsh]}
    p = L + "/plan_a.json"
    json.dump(sub, open(p, "w"))
    import wa
    sys.argv = ["wa.py", p, store, "/data2/k6tk", L + "/out.jsonl", par]
    wa.main()
elif kind == "v":
    sub = {}
    for t in sorted(plan["v"])[shard::nsh]:
        e = dict(plan["v"][t])
        e["p"] = L + "/media/" + e.pop("n")
        sub[t] = e
    p = L + "/man_v.json.gz"
    with gzip.open(p, "wt") as f:
        json.dump({"v": sub}, f)
    c = L + "/conf.json"
    json.dump({"groups": {"d1": {"mode": "same", "out_wh": [640, 480]}, "d2": {"mode": "same", "out_wh": [640, 480]}}}, open(c, "w"))
    import wd
    sys.argv = ["wd.py", p, c, store, L + "/out.jsonl", par]
    wd.main()
