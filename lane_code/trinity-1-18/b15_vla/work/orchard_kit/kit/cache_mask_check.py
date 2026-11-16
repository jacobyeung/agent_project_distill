"""Checks of vl_data_patch's where-cache reader and the schema mask (integration breaks 5-7; CPU, synthetic caches).
1. a root whose MANIFEST.json carries another schema id is refused;
2. two roots holding the same episode id return their own outputs (memoised per resolved root and episode);
3. a corrupt entry (content sha mismatch) is refused;
4. the hook's _prepare turns the schema's fp32 [K] action_mask into StarVLA's [K, 7] bool mask, and a [K, 7] mask
   passes through. usage: cache_mask_check.py WORK_DIR"""
import hashlib, json, os, sys
import numpy as np
import vl_data_patch as P
import vl_heads_hook as H

work = sys.argv[1]; os.makedirs(work, exist_ok=True); res = {}


def make_root(name, schema, value, corrupt=False):
    root = os.path.join(work, name); os.makedirs(os.path.join(root, "episodes"), exist_ok=True)
    json.dump({"schema": schema, "pins": {}, "provider_sha": name}, open(os.path.join(root, "MANIFEST.json"), "w"))
    recs = [{"t": 0, "key": "k", "output": {"entities": [], "line": value, "meta": {}}}]
    sha = hashlib.sha256(P._json(recs).encode()).hexdigest()
    json.dump({"episode": "libero_spatial/task00/ep000001", "records": recs, "content_sha256": "0" * 64 if corrupt else sha},
              open(os.path.join(root, "episodes", "libero_spatial__task00__ep000001.json"), "w"))
    return root


eid = "libero_spatial/task00/ep000001"
a, b = make_root("rootA", P.CACHE_SCHEMA, "A"), make_root("rootB", P.CACHE_SCHEMA, "B")
old = make_root("rootOld", "vla_schema_v1/where_cache_key", "old")
bad = make_root("rootBad", P.CACHE_SCHEMA, "bad", corrupt=True)
res["two_roots"] = [P.where_output(a, eid, 0)["line"], P.where_output(b, eid, 0)["line"]]
for name, root in (("wrong_schema_refused", old), ("corrupt_refused", bad)):
    try:
        P.where_output(root, eid, 0); res[name] = False
    except ValueError:
        res[name] = True
ex = [{"lang": "x", "action": np.zeros((8, 7), np.float32), "action_mask": np.array([1] * 5 + [0] * 3, np.float32)},
      {"lang": "x", "action": np.zeros((8, 7), np.float32), "action_mask": np.ones((8, 7), bool)}]
out = H._prepare(ex, training=True)
res["mask_k_to_k7"] = list(out[0]["action_mask"].shape) == [8, 7] and out[0]["action_mask"].dtype == bool and out[0]["action_mask"][:, 0].tolist() == [True] * 5 + [False] * 3
res["mask_k7_passes"] = list(out[1]["action_mask"].shape) == [8, 7]
res["verdict"] = "CACHE_MASK_OK" if (res["two_roots"] == ["A", "B"] and res["wrong_schema_refused"] and res["corrupt_refused"]
                                     and res["mask_k_to_k7"] and res["mask_k7_passes"]) else "CACHE_MASK_FAIL"
print(json.dumps(res)); print(res["verdict"])
