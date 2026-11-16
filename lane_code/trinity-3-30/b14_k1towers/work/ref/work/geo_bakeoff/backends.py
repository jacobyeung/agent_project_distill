import importlib
import json
import math
from contextlib import nullcontext
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

from .io import ASSETS, ROOT
from .safety import validate_device


@dataclass
class Prediction:
    depth: np.ndarray
    intrinsics: np.ndarray
    c2w: np.ndarray | None
    source_hw: tuple[int, int]
    metadata: dict = field(default_factory=dict)

    def validate(self, n):
        if self.depth.ndim != 3 or len(self.depth) != n or self.intrinsics.shape != (n, 3, 3):
            raise ValueError("Backend output does not cover every input frame")
        if not np.isfinite(self.depth).all() or np.any(self.depth < 0):
            raise ValueError("Backend depth must be finite and nonnegative")
        if not np.isfinite(self.intrinsics).all() or np.any(self.intrinsics[:, (0, 1), (0, 1)] <= 0):
            raise ValueError("Invalid backend calibration")
        if self.c2w is not None and (self.c2w.shape != (n, 4, 4) or not np.isfinite(self.c2w).all()):
            raise ValueError("Invalid backend trajectory")
        return self


def numpy(tensor):
    return tensor.detach().float().cpu().numpy()


def clean_depth(depth):
    return np.where(np.isfinite(depth) & (depth > 0), depth, 0).astype(np.float32)


def read_rgb(item):
    if isinstance(item, np.ndarray):
        if item.dtype != np.uint8 or item.ndim != 3 or item.shape[-1] != 3:
            raise ValueError("RGB frames must be uint8 [height,width,3]")
        return Image.fromarray(item)
    if isinstance(item, Image.Image):
        return item.convert("RGB")
    with Image.open(item) as image:
        return image.convert("RGB")


def pi3x_size(source_hw, pixel_limit=255000):
    h, w = source_hw
    scale = math.sqrt(pixel_limit/(h*w))
    target_w, target_h = w*scale, h*scale
    k, m = round(target_w/14), round(target_h/14)
    while k*m*14**2 > pixel_limit:
        if k/m > target_w/target_h:
            k -= 1
        else:
            m -= 1
    return max(1, m)*14, max(1, k)*14


def default_resolution(model):
    return 504 if model == "da3" else 518


def restore_intrinsics(intrinsics, processed_hw, source_hw, integer_centres=False):
    k = np.array(intrinsics, np.float64, copy=True)
    if integer_centres:
        k[..., :2, 2] += .5
    k[..., 0, :] *= source_hw[1] / processed_hw[1]
    k[..., 1, :] *= source_hw[0] / processed_hw[0]
    return k


def pointmap_intrinsics(points):
    points = np.asarray(points)
    n, h, w, _ = points.shape
    yy, xx = np.mgrid[:h, :w]
    pixels = (xx + .5 - w / 2, yy + .5 - h / 2)
    out = np.repeat(np.eye(3)[None], n, axis=0)
    out[:, 0, 2], out[:, 1, 2] = w / 2, h / 2
    for i in range(n):
        good = np.isfinite(points[i]).all(-1) & (points[i, :, :, 2] > 0)
        for axis in (0, 1):
            rays = points[i, :, :, axis] / np.maximum(points[i, :, :, 2], 1e-8)
            ok = good & (np.abs(rays) > .03) & (np.abs(rays) < 3)
            if ok.sum() < 100:
                raise ValueError("Not enough point-map rays to estimate focal length")
            ratios = pixels[axis][ok] / rays[ok]
            ratios = ratios[np.isfinite(ratios) & (ratios > 0)]
            if len(ratios) < 100:
                raise ValueError("Point-map focal fit is invalid")
            out[i, axis, axis] = float(np.median(ratios))
    return out


def weight_file(name, filename):
    path = ASSETS / name / filename
    if not path.is_file():
        raise FileNotFoundError(f"The approved checkpoint has not arrived: {path}")
    receipts = [json.loads(line) for line in (ASSETS / "downloads.jsonl").read_text().splitlines()]
    suffix = f"/{name}/{filename}"
    receipt = next((r for r in receipts if r["path"].endswith(suffix) and r["verified_expected_sha256"]), None)
    if not receipt or path.stat().st_size != receipt["bytes"]:
        raise ValueError(f"Checkpoint has no authenticated completed download: {path}")
    return path


def load_tied_state_dict(model, state):
    expanded, aliases, groups = dict(state), [], {}
    for key, value in model.state_dict(keep_vars=True).items():
        groups.setdefault(id(value), []).append(key)
    for keys in groups.values():
        present = next((key for key in keys if key in expanded), None)
        if present is not None:
            for key in keys:
                if key not in expanded:
                    expanded[key] = expanded[present]
                    aliases.append(key)
    model.load_state_dict(expanded, strict=True)
    return aliases


