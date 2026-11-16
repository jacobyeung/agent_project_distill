"""Check a B1 backbone dir against the base: same tensor names (minus mtp.*) and shapes; shard sha256 equal to
the export's full_weights.json; report which groups (language_model, visual, lm_head) differ from the base, and every
tensor whose stored dtype differs (the export stores some base-fp32 tensors such as linear_attn.A_log in bf16; the
trainer loads both arms with torch_dtype=bfloat16, so the arms see the same dtype)."""
import hashlib, json, os, sys
from safetensors import safe_open
d, base = sys.argv[1], sys.argv[2]
fw = json.load(open(os.path.join(d, "full_weights.json")))
for f in fw["files"]:
    h = hashlib.sha256()
    with open(os.path.join(d, f["name"]), "rb") as fh:
        for b in iter(lambda: fh.read(1 << 24), b""):
            h.update(b)
    assert h.hexdigest() == f["sha256"], ("sha mismatch", f["name"])
def tensors(root):
    idx = json.load(open(os.path.join(root, "model.safetensors.index.json")))["weight_map"]
    return {k: v for k, v in idx.items() if not k.startswith("mtp.")}
st, bt = tensors(d), tensors(base)
assert set(st) == set(bt), (sorted(set(st) ^ set(bt))[:10])
diff, dtd = {}, {}
bh = {s: safe_open(os.path.join(base, s), "pt") for s in set(bt.values())}
for shard in sorted(set(st.values())):
    with safe_open(os.path.join(d, shard), "pt") as fs:
        for k in fs.keys():
            g = "visual" if ".visual." in k else ("lm_head" if k.startswith("lm_head") else "language_model")
            a, b = fs.get_tensor(k), bh[bt[k]].get_tensor(k)
            assert a.shape == b.shape and a.is_floating_point() == b.is_floating_point(), (k, a.shape, b.shape, a.dtype, b.dtype)
            if a.dtype != b.dtype:
                dtd.setdefault(f"{b.dtype}->{a.dtype}", []).append(k)
            diff.setdefault(g, [0, 0]); diff[g][0] += 1; diff[g][1] += int(not bool((a == b).all()))
print("B1_CHECK_OK tensors", len(st), "changed/total per group", diff, "dtype diffs", {t: len(v) for t, v in dtd.items()})
json.dump({"tensors": len(st), "changed_per_group": diff, "shards_sha_ok": True, "dtype_diffs": dtd}, open(os.path.join(d, "B1_CHECK.json"), "w"))
