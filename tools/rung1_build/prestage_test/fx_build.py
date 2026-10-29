"""Build the local CPU fixture: fake weight shards, frames under data2root, row payloads, frozen inputs (cold config)."""
import hashlib, json, os, shutil, sys, tarfile
from pathlib import Path
FX = Path(os.environ["FX"]); RP = Path("/scratch/jjyeung/rung1_push"); TB = RP / "test_build"
snap = next((FX / "runs/aws128p_20261025/models/models--Qwen--Qwen3.5-9B/snapshots").iterdir())
index = json.loads((snap / "model.safetensors.index.json").read_text())
for i, name in enumerate(sorted(set(index["weight_map"].values()))):
    path = snap / name
    if not path.exists():
        path.write_bytes(hashlib.sha256(name.encode()).digest() * (65536 + 4096 * i))  # ~2 MB placeholders
needed = json.loads((TB / "FRAMES_NEEDED.json").read_text())
root = FX / "data2root"
placed = 0
for part in sorted((RP / "frames").glob("frames_*.json")):
    table = json.loads(part.read_text())
    with open(part.with_suffix(".tar"), "rb") as stream:
        for digest, (offset, size) in table.items():
            if digest not in needed:
                continue
            target = root / Path(needed[digest]).relative_to("/data2")
            if target.exists():
                continue
            stream.seek(offset)
            data = stream.read(size)
            assert hashlib.sha256(data).hexdigest() == digest
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            placed += 1
print("frames placed", placed, "of needed", len(needed))
frozen = FX / "runs/aws128p_20261025/frozen/FXP_S17"
frozen.mkdir(parents=True, exist_ok=True)
with tarfile.open(TB / "frozen_inputs.tar.gz") as t:
    for name in ("candidate_index.jsonl", "inherited_division.json", "config.json"):
        data = t.extractfile("frozen/RG1T_P_S17/" + name).read()
        if name == "config.json":
            config = json.loads(data)
            config.pop("init_adapter")
            config["world_size"] = 4
            data = (json.dumps(config, indent=2, sort_keys=True) + "\n").encode()
        if not (frozen / name).exists():
            (frozen / name).write_bytes(data)
print("frozen", frozen)
