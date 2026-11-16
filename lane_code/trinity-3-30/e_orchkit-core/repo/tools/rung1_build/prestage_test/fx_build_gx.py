"""GX fixture: a sealed geometry feature store for every 32-frame selection of FXP_S17 (float16 [32, h, w, 2048], seeded
random values) and the frozen inputs of FXG_S17 = FXP_S17 plus the production A1GX geometry block (store re-pointed)."""
import hashlib, json, os, sys
from pathlib import Path
import numpy as np
FX = Path(os.environ["FX"])
src = FX / "runs/aws128p_20261025/frozen/FXP_S17"
dst = FX / "runs/aws128p_20261025/frozen/FXG_S17"
store = FX / "fs/fx01"
spec = json.load(open(sys.argv[1]))  # the A1GX prep spec: derive.geometry is the production block without the store
block = dict(spec["derive"]["geometry"])
D = block["feature_dim"]
training = json.loads((src / "training.json").read_text())
audits = {audit["qid"]: audit for audit in training["input_audits"]}
selections = {}
for row in training["rows"]:
    if row.get("student_input") is None:
        continue
    frames = [frame["sha256"] for frame in row["student_input"]["frames"]]
    t, gh, gw = audits[row["qid"]]["video_grid_thw"][0]
    grid = (gh // 2, gw // 2)
    assert selections.setdefault(tuple(frames), grid) == grid
store.mkdir(parents=True, exist_ok=True)
lines = []
for number, (frames, (h, w)) in enumerate(sorted(selections.items())):
    key = hashlib.sha256("\n".join(frames).encode()).hexdigest()
    relative = "f/%s/%s.npy" % (key[:2], key)
    path = store / relative
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        array = np.random.default_rng(number).standard_normal((32, h, w, D), dtype=np.float32).astype(np.float16)
        with open(path, "xb") as stream:
            np.save(stream, array, allow_pickle=False)
    lines.append(json.dumps({"key": key, "frames": list(frames), "file": relative,
                             "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "shape": [32, h, w, D],
                             "dtype": "float16", "layer": block["layer"], "encoder": block["encoder"]}, sort_keys=True) + "\n")
manifest = store / "manifest.jsonl"
data = "".join(lines).encode()
if not manifest.exists():
    manifest.write_bytes(data)
assert manifest.read_bytes() == data
block["store"] = {"manifest": str(manifest), "manifest_sha256": hashlib.sha256(data).hexdigest()}
dst.mkdir(parents=True, exist_ok=True)
for name in ("candidate_index.jsonl", "inherited_division.json"):
    if not (dst / name).exists():
        (dst / name).write_bytes((src / name).read_bytes())
config = json.loads((src / "config.json").read_text())
config["geometry"] = block
text = (json.dumps(config, indent=2, sort_keys=True) + "\n").encode()
if not (dst / "config.json").exists():
    (dst / "config.json").write_bytes(text)
assert (dst / "config.json").read_bytes() == text
print("store", manifest, len(lines), "selections; config", dst / "config.json")
