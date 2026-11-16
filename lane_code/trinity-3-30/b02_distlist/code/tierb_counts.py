"""Tier B counts (report only): 790 primary dev-S1 distance items, metre count from question text,
backend coverage of the 640 items outside the fixed list. Stdlib only."""
import hashlib, json, math, os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from unit_from_question import DISTANCE_TYPE, parse_unit

P = sys.argv[1]  # work/pull
OUT = sys.argv[2]
FIXED = sys.argv[3]  # frozen DISTANCE_LIST_DEVS1_150.jsonl
ITEMS = os.path.join(P, "b113/sj/mask_recall_run/kit/out/ITEMS.jsonl")
MAN = {"mask_cache_dense_aliases": "b113/sj/mask_recall_run/results/dense_aliases/MANIFEST.json",
       "mask_cache_dense": "b113/sj/mask_recall_run/results/dense/MANIFEST.json",
       "sam3_devs1_mask_run_P0": "b118/devs1_masks/out/MANIFEST.json"}
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()

rows = [json.loads(l) for l in open(ITEMS) if l.strip()]
dist = [r for r in rows if r["question_type"] == DISTANCE_TYPE]
prim = sorted((r for r in dist if r["stratum"] == "primary"), key=lambda r: r["qid"])
fixed = set(json.loads(l)["question_id"] for l in open(FIXED))
assert fixed == set(r["qid"] for r in prim if r["fixed"])
new = [r for r in prim if not r["fixed"]]

def units(S):
    c, bad, metre_rooms = Counter(), [], set()
    for r in S:
        u = parse_unit(r["question"], DISTANCE_TYPE)
        c[u["unit"] if u["status"] == "ok" else "status:" + u["status"]] += 1
        if u["status"] != "ok":
            bad.append({"qid": r["qid"], "status": u["status"], "mentions": u["mentions"], "question": r["question"]})
        elif u["unit"] == "meters":
            metre_rooms.add(r["room"])
    return c, bad, metre_rooms

ITEMS_UNIT = {"m": "meters", "cm": "centimeters", "ft": "feet", "in": "inches", "inch": "inches"}
caps = {k: {c["native"]: c for c in json.load(open(os.path.join(P, v)))["captures"]} for k, v in MAN.items()}
geo = set()
for grp in ("g3s32", "g3s64"):
    d = os.path.join(P, "b113", grp)
    for sub in os.listdir(d):
        geo.update(f[:-5] for f in os.listdir(os.path.join(d, sub)) if f.endswith(".json") and "__" in f)
res = {"items_file": {"path": "trinity-1-13 native_r2/work/obj/masks_4984fac22d84e8c5.tar:sj/mask_recall_run/kit/out/ITEMS.jsonl",
                      "sha256": sha(ITEMS), "rows": len(rows)},
       "distance_strata": dict(Counter(r["stratum"] for r in dist))}
for lab, S in (("primary790", prim), ("fixed150", [r for r in prim if r["fixed"]]), ("new640", new)):
    c, bad, mr = units(S)
    pairs = set((r["native"], o) for r in S for o in r["operands"])
    cov = {}
    for k, m in caps.items():
        cov[k] = {"captures": sum(x in m for x in set(r["native"] for r in S)),
                  "pairs": sum(x in m and o in m[x]["names"] for x, o in pairs),
                  "items_all_operands": sum(all(r["native"] in m and o in m[r["native"]]["names"] for o in r["operands"]) for r in S)}
    scene = lambda x: caps["mask_cache_dense"][x]["scene"].replace("/", "__")
    cov["geometry_8c58df1547371bdb"] = {"captures": sum(scene(x) in geo for x in set(r["native"] for r in S)),
                                        "items": sum(scene(r["native"]) in geo for r in S)}
    disagree_items_unit = sum(1 for r in S if parse_unit(r["question"], DISTANCE_TYPE)["unit"] != ITEMS_UNIT.get(r.get("unit")))
    res[lab] = {"items": len(S), "captures": len(set(r["native"] for r in S)), "rooms": len(set(r["room"] for r in S)),
                "operand_pairs": len(pairs), "units": dict(c), "metre_items": c["meters"], "metre_rooms": len(mr),
                "not_ok": bad, "parser_vs_items_unit_field_mismatch": disagree_items_unit, "coverage": cov}
m43, m = res["fixed150"]["metre_items"], res["primary790"]["metre_items"]
r43, r = res["fixed150"]["metre_rooms"], res["primary790"]["metre_rooms"]
res["halfwidth_scaling_from_13.6"] = {"by_items": round(13.6 * math.sqrt(m43 / m), 2), "by_rooms": round(13.6 * math.sqrt(r43 / r), 2)}
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "TIERB_COUNTS.json"), "w").write(json.dumps(res, indent=1, sort_keys=True) + "\n")
print(json.dumps({k: (v if k not in ("primary790", "fixed150", "new640") else {kk: vv for kk, vv in v.items() if kk != "not_ok"}) for k, v in res.items()}, indent=1, sort_keys=True))
