import argparse
import importlib
import json
import os
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = ""

from geo_bakeoff.inputs import dense_tower, fixture_images, TOWER
from geo_bakeoff.io import ASSETS, ROOT, dump_json, sha256, utc
from geo_bakeoff.paths import path as data_path
from geo_bakeoff.reference import modules
from geo_bakeoff.selectors import deployed_tables


parser = argparse.ArgumentParser()
parser.add_argument("--weights", action="store_true")
args = parser.parse_args()
seal = json.loads((ROOT / "KIT_SEAL.json").read_text())
for relative, digest in seal["files"].items():
    if sha256(ROOT / relative) != digest:
        raise ValueError(f"Sealed code changed: {relative}")
versions = {}
for name in ("numpy", "scipy", "torch", "torchvision", "cv2", "av", "PIL", "timm", "e3nn", "uniception",
             "omegaconf", "safetensors", "huggingface_hub", "matplotlib", "utils3d_moge",
             "moge.model.v2", "mapanything.models", "depth_anything_3.cfg", "depth_anything_3.registry",
             "depth_anything_3.utils.io.input_processor", "pi3.models.pi3x"):
    module = importlib.import_module(name)
    if module.__file__ and not Path(module.__file__).resolve().is_relative_to(ROOT):
        raise ValueError(f"Runtime import escaped the kit: {name}: {module.__file__}")
    versions[name] = getattr(module, "__version__", None)
import torch
if torch.cuda.is_initialized():
    raise RuntimeError("CPU verification must not initialize CUDA")
paths, frames, fixture = fixture_images(64)
assert len(paths) == len(frames) == 64
scenes = sorted(p.stem.split("__", 1)[1] for p in TOWER.glob("scannet__*.npz"))
assert len(scenes) == 312
for scene in scenes:
    baseline, cameras, dense_frames, slots, source_hw = dense_tower(scene)
    assert len(cameras) == len(dense_frames) == 64 and len(slots) == 32
os.environ["GEO_BAKEOFF_FUSION_SOURCE"] = "policy"
ref = modules()
questions = ref["run_tg"].items()
assert len(questions) == 7353
tables = deployed_tables()
assert tables[-1]["tau_count"] == .15 and tables[-1]["thr_merge"] == .2
ledger = [json.loads(line) for line in (ASSETS / "downloads.jsonl").read_text().splitlines()]
weights = {}
for model in ("moge2", "mapanything", "da3", "pi3x", "moge3"):
    filename = "model.pt" if model.startswith("moge") else "model.safetensors"
    path = ASSETS / model / filename
    receipt = next(r for r in ledger if r["path"].endswith(f"/{model}/{filename}") and r["verified_expected_sha256"])
    assert path.stat().st_size == receipt["bytes"]
    if args.weights:
        assert sha256(path) == receipt["sha256"]
    weights[model] = {"bytes": path.stat().st_size, "sha256_checked": args.weights, "expected_sha256": receipt["sha256"]}
result = {"checked_at": utc(), "verdict": "COMPLETE", "scope": "CPU portability and frozen inputs; CUDA capacity is not tested",
          "kit_sha256": sha256(ROOT / "KIT_SEAL.json"), "scenes": len(scenes), "items": len(questions),
          "fixture_frames": len(frames), "runtime": versions, "weights": weights, "gpu_initialized": False}
dump_json(ROOT / "out/receipts/kit_integrity.json", result, replace=True)
print(json.dumps(result, indent=2))