class Backend:
    def __init__(self, name, device="cpu", threads=8, go_file=None):
        validate_device(device, go_file)
        import torch
        if device != "cpu" and not device.startswith("cuda"):
            raise ValueError("Only explicit CPU or CUDA devices are supported")
        if not 1 <= threads <= 16:
            raise ValueError("CPU thread budget exceeded")
        torch.set_num_threads(threads)
        torch.set_num_interop_threads(1)
        torch.manual_seed(0)
        if device == "cuda":
            memory = torch.cuda.get_device_properties(0).total_memory
            if memory < 48_000_000_000:
                raise RuntimeError("This run card requires a 48 GB or larger GPU")
            torch.cuda.set_per_process_memory_fraction(min(1., 46 * 1024 ** 3 / memory))
        self.torch, self.name, self.device = torch, name, device
        self.model = self.load().to(device).eval()

    def load(self):
        torch, name = self.torch, self.name
        if name in ("moge2", "moge3"):
            if name == "moge3" and self.device == "cpu":
                raise RuntimeError("MoGe-3's released sparse refinement requires CUDA; CPU inference is unsupported")
            cls = importlib.import_module(f"moge.model.v{2 if name == 'moge2' else 3}").MoGeModel
            checkpoint = torch.load(weight_file(name, "model.pt"), map_location="cpu", weights_only=True)
            model = cls(**checkpoint["model_config"])
            model.load_state_dict(checkpoint["model"], strict=True)
            return model
        from safetensors.torch import load_file
        path = weight_file(name, "model.safetensors")
        if name == "pi3x":
            from pi3.models.pi3x import Pi3X
            model = Pi3X()
            model.load_state_dict(load_file(path, device="cpu"), strict=True)
            return model
        if name == "da3":
            from depth_anything_3.cfg import create_object, load_config
            from depth_anything_3.registry import MODEL_REGISTRY
            model = create_object(load_config(MODEL_REGISTRY["da3nested-giant-large"]))
            state = load_file(path, device="cpu")
            if not all(k.startswith("model.") for k in state):
                raise ValueError("Unexpected DA3 checkpoint namespace")
            self.checkpoint_aliases = load_tied_state_dict(model, {k[len("model."):]: v for k, v in state.items()})
            return model
        if name == "mapanything":
            from mapanything.models import MapAnything
            pin = json.loads((ROOT / "out/sources/dinov2_pin.json").read_text())
            original_load = torch.hub.load
            def local_hub(repo, model, *args, **kwargs):
                if str(repo).split(":")[0] != "facebookresearch/dinov2":
                    raise RuntimeError(f"Unstaged Torch Hub source: {repo}")
                kwargs.update(source="local", pretrained=False)
                return original_load(str(ASSETS / pin["relative_dir"]), model, *args, **kwargs)
            torch.hub.load = local_hub
            try:
                return MapAnything.from_pretrained(str(path.parent), local_files_only=True, strict=True)
            finally:
                torch.hub.load = original_load
        raise ValueError(f"Unknown model backend: {name}")

    def predict(self, image_paths, progress=None, resolution=None, tokens=3600):
        torch = self.torch
        with read_rgb(image_paths[0]) as first:
            source_hw = (first.height, first.width)
        for path in image_paths:
            with read_rgb(path) as im:
                if (im.height, im.width) != source_hw:
                    raise ValueError("Mixed input rasters require an explicit per-frame transform")
        with torch.inference_mode():
            if self.name in ("moge2", "moge3"):
                prediction = self._moge(image_paths, source_hw, tokens, progress)
            elif self.name == "pi3x":
                prediction = self._pi3(image_paths, source_hw, resolution)
            elif self.name == "da3":
                prediction = self._da3(image_paths, source_hw, resolution or default_resolution(self.name))
            elif self.name == "mapanything":
                prediction = self._mapanything(image_paths, source_hw, resolution or default_resolution(self.name))
            else:
                raise ValueError(self.name)
        if hasattr(self, "checkpoint_aliases"):
            prediction.metadata["shared_parameter_aliases_loaded"] = self.checkpoint_aliases
        return prediction.validate(len(image_paths))

    def amp(self):
        return self.torch.autocast("cuda", dtype=self.torch.bfloat16) if self.device.startswith("cuda") else nullcontext()

    def _moge(self, paths, source_hw, tokens, progress):
        depths, intrinsics = [], []
        for i, path in enumerate(paths):
            with read_rgb(path) as im:
                tensor = self.torch.from_numpy(np.asarray(im.convert("RGB")).copy()).permute(2, 0, 1).float().to(self.device) / 255
            kwargs = dict(num_tokens=tokens, apply_mask=False, use_fp16=self.device.startswith("cuda"))
            if self.name == "moge3":
                kwargs["refine_steps"] = 3
            output = self.model.infer(tensor, **kwargs)
            depths.append(clean_depth(numpy(output["depth"])))
            k = numpy(output["intrinsics"])
            k[0] *= source_hw[1]
            k[1] *= source_hw[0]
            intrinsics.append(k)
            if progress:
                progress(i + 1, len(paths))
        return Prediction(np.stack(depths), np.stack(intrinsics), None, source_hw,
                          {"metric": True, "pose_source": "none", "tokens": tokens, "refinement_steps": 3 if self.name == "moge3" else 0})

    def _pi3(self, paths, source_hw, resolution):
        h, w = source_hw
        if resolution is None:
            height, width = pi3x_size(source_hw)
        else:
            width = max(14, round(resolution * w / max(h, w) / 14) * 14)
            height = max(14, round(resolution * h / max(h, w) / 14) * 14)
        images = []
        for path in paths:
            with read_rgb(path) as im:
                image = np.asarray(im.convert("RGB").resize((width, height), Image.Resampling.LANCZOS)).copy()
            images.append(self.torch.from_numpy(image).permute(2, 0, 1).float() / 255)
        tensor = self.torch.stack(images).to(self.device)[None]
        with self.amp():
            output = self.model(tensor)
        local_points = numpy(output["local_points"])[0]
        k = restore_intrinsics(pointmap_intrinsics(local_points), (height, width), source_hw)
        return Prediction(clean_depth(local_points[..., 2]), k, numpy(output["camera_poses"])[0], source_hw,
                          {"metric": "approximate_metric_native", "intrinsics": "robust_point_ray_fit",
                           "processed_hw": [height, width], "resize_filter": "LANCZOS",
                           "resolution_protocol": "official_255000_pixels" if resolution is None else "explicit_max_edge_handicap"})

    def _da3(self, paths, source_hw, resolution):
        from depth_anything_3.utils.io.input_processor import InputProcessor
        images, _, _ = InputProcessor()([read_rgb(p) for p in paths], process_res=resolution,
                                        process_res_method="upper_bound_resize", num_workers=1, sequential=True)
        if images.ndim == 4:
            images = images[None]
        with self.amp():
            output = self.model(images.to(self.device), infer_gs=False, ref_view_strategy="saddle_balanced")
        depth = numpy(output["depth"])[0]
        extrinsics = numpy(output["extrinsics"])[0]
        if extrinsics.shape[-2:] == (3, 4):
            row = np.broadcast_to([0., 0., 0., 1.], (len(paths), 1, 4))
            extrinsics = np.concatenate([extrinsics, row], axis=1)
        k = restore_intrinsics(numpy(output["intrinsics"])[0], depth.shape[-2:], source_hw)
        return Prediction(clean_depth(depth), k, np.linalg.inv(extrinsics), source_hw,
                          {"metric": bool(output["is_metric"]), "processed_hw": list(depth.shape[-2:]),
                           "nested_scale": float(output["scale_factor"]), "process_res": resolution,
                           "resolution_protocol": "official_504" if resolution == 504 else "explicit_resolution_handicap"})

    def _mapanything(self, paths, source_hw, resolution):
        from mapanything.utils.image import preprocess_inputs
        h, w = source_hw
        width = max(14, round(resolution * w / max(h, w) / 14) * 14)
        height = max(14, round(resolution * h / max(h, w) / 14) * 14)
        views = preprocess_inputs([{"img": read_rgb(p).resize((width, height), Image.Resampling.BICUBIC)} for p in paths],
                                  resize_mode="fixed_size", size=(width, height), verbose=False)
        output = self.model.infer(views, memory_efficient_inference=True, minibatch_size=1,
                                  use_amp=self.device.startswith("cuda"), amp_dtype="bf16", apply_mask=False,
                                  mask_edges=False, apply_confidence_mask=False)
        depth = np.stack([numpy(p["depth_z"])[0, ..., 0] for p in output])
        k = restore_intrinsics(np.stack([numpy(p["intrinsics"])[0] for p in output]), depth.shape[-2:], source_hw,
                               integer_centres=True)
        c2w = np.stack([numpy(p["camera_poses"])[0] for p in output])
        return Prediction(clean_depth(depth), k, c2w, source_hw,
                          {"metric": True, "processed_hw": list(depth.shape[-2:]), "memory_efficient_minibatch": 1,
                           "intrinsics_pixel_convention": "integer_to_half_pixel_before_resize"})
