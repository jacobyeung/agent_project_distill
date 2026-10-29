import json, os, sys
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
if os.environ.get("EXPECT_GEOMETRY") == "1" and not ("geometry_store" in m and "geometry_store" in n):
    ok = False
    print("DIFF geometry expected (EXPECT_GEOMETRY=1) but a run has no geometry store")
if "geometry_store" in m or "geometry_store" in n:
    same = m.get("geometry_store") == n.get("geometry_store") and m.get("geometry_store") is not None; ok &= same
    print(("SAME " if same else "DIFF ") + "geometry_store coverage %s" % json.dumps(n.get("geometry_store"), sort_keys=True))
    names = {name for s in m["steps"] for name in s["tensors"]}
    ok &= all("geometry_features" in s["tensors"] for s in m["steps"] + n["steps"])
    print("   step tensors:", sorted(names))
steps_same = m["steps"] == n["steps"]; ok &= steps_same
print(("SAME " if steps_same else "DIFF ") + "steps 1-3 microbatches: %d (step, rank, chunk) records: qids, weights, tensor shapes/dtypes/SHA256, input_ids" % len(m["steps"]))
print("   ranks covered per step:", sorted({(s["step"], s["rank"]) for s in m["steps"]}))
for s in m["steps"][:2]:
    print("   step", s["step"], "rank", s["rank"], "qids", s["qids"], "input_ids", s["tensors"]["input_ids"][:2], s["tensors"]["input_ids"][2][:12])
print("mirror seconds old", m["mirror_seconds"], "new", n["mirror_seconds"])
# The hooks must have engaged (new: every cache path; fallback: the trainer's own staging and mirror) and be pinned.
events = {name: (R / f"{name}_{MODE}.err").read_text() for name in ("rank0", "mirror")}
required = {"new": {"rank0": ("manifest_from_cache", "frames_attached", "input_manifest_from_cache"), "mirror": ("mirror_attached",)},
            "fallback": {"rank0": ("manifest_from_cache", "frames_unavailable", "stage_fallback"),
                         "mirror": ("frames_unavailable",)}}.get(MODE, {})
missing = [f"{name}:{event}" for name, wanted in required.items() for event in wanted
           if "AWS_PRESTAGE " + event + " " not in events[name]]
unpinned = any("AWS_PRESTAGE module_not_pinned" in text for text in events.values())
hooks_off = not any("AWS_PRESTAGE " in (R / f"{name}_old.err").read_text() for name in ("rank0", "mirror"))
hooks_ok = not missing and not unpinned and hooks_off
ok &= hooks_ok
print(("SAME " if hooks_ok else "DIFF ") + "hook events" + ("" if hooks_ok else f" missing {missing} unpinned {unpinned} old_path_hooked {not hooks_off}"))
print("PARITY", "PASS" if ok else "FAIL")
