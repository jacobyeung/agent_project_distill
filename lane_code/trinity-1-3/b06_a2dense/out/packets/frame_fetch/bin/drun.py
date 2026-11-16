"""Dense-frame runner (tokens only). usage:
  drun.py vlist SHARD NSH            -> media archive member names for this video shard
  drun.py a|v SHARD NSH PAR LOCALDIR -> new frames into LOCALDIR/store, results LOCALDIR/out.jsonl
Workers: k6 wd.py unchanged (videos); wa_dense.py around k6 wa.py unchanged (ARKit range reads)."""
import gzip, json, os, sys
B = os.path.dirname(os.path.abspath(__file__))
F = os.path.dirname(B)
sys.path.insert(0, B)
kind, shard, nsh = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
if kind in ("vlist", "v"):
    tv = json.load(gzip.open(F + "/plan/tasks_v.json.gz", "rt"))["v"]
    toks = sorted(tv)[shard::nsh]
if kind == "vlist":
    for t in toks:
        print(tv[t]["n"])
    sys.exit(0)
par, L = sys.argv[4], sys.argv[5]
store = L + "/store"
os.makedirs(store, exist_ok=True)
if kind == "a":
    ta = json.load(open(F + "/plan/tasks_a.json"))
    p = L + "/tasks_a.json"
    json.dump({t: ta[t] for t in sorted(ta)[shard::nsh]}, open(p, "w"))
    import wa_dense
    sys.argv = ["wa_dense.py", B + "/wa.py", p, store, L + "/out.jsonl", par, "20"]
    wa_dense.main()
elif kind == "v":
    sub = {}
    for t in toks:
        e = dict(tv[t]); e["p"] = L + "/media/" + e.pop("n"); sub[t] = e
    p = L + "/man_v.json.gz"
    with gzip.open(p, "wt") as f:
        json.dump({"v": sub}, f)
    c = L + "/conf.json"
    json.dump({"groups": {"d1": {"mode": "same", "out_wh": [640, 480]}, "d2": {"mode": "same", "out_wh": [640, 480]}}}, open(c, "w"))
    import wd
    sys.argv = ["wd.py", p, c, store, L + "/out.jsonl", par]
    wd.main()
else:
    raise SystemExit(__doc__)
