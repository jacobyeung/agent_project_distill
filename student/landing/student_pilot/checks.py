import importlib.metadata

import numpy as np
import torch
from accelerate import init_empty_weights
from safetensors import safe_open
from transformers import Qwen3VLConfig, Qwen3VLForConditionalGeneration
from transformers.video_utils import VideoMetadata

from .adapters import attach_adapters
from .batches import encode_arrays, encode_row, load_processor
from .common import MODEL, MODEL_REVISION, binding, load_json, write_once


def cpu_check(output_path, manifest_path=None):
    if torch.cuda.is_initialized():
        raise ValueError("CPU readiness must not initialize CUDA")
    config = Qwen3VLConfig.from_pretrained(MODEL, local_files_only=True)
    with init_empty_weights(include_buffers=True):
        model = Qwen3VLForConditionalGeneration(config)
        expected_shapes = {name: tuple(value.shape) for name, value in model.state_dict().items()}
        model, adapter_report = attach_adapters(model)
    index_path = MODEL / "model.safetensors.index.json"
    index = load_json(index_path)
    observed_shapes, shards = {}, []
    for name in sorted(set(index["weight_map"].values())):
        path = MODEL / name
        with safe_open(path, framework="pt", device="cpu") as archive:
            for key in archive.keys():
                observed_shapes[key] = tuple(archive.get_slice(key).get_shape())
                if index["weight_map"].get(key) != name:
                    raise ValueError(f"Checkpoint index has the wrong shard for {key}")
        shards.append({"path": str(path), "resolved_path": str(path.resolve()), "bytes": path.stat().st_size, "header_readable": True})
    if expected_shapes != observed_shapes:
        missing = sorted(set(expected_shapes) - set(observed_shapes))
        extra = sorted(set(observed_shapes) - set(expected_shapes))
        mismatched = [name for name in set(expected_shapes) & set(observed_shapes) if expected_shapes[name] != observed_shapes[name]]
        raise ValueError(f"Checkpoint/model mismatch: missing={missing}, extra={extra}, shapes={mismatched}")
    processor = load_processor()
    indices = [i * 7 for i in range(32)]
    metadata = VideoMetadata(total_num_frames=225, fps=30.0, frames_indices=indices, width=512, height=384)
    batch, processor_audit = encode_arrays(
        processor, "Synthetic processor boundary check, not a benchmark question.", [],
        np.zeros((32, 384, 512, 3), dtype=np.uint8), metadata, "synthetic target",
    )
    report = {
        "status": "CPU_READY", "gpu_smoke_passed": False, "cuda_initialized": torch.cuda.is_initialized(),
        "infrastructure_only": True, "detailed_distillation": False,
        "model_revision": MODEL_REVISION, "model_config": binding(MODEL / "config.json"),
        "checkpoint_index": binding(index_path), "checkpoint_tensor_shapes_verified": len(observed_shapes),
        "weight_verification": "Pinned local snapshot; all shard headers and tensor shapes checked, not a new whole-weight checksum",
        "shards": shards, "adapters": adapter_report,
        "versions": {name: importlib.metadata.version(name) for name in ("torch", "torchvision", "transformers", "peft", "accelerate", "numpy", "Pillow", "safetensors", "av")},
        "synthetic_processor_check": processor_audit,
        "synthetic_pixels_are_not_admitted_training_data": True,
    }
    if manifest_path is not None:
        from .admission import load_admitted_manifest
        manifest = load_admitted_manifest(manifest_path)
        report["manifest"] = binding(manifest_path)
        report["source_rgb_checks"] = [encode_row(processor, row)[1] for row in manifest["rows"]]
    if report["cuda_initialized"]:
        raise ValueError("CPU check unexpectedly initialized CUDA")
    write_once(output_path, report)
    return report
