import json, sys
from pathlib import Path
R = Path(sys.argv[1]); MODE = sys.argv[2] if len(sys.argv) > 2 else "new"
print("== old vs", MODE)
a, b = json.loads((R / "rank0_old.json").read_text()), json.loads((R / f"rank0_{MODE}.json").read_text())
ok = True
for key in sorted(set(a) | set(b)):
    if key == "timings":
        continue
    same = a.get(key) == b.get(key)
    ok &= same
    print(("SAME " if same else "DIFF ") + key + ("" if key != "store_files" else f" ({len(a[key])} files)"))
    if key == "store_files" and not same:
        for name in sorted(set(a[key]) | set(b[key])):
            if a[key].get(name) != b[key].get(name):
                print("   ", name, (a[key].get(name) or "-")[:12], (b[key].get(name) or "-")[:12])
print("timings old", a["timings"]); print("timings new", b["timings"])
m, n = json.loads((R / "mirror_old.json").read_text()), json.loads((R / f"mirror_{MODE}.json").read_text())
for key in ("mirror_files", "mirror_record"):
    same = m[key] == n[key]; ok &= same
    print(("SAME " if same else "DIFF ") + key + (f" ({len(m[key])} files)" if key == "mirror_files" else ""))
steps_same = m["steps"] == n["steps"]; ok &= steps_same
print(("SAME " if steps_same else "DIFF ") + "steps 1-3 microbatches: %d (step, rank, chunk) records: qids, weights, tensor shapes/dtypes/SHA256, input_ids" % len(m["steps"]))
for s in m["steps"][:2]:
    print("   step", s["step"], "rank", s["rank"], "qids", s["qids"], "input_ids", s["tensors"]["input_ids"][:2], s["tensors"]["input_ids"][2][:12])
print("mirror seconds old", m["mirror_seconds"], "new", n["mirror_seconds"])
print("PARITY", "PASS" if ok else "FAIL")
