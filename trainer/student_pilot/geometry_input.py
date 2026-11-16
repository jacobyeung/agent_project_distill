"""Geometry input (schema geometry-input-v1), shared byte-identical by the trainer and the evaluator.

A frozen multi-view encoder (G3T, the gravity-aligned VGGT-1B fine-tune of the tool harness) runs once per video on the
same 32 RGB frames the student sees. Its patch tokens from one aggregator layer are pooled to the student's merged
video-token grid (one cell per 2x2 merged patch, per frame) and stored per video in a feature store. In the student,
the two frames of each temporal patch are concatenated, a projector (LayerNorm, Linear, GELU, Linear with a
zero-initialised output layer) maps them to the language-model width, and the result is added to the merged video
tokens before they enter the language model. At initialisation the projector outputs zeros, so the student starts
exactly at its warm start. The token count, prompt, positions and every other input stay unchanged.

A second injection, cross_attend_merged_video_tokens, replaces the projector by frame-strict cross-attention: each merged
video token of temporal patch t queries the geometry cells of the two frames 2t and 2t+1 of the same video (2*h*w keys,
a fixed 2D sinusoidal code of the normalized cell centre on queries and keys, a learned slot embedding per frame on the
keys), and the zero-initialised output layer adds the result to the token.

A third injection, add_spatial_mllm_connector_to_merged_video_tokens, replicates Spatial-MLLM's mlp_add connector
(arXiv 2505.23747; code src/qwenvl/model/connector/mlp_add_connector.py): the store holds G3T cells on the student's
unmerged patch grid (2h, 2w); for each merged video token the 2x2 spatial cells of both frames of its temporal patch are
concatenated (merged width 8 * feature_dim, Spatial-MLLM's permute order), normalized by an RMSNorm (eps 1e-6) and passed
through Linear(merged, merged), GELU, Linear(merged, output); the result is added to the merged video tokens. The
initialization is the source's effective one: Spatial-MLLM builds the connector inside its Qwen2.5-VL model, so
from_pretrained's missing-key pass applies Qwen2_5_VLPreTrainedModel._init_weights (Linear weights N(0, 0.02), the
checkpoint's initializer_range; biases 0) and leaves the RMSNorm weight at ones (transformers 4.51.3, the source's pin).

A fourth injection, add_gated_spatial_mllm_connector_to_merged_video_tokens, keeps that connector and its init and bounds
its contribution: the connector output is normalized by a LayerNorm without affine parameters (Swin Transformer V2's
res-post-norm, arXiv 2111.09883) and scaled by Flamingo's tanh gate (arXiv 2204.14198), a learned scalar alpha that starts
at 0. The added delta is tanh(alpha) * LayerNorm(connector(x)), so every token's delta norm is exactly
|tanh(alpha)| * sqrt(output width), whatever the connector's weights do, and the student starts at its warm start.

The settings name exactly one of the (injection, projector) pairs; the module class follows from them.

Store layout: a JSON-lines manifest beside the feature files. Each row is
  {"key": frame_key(frames), "frames": [32 PNG sha256], "file": relative path of a .npy, "sha256": file sha256,
   "shape": [32, h, w, feature_dim], "dtype": "float16", "layer": int, "encoder": {...}}
where (h, w) is the merged grid of the student's processor for that video (video_grid_thw[1:] // 2).
"""
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn

SCHEMA = "geometry-input-v1"
INJECTION = "add_to_merged_video_tokens"
CROSS_INJECTION = "cross_attend_merged_video_tokens"
SPATIAL_INJECTION = "add_spatial_mllm_connector_to_merged_video_tokens"
FRAMES = 32
FRAMES_PER_TOKEN = 2
MERGE = 2
PROJECTOR = {"type": "layernorm_linear_gelu_linear", "hidden": 1024, "output_init": "zeros"}
CROSS_ATTENTION = {"type": "frame_strict_cross_attention", "width": 1024, "heads": 8, "output_init": "zeros",
                   "positions": "sinusoidal_2d_normalized"}
SPATIAL_MLLM = {"type": "spatial_mllm_mlp_add", "merge": "2x2_spatial_x_2_frames_concat", "norm": "rmsnorm_eps_1e-6",
                "hidden": "merged_width", "init": "hf_init_weights_normal_0.02_bias_0_norm_1",
                "store_grid": "unmerged_patch_grid"}
# Spatial-MLLM's effective connector init: Qwen2.5-VL's initializer_range (Qwen2.5-VL-3B-Instruct config.json).
SPATIAL_MLLM_INIT_STD = 0.02
GATED_SPATIAL_INJECTION = "add_gated_spatial_mllm_connector_to_merged_video_tokens"
SPATIAL_MLLM_GATED = {**SPATIAL_MLLM, "output_norm": "layernorm_no_affine_eps_1e-5", "gate": "tanh_scalar_init_0"}
SPATIAL_INJECTIONS = (SPATIAL_INJECTION, GATED_SPATIAL_INJECTION)  # the connector and store layout they share
INJECTIONS = {INJECTION: PROJECTOR, CROSS_INJECTION: CROSS_ATTENTION, SPATIAL_INJECTION: SPATIAL_MLLM,
              GATED_SPATIAL_INJECTION: SPATIAL_MLLM_GATED}  # the only accepted (injection, projector) pairs
CONFIG_KEYS = {"schema", "injection", "encoder", "layer", "feature_dim", "frames_per_token", "projector", "store"}
ENCODER_KEYS = {"name", "repository", "revision", "source_sha256", "input", "pooling"}
STORE_KEYS = {"manifest", "manifest_sha256"}
CAMERA_STORE_KEYS = {"camera_manifest", "camera_manifest_sha256"}
ROW_KEYS = {"key", "frames", "file", "sha256", "shape", "dtype", "layer", "encoder"}
CAMERA_ROW_REQUIRED_KEYS = {"key", "frames", "file", "sha256", "cam_token_shape", "layer", "encoder"}
CAMERA_ROW_ALLOWED_KEYS = CAMERA_ROW_REQUIRED_KEYS | {
    "schema", "sidecar", "bytes", "groups", "feature_dim", "cam_token_dtype",
    "pose_shape", "pose_9d_shape", "gravity_shape", "step_scale",
}
CAMERA_ROW_KEYS = CAMERA_ROW_ALLOWED_KEYS
CAMERA_TOKEN_DIM = 2048
CAMERA_GROUP_TOKEN_DIM = FRAMES_PER_TOKEN * CAMERA_TOKEN_DIM
CAMERA_POSE_DIM = 9
CAMERA_GROUPS = FRAMES // FRAMES_PER_TOKEN
HEX64 = re.compile(r"[0-9a-f]{64}")
WEIGHTS_NAME = "geometry_projector.safetensors"
MANIFEST_NAME = "geometry_input.json"


def _hex(value, what):
    if not isinstance(value, str) or not HEX64.fullmatch(value):
        raise ValueError(f"{what} must be a lowercase sha256")
    return value


def normalize(value):
    """Return the canonical geometry block or refuse it. Every key is required; nothing else is allowed."""
    if not isinstance(value, dict) or set(value) != CONFIG_KEYS:
        raise ValueError(f"Geometry block keys must be exactly {sorted(CONFIG_KEYS)}")
    if value["schema"] != SCHEMA or not isinstance(value["injection"], str) or value["injection"] not in INJECTIONS:
        raise ValueError("Unsupported geometry schema or injection")
    if value["frames_per_token"] != FRAMES_PER_TOKEN or value["projector"] != INJECTIONS[value["injection"]]:
        raise ValueError("Geometry projector or temporal pairing differs from geometry-input-v1")
    if type(value["layer"]) is not int or not 0 <= value["layer"] < 24:
        raise ValueError("Geometry layer must be an aggregator layer index 0..23")
    if type(value["feature_dim"]) is not int or value["feature_dim"] <= 0:
        raise ValueError("Geometry feature_dim must be a positive integer")
    encoder = value["encoder"]
    if not isinstance(encoder, dict) or set(encoder) != ENCODER_KEYS or not all(isinstance(encoder[k], str) and encoder[k]
                                                                               for k in ENCODER_KEYS):
        raise ValueError(f"Geometry encoder keys must be exactly {sorted(ENCODER_KEYS)} with nonempty strings")
    _hex(encoder["source_sha256"], "Geometry encoder source_sha256")
    store = value["store"]
    if (not isinstance(store, dict) or set(store) not in (STORE_KEYS, STORE_KEYS | CAMERA_STORE_KEYS)
            or not isinstance(store["manifest"], str)):
        raise ValueError(f"Geometry store keys must be exactly {sorted(STORE_KEYS)} (optionally with {sorted(CAMERA_STORE_KEYS)})")
    _hex(store["manifest_sha256"], "Geometry store manifest_sha256")
    if "camera_manifest" in store:
        if not isinstance(store["camera_manifest"], str) or not store["camera_manifest"]:
            raise ValueError("Geometry store camera_manifest must be a nonempty string")
        _hex(store["camera_manifest_sha256"], "Geometry store camera_manifest_sha256")
    return json.loads(json.dumps(value, sort_keys=True))


def frame_key(frame_sha256s):
    """Key of one ordered 32-frame selection: sha256 over the newline-joined PNG file sha256s."""
    if not isinstance(frame_sha256s, (list, tuple)) or len(frame_sha256s) != FRAMES:
        raise ValueError("A geometry key needs exactly 32 ordered frame sha256s")
    for item in frame_sha256s:
        _hex(item, "Frame sha256")
    return hashlib.sha256("\n".join(frame_sha256s).encode()).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def merged_grid(grid_thw):
    t, gh, gw = (int(x) for x in grid_thw)
    if t * FRAMES_PER_TOKEN != FRAMES or gh % MERGE or gw % MERGE:
        raise ValueError(f"Video grid {grid_thw} is not a 32-frame, 2x2-mergeable grid")
    return t, gh // MERGE, gw // MERGE


def store_grid(settings, grid_thw):
    """(h, w) of the store rows for a student video grid: the merged grid, or the unmerged patch grid for Spatial-MLLM."""
    _, h, w = merged_grid(grid_thw)
    return (MERGE * h, MERGE * w) if settings["injection"] in SPATIAL_INJECTIONS else (h, w)


def patch_tokens(array, grid_thw):
    """Per-frame patch-grid cells [32, 2h, 2w, D] -> per merged video token [t*h*w, 8*D] in Spatial-MLLM's order.

    Spatial-MLLM views its features as (t, temporal 2, D, h, 2, w, 2) and permutes to (t, h, w, 2, 2, D, temporal 2)
    before flattening, so the merged vector is ordered (row offset, column offset, channel, frame)."""
    t, h, w = merged_grid(grid_thw)
    if array.ndim != 4 or tuple(array.shape[:3]) != (FRAMES, MERGE * h, MERGE * w):
        raise ValueError(f"Geometry features {tuple(array.shape)} do not match the student patch grid (32, {2 * h}, {2 * w}, D)")
    tensor = torch.from_numpy(np.ascontiguousarray(array))
    dim = tensor.shape[-1]
    tensor = tensor.reshape(t, FRAMES_PER_TOKEN, h, MERGE, w, MERGE, dim).permute(0, 2, 4, 3, 5, 6, 1)
    return tensor.reshape(t * h * w, MERGE * MERGE * dim * FRAMES_PER_TOKEN)


def token_width(settings):
    factor = MERGE * MERGE * FRAMES_PER_TOKEN if settings["injection"] in SPATIAL_INJECTIONS else FRAMES_PER_TOKEN
    return factor * settings["feature_dim"]


def tokens(array, grid_thw):
    """Per-frame cell features [32, h, w, D] -> per merged video token [t*h*w, 2*D], in the student's token order.

    Qwen3-VL/3.5 orders a video's merged tokens by temporal patch, then merged row, then merged column; temporal patch
    k covers frames 2k and 2k+1, whose features are concatenated in frame order."""
    t, h, w = merged_grid(grid_thw)
    if array.ndim != 4 or tuple(array.shape[:3]) != (FRAMES, h, w):
        raise ValueError(f"Geometry features {tuple(array.shape)} do not match the student grid (32, {h}, {w}, D)")
    tensor = torch.from_numpy(np.ascontiguousarray(array))
    dim = tensor.shape[-1]
    return tensor.reshape(t, FRAMES_PER_TOKEN, h, w, dim).permute(0, 2, 3, 1, 4).reshape(t * h * w, FRAMES_PER_TOKEN * dim)


def camera_group_tokens(cam_token_l23):
    """Per-frame G3T camera tokens [32, 2048] -> per temporal group [16, 4096] by concatenating frames (2g, 2g+1)."""
    tensor = cam_token_l23.contiguous() if isinstance(cam_token_l23, torch.Tensor) else torch.from_numpy(np.ascontiguousarray(cam_token_l23))
    if tensor.ndim != 2 or tuple(tensor.shape) != (FRAMES, CAMERA_TOKEN_DIM):
        raise ValueError(f"G3T camera tokens {tuple(tensor.shape)} do not match ({FRAMES}, {CAMERA_TOKEN_DIM})")
    return tensor.reshape(CAMERA_GROUPS, CAMERA_GROUP_TOKEN_DIM)


def empty_camera_sidecar(groups=CAMERA_GROUPS, cam_token_dim=CAMERA_GROUP_TOKEN_DIM):
    """Zero-filled [1, ...] sidecar tensors for text-only or unlabelled rows in a batch (step_scale=-1 marks absent)."""
    return {
        "aux_g3t_cam_tokens": torch.zeros((1, groups, cam_token_dim), dtype=torch.float16),
        "aux_g3t_pose_9d": torch.zeros((1, groups, CAMERA_POSE_DIM), dtype=torch.float32),
        "aux_g3t_gravity_up": torch.zeros((1, 3), dtype=torch.float32),
        "aux_g3t_step_scale": torch.full((1, 1), -1.0, dtype=torch.float32),
    }


class FeatureStore:
    """Read-only view of one sealed feature store. Every file is verified against its manifest sha256 before first use."""

    def __init__(self, settings, resolve=None):
        self.settings = normalize(settings)
        self.resolve = resolve or (lambda path: Path(path))
        manifest = self.resolve(self.settings["store"]["manifest"])
        if file_sha256(manifest) != self.settings["store"]["manifest_sha256"]:
            raise ValueError("Geometry store manifest differs from its pinned sha256")
        self.root = Path(manifest).parent
        self.rows = {}
        with open(manifest) as handle:
            lines = list(handle)
        for line in lines:
            if not line.strip():
                continue
            row = json.loads(line)
            if set(row) != ROW_KEYS:
                raise ValueError("Malformed geometry manifest row")
            if row["key"] != frame_key(row["frames"]) or row["key"] in self.rows:
                raise ValueError("Geometry manifest key differs from its frames or repeats")
            if (row["encoder"] != self.settings["encoder"] or row["layer"] != self.settings["layer"]
                    or row["dtype"] != "float16" or len(row["shape"]) != 4 or row["shape"][0] != FRAMES
                    or row["shape"][3] != self.settings["feature_dim"]):
                raise ValueError("Geometry manifest row differs from the configured encoder, layer or shape")
            relative = Path(row["file"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Geometry feature path escapes its store")
            _hex(row["sha256"], "Geometry feature sha256")
            self.rows[row["key"]] = row
        if not self.rows:
            raise ValueError("Empty geometry store")
        self.verified = set()
        self.camera_root = None
        self.camera_rows = {}
        self.camera_verified = set()
        if "camera_manifest" in self.settings["store"]:
            cam_manifest = self.resolve(self.settings["store"]["camera_manifest"])
            if file_sha256(cam_manifest) != self.settings["store"]["camera_manifest_sha256"]:
                raise ValueError("Geometry camera manifest differs from its pinned sha256")
            self.camera_root = Path(cam_manifest).parent
            with open(cam_manifest) as handle:
                cam_lines = list(handle)
            for line in cam_lines:
                if not line.strip():
                    continue
                crow = json.loads(line)
                if not CAMERA_ROW_REQUIRED_KEYS.issubset(crow) or not set(crow).issubset(CAMERA_ROW_ALLOWED_KEYS):
                    raise ValueError("Malformed geometry camera manifest row")
                if crow["key"] != frame_key(crow["frames"]) or crow["key"] in self.camera_rows:
                    raise ValueError("Geometry camera manifest key differs from its frames or repeats")
                if crow["key"] not in self.rows or crow["frames"] != self.rows[crow["key"]]["frames"]:
                    raise ValueError("Geometry camera manifest row has no matching feature store row")
                pose_shape = crow.get("pose_shape", crow.get("pose_9d_shape"))
                if (crow["encoder"] != self.settings["encoder"] or crow["layer"] != self.settings["layer"]
                        or crow["cam_token_shape"] != [FRAMES, CAMERA_TOKEN_DIM]
                        or pose_shape != [CAMERA_GROUPS, CAMERA_POSE_DIM]):
                    raise ValueError("Geometry camera manifest row differs from the configured encoder, layer or shape")
                relative = Path(crow["file"])
                if relative.is_absolute() or ".." in relative.parts:
                    raise ValueError("Geometry camera sidecar path escapes its store")
                _hex(crow["sha256"], "Geometry camera sidecar sha256")
                self.camera_rows[crow["key"]] = crow
            if set(self.camera_rows) != set(self.rows):
                raise ValueError("Geometry camera manifest keys differ from the feature store")

    @property
    def has_camera_sidecar(self):
        return bool(self.camera_rows)

    def row(self, frame_sha256s):
        key = frame_key(list(frame_sha256s))
        if key not in self.rows:
            raise ValueError(f"No geometry features for frame selection {key}")
        if self.rows[key]["frames"] != list(frame_sha256s):
            raise ValueError("Geometry row frames differ from the requested selection")
        return self.rows[key]

    def camera_row(self, frame_sha256s):
        if not self.has_camera_sidecar:
            raise ValueError("Geometry store has no camera sidecar manifest")
        key = frame_key(list(frame_sha256s))
        if key not in self.camera_rows:
            raise ValueError(f"No geometry camera sidecar for frame selection {key}")
        if self.camera_rows[key]["frames"] != list(frame_sha256s):
            raise ValueError("Geometry camera row frames differ from the requested selection")
        return self.camera_rows[key]

    def array(self, frame_sha256s):
        row = self.row(frame_sha256s)
        path = self.root / row["file"]
        if row["key"] not in self.verified:
            if file_sha256(path) != row["sha256"]:
                raise ValueError(f"Geometry feature file changed: {row['file']}")
            self.verified.add(row["key"])
        array = np.load(path, allow_pickle=False)
        if array.dtype != np.float16 or list(array.shape) != row["shape"] or not np.isfinite(array).all():
            raise ValueError(f"Geometry feature array differs from its manifest row: {row['file']}")
        return array

    def camera_arrays(self, frame_sha256s):
        crow = self.camera_row(frame_sha256s)
        path = self.camera_root / crow["file"]
        if crow["key"] not in self.camera_verified:
            if file_sha256(path) != crow["sha256"]:
                raise ValueError(f"Geometry camera sidecar file changed: {crow['file']}")
            self.camera_verified.add(crow["key"])
        pose_shape = crow.get("pose_shape", crow.get("pose_9d_shape"))
        with np.load(path, allow_pickle=False) as data:
            files = set(data.files)
            v1_keys = {"cam_token_l23", "local_pose_enc", "global_pose_enc", "coords_1024",
                       "g3t_pose_9d", "g3t_gravity_up", "g3t_step_scale"}
            legacy_keys = {"cam_token_l23", "pose_enc_9d", "pose_9d_group16", "gravity_up", "step_scale"}
            if files not in (v1_keys, legacy_keys):
                raise ValueError(f"Geometry camera sidecar keys differ from schema: {crow['file']}")
            arrays = {k: data[k] for k in files}
        if files == v1_keys:
            step_scale = np.asarray(arrays["g3t_step_scale"])
            valid = (arrays["cam_token_l23"].dtype == np.float16
                     and list(arrays["cam_token_l23"].shape) == crow["cam_token_shape"]
                     and arrays["local_pose_enc"].dtype == np.float32
                     and list(arrays["local_pose_enc"].shape) == [FRAMES, 6]
                     and arrays["global_pose_enc"].dtype == np.float32
                     and list(arrays["global_pose_enc"].shape) == [FRAMES, 5]
                     and arrays["coords_1024"].dtype == np.float32
                     and list(arrays["coords_1024"].shape) == [FRAMES, 4]
                     and arrays["g3t_pose_9d"].dtype == np.float32
                     and list(arrays["g3t_pose_9d"].shape) == pose_shape
                     and arrays["g3t_gravity_up"].dtype == np.float32
                     and list(arrays["g3t_gravity_up"].shape) == [3]
                     and step_scale.dtype == np.float32
                     and list(step_scale.shape) in ([], [1])
                     and all(np.isfinite(v).all() for v in arrays.values())
                     and float(step_scale.reshape(-1)[0]) >= 0.0)
        else:
            step_scale = np.asarray(arrays["step_scale"])
            valid = (arrays["cam_token_l23"].dtype == np.float16
                     and list(arrays["cam_token_l23"].shape) == crow["cam_token_shape"]
                     and arrays["pose_enc_9d"].dtype == np.float32
                     and list(arrays["pose_enc_9d"].shape) == [FRAMES, CAMERA_POSE_DIM]
                     and arrays["pose_9d_group16"].dtype == np.float32
                     and list(arrays["pose_9d_group16"].shape) == pose_shape
                     and arrays["gravity_up"].dtype == np.float32
                     and list(arrays["gravity_up"].shape) == [3]
                     and step_scale.dtype == np.float32
                     and list(step_scale.shape) in ([], [1])
                     and all(np.isfinite(v).all() for v in arrays.values())
                     and float(step_scale.reshape(-1)[0]) >= 0.0)
        if not valid:
            raise ValueError(f"Geometry camera sidecar arrays differ from schema: {crow['file']}")
        return arrays

    def camera_sidecar(self, frame_sha256s, device=None):
        arrays = self.camera_arrays(frame_sha256s)
        pose_9d = arrays["g3t_pose_9d"] if "g3t_pose_9d" in arrays else arrays["pose_9d_group16"]
        grav_up = arrays["g3t_gravity_up"] if "g3t_gravity_up" in arrays else arrays["gravity_up"]
        step_val = arrays["g3t_step_scale"] if "g3t_step_scale" in arrays else arrays["step_scale"]
        out = {
            "aux_g3t_cam_tokens": camera_group_tokens(arrays["cam_token_l23"]).unsqueeze(0),
            "aux_g3t_pose_9d": torch.from_numpy(np.ascontiguousarray(pose_9d)).unsqueeze(0),
            "aux_g3t_gravity_up": torch.from_numpy(np.ascontiguousarray(grav_up)).unsqueeze(0),
            "aux_g3t_step_scale": torch.tensor([[float(np.asarray(step_val).reshape(-1)[0])]], dtype=torch.float32),
        }
        if device is not None:
            out = {k: v.to(device) for k, v in out.items()}
        return out

    def tokens(self, frame_sha256s, grid_thw):
        array = self.array(frame_sha256s)
        if self.settings["injection"] in SPATIAL_INJECTIONS:
            return patch_tokens(array, grid_thw)
        return tokens(array, grid_thw)


class GeometryProjector(nn.Module):
    def __init__(self, feature_dim, output_dim, hidden=PROJECTOR["hidden"]):
        super().__init__()
        width = FRAMES_PER_TOKEN * feature_dim
        self.norm = nn.LayerNorm(width)
        self.fc1 = nn.Linear(width, hidden)
        self.act = nn.GELU()
        self.fc2 = nn.Linear(hidden, output_dim)
        nn.init.zeros_(self.fc2.weight)
        nn.init.zeros_(self.fc2.bias)

    def forward(self, features):
        return self.fc2(self.act(self.fc1(self.norm(features))))


class RMSNorm(nn.Module):
    """Qwen2RMSNorm: the variance in float32, weight applied after the cast back (Spatial-MLLM's ln_q)."""

    def __init__(self, width, eps=1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(width))
        self.eps = eps

    def forward(self, x):
        dtype = x.dtype
        x = x.to(torch.float32)
        x = x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps)
        return self.weight * x.to(dtype)


class SpatialMLLMConnector(nn.Module):
    """Spatial-MLLM's mlp_add connector: RMSNorm, Linear(merged, merged), GELU, Linear(merged, output)."""

    def __init__(self, feature_dim, output_dim):
        super().__init__()
        width = MERGE * MERGE * FRAMES_PER_TOKEN * feature_dim
        self.ln_q = RMSNorm(width, eps=1e-6)
        self.mlp = nn.Sequential(nn.Linear(width, width), nn.GELU(), nn.Linear(width, output_dim))
        # Qwen2_5_VLPreTrainedModel._init_weights, which from_pretrained applies to the source's missing connector keys.
        for layer in (self.mlp[0], self.mlp[2]):
            nn.init.normal_(layer.weight, mean=0.0, std=SPATIAL_MLLM_INIT_STD)
            nn.init.zeros_(layer.bias)

    @property
    def fc1(self):
        return self.mlp[0]

    @property
    def fc2(self):
        return self.mlp[2]

    def forward(self, features):
        return self.mlp(self.ln_q(features))


class GatedSpatialMLLMConnector(SpatialMLLMConnector):
    """Spatial-MLLM's connector (same layers, same init), its output normalized by a LayerNorm without affine parameters
    (Swin V2 res-post-norm) and scaled by Flamingo's tanh gate: delta = tanh(gate) * LayerNorm(connector(x)).

    The gate is one learned scalar (stored as a 1-element tensor) that starts at 0, so the module first returns exact
    zeros while the gate itself receives a gradient. Every token's delta has norm |tanh(gate)| * sqrt(output width) (up
    to the LayerNorm eps), so under Adam the contribution grows by at most about lr * sqrt(width) per step, however
    the connector's own weights move."""

    LAYERNORM_EPS = 1e-5

    def __init__(self, feature_dim, output_dim):
        super().__init__(feature_dim, output_dim)  # identical RNG draws to SpatialMLLMConnector
        self.gate = nn.Parameter(torch.zeros(1))

    def forward(self, features):
        output = self.mlp(self.ln_q(features))
        return torch.tanh(self.gate) * F.layer_norm(output, (output.shape[-1],), eps=self.LAYERNORM_EPS)


class GatedCameraTokenConnector(nn.Module):
    """Per-group G3T camera token connector into the LLM carrier slots:
    RMSNorm(in_dim) -> Linear(in_dim, out_dim) -> GELU -> Linear(out_dim, out_dim) -> LayerNorm(no affine) * tanh(alpha_cam)."""

    LAYERNORM_EPS = 1e-5

    def __init__(self, in_dim=CAMERA_GROUP_TOKEN_DIM, out_dim=4096, out_init='tanh_gate', rms_cam=1.0):
        super().__init__()
        self.in_dim = in_dim
        self.out_dim = out_dim
        if out_init not in ('tanh_gate', 'zero'):
            raise ValueError('Unknown camera connector initialization')
        self.out_init = out_init
        self.ln_q = RMSNorm(in_dim, eps=1e-6)
        self.mlp = nn.Sequential(nn.Linear(in_dim, out_dim), nn.GELU(), nn.Linear(out_dim, out_dim))
        if out_init == 'tanh_gate':
            self.out_norm = nn.LayerNorm(out_dim, elementwise_affine=False, eps=self.LAYERNORM_EPS)
            self.alpha_cam = nn.Parameter(torch.zeros(1))
        else:
            self.register_buffer('rms_cam', torch.tensor([rms_cam], dtype=torch.float32))
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.ones_(self.ln_q.weight)
        for layer in (self.mlp[0], self.mlp[2]):
            nn.init.normal_(layer.weight, mean=0.0, std=SPATIAL_MLLM_INIT_STD)
            nn.init.zeros_(layer.bias)
        if self.out_init == 'tanh_gate':
            nn.init.zeros_(self.alpha_cam)
        else:
            nn.init.zeros_(self.mlp[2].weight)

    def forward(self, x):
        h = self.mlp(self.ln_q(x))
        if self.out_init == 'zero':
            return self.rms_cam * h
        return torch.tanh(self.alpha_cam) * self.out_norm(h)


class GatedCameraHeadBypass(nn.Module):
    """Direct residual bypass from G3T group camera tokens [B, 16, 4096] into CameraHead input [B, 16, 2048]:
    RMSNorm(in_dim) -> Linear(in_dim, out_dim) -> LayerNorm(no affine) * tanh(alpha_bypass)."""

    LAYERNORM_EPS = 1e-5

    def __init__(self, in_dim=CAMERA_GROUP_TOKEN_DIM, out_dim=2048):
        super().__init__()
        self.in_dim = in_dim
        self.out_dim = out_dim
        self.ln_q = RMSNorm(in_dim, eps=1e-6)
        self.fc = nn.Linear(in_dim, out_dim)
        self.out_norm = nn.LayerNorm(out_dim, elementwise_affine=False, eps=self.LAYERNORM_EPS)
        self.alpha_bypass = nn.Parameter(torch.zeros(1))
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.ones_(self.ln_q.weight)
        nn.init.normal_(self.fc.weight, mean=0.0, std=SPATIAL_MLLM_INIT_STD)
        nn.init.zeros_(self.fc.bias)
        nn.init.zeros_(self.alpha_bypass)

    def forward(self, x):
        h = self.fc(self.ln_q(x))
        return torch.tanh(self.alpha_bypass) * self.out_norm(h)


def position_code(height, width, channels, heads=1):
    """Fixed 2D sinusoidal code [height * width, channels] of the normalized merged-cell centres ((r + 0.5) / height,
    (c + 0.5) / width), row-major like the merged tokens. Per axis it holds the sine and the cosine of geometric
    frequencies from 1 to 64 cycles per unit length. The channels are interleaved per head: each of the `heads`
    contiguous channel groups holds a [row sin | row cos | col sin | col cos] slice, so every head sees both axes.
    Computed in float64 on the CPU and cast once to float32, so every device receives identical values."""
    if channels % (4 * heads):
        raise ValueError("The 2D position code needs channels divisible by 4 * heads")
    bands = channels // 4
    frequencies = 2 * math.pi * torch.logspace(0, math.log10(64), bands, dtype=torch.float64)

    def encode(count):
        angles = ((torch.arange(count, dtype=torch.float64) + 0.5) / count)[:, None] * frequencies[None]
        return torch.cat([angles.sin(), angles.cos()], dim=-1)

    rows = encode(height)[:, None, :].expand(height, width, 2 * bands)
    cols = encode(width)[None, :, :].expand(height, width, 2 * bands)
    code = torch.cat([rows, cols], dim=-1).reshape(height * width, 4, heads, bands // heads)
    return code.transpose(1, 2).reshape(height * width, 4 * bands).to(torch.float32)


class GeometryCrossAttention(nn.Module):
    """Frame-strict cross-attention from merged video tokens to the geometry cells of their own temporal patch.

    For each video (merged grid t, h, w) and temporal patch k, the h*w visual tokens of k are the queries and the 2*h*w
    cells of frames 2k and 2k+1 (features[..., :D] and features[..., D:]) the keys and values; nothing attends across
    patches or videos. Queries and keys carry the fixed position code of their cell, interleaved so that every head
    sees both axes; keys also carry a learned slot embedding of their frame. The output layer starts at zero, so the
    module first returns zeros."""

    def __init__(self, feature_dim, output_dim, width=CROSS_ATTENTION["width"], heads=CROSS_ATTENTION["heads"]):
        super().__init__()
        if width % (4 * heads):
            raise ValueError("Cross-attention width must divide into its heads and the 2D position code")
        self.feature_dim, self.width, self.heads = feature_dim, width, heads
        self.ln_q = nn.LayerNorm(output_dim)
        self.ln_k = nn.LayerNorm(feature_dim)
        self.q = nn.Linear(output_dim, width)
        self.k = nn.Linear(feature_dim, width)
        self.v = nn.Linear(feature_dim, width)
        self.o = nn.Linear(width, output_dim)
        nn.init.zeros_(self.o.weight)
        nn.init.zeros_(self.o.bias)
        self.slot = nn.Parameter(torch.empty(FRAMES_PER_TOKEN, width))
        nn.init.normal_(self.slot, std=0.02)
        self._codes = {}  # (h, w, device, dtype) -> position code; a cache outside the state dict

    def code(self, height, width, device, dtype):
        """The per-head position code of a merged grid on a device and dtype, built once from the float64 code."""
        key = (height, width, torch.device(device), dtype)
        if key not in self._codes:
            with torch.inference_mode(False), torch.no_grad():
                self._codes[key] = position_code(height, width, self.width, self.heads).to(device=device, dtype=dtype)
        return self._codes[key]

    @property
    def fc2(self):
        """The zero-initialised output layer under the projector's name, for callers that check the zero start."""
        return self.o

    def forward(self, visual, features, grid_thw):
        if visual.ndim != 2 or features.ndim != 2 or features.shape[1] != FRAMES_PER_TOKEN * self.feature_dim:
            raise ValueError("Cross-attention needs [video tokens, width] queries and [video tokens, 2 * feature_dim] cells")
        head = self.width // self.heads
        outputs, start = [], 0
        for grid in grid_thw.tolist():
            t, h, w = merged_grid(grid)
            cells, count = h * w, t * h * w
            tokens, cell_features = visual[start:start + count], features[start:start + count]
            start += count
            if tokens.shape[0] != count or cell_features.shape[0] != count:
                raise ValueError("Cross-attention grid covers more tokens than the batch holds")
            query = self.q(self.ln_q(tokens)).reshape(t, cells, self.width)
            query = query + self.code(h, w, query.device, query.dtype)
            frames = self.ln_k(cell_features.reshape(t, cells, FRAMES_PER_TOKEN, self.feature_dim).transpose(1, 2))
            key = self.k(frames)
            key = key + self.code(h, w, key.device, key.dtype) + self.slot.to(key.dtype)[:, None, :]
            value = self.v(frames)
            key = key.reshape(t, FRAMES_PER_TOKEN * cells, self.heads, head).transpose(1, 2)
            value = value.reshape(t, FRAMES_PER_TOKEN * cells, self.heads, head).transpose(1, 2)
            query = query.reshape(t, cells, self.heads, head).transpose(1, 2)
            attended = F.scaled_dot_product_attention(query, key, value)
            outputs.append(self.o(attended.transpose(1, 2).reshape(count, self.width)))
        if start != visual.shape[0]:
            raise ValueError("Cross-attention grid and merged token count disagree")
        return torch.cat(outputs)


def vision_module(model):
    found = [module for module in model.modules()
             if type(module).__name__.endswith("VisionModel") and hasattr(module, "merger")]
    if len(found) != 1:
        raise ValueError(f"Expected exactly one vision tower with a merger, found {len(found)}")
    return found[0]


class GeometryInput(nn.Module):
    """Holds the projector (or the cross-attention) and adds its output to the vision tower's merged tokens through a
    forward hook.

    The caller provides the token-aligned features for exactly one vision forward (provide), the hook consumes them,
    and a vision forward without provided features, or with a different token count, raises. Cross-attention also
    needs the forward's grid_thw."""

    def __init__(self, settings, output_dim):
        super().__init__()
        self.settings = normalize(settings)
        self.cross = self.settings["injection"] == CROSS_INJECTION
        self.projector = (GeometryCrossAttention(self.settings["feature_dim"], output_dim) if self.cross
                          else SpatialMLLMConnector(self.settings["feature_dim"], output_dim)
                          if self.settings["injection"] == SPATIAL_INJECTION
                          else GatedSpatialMLLMConnector(self.settings["feature_dim"], output_dim)
                          if self.settings["injection"] == GATED_SPATIAL_INJECTION
                          else GeometryProjector(self.settings["feature_dim"], output_dim))
        self._pending = None
        self.calls = 0
        self._handle = None

    def provide(self, features):
        if self._pending is not None:
            raise ValueError("Geometry features were provided twice without a vision forward")
        if features.ndim != 2 or features.shape[1] != token_width(self.settings):
            raise ValueError("Geometry features must be [video tokens, token width of the injection]")
        self._pending = features

    def clear(self):
        self._pending = None

    def hook(self, module, args, kwargs, output):
        features, self._pending = self._pending, None
        if features is None:
            raise ValueError("Video tokens reached the language model without geometry features")
        pooled = output.pooler_output if hasattr(output, "pooler_output") else output[1]
        grid = kwargs.get("grid_thw", args[1] if len(args) > 1 else None)
        if grid is not None and int((grid.prod(-1) // MERGE**2).sum()) != pooled.shape[0]:
            raise ValueError("Vision grid and merged token count disagree")
        if features.shape[0] != pooled.shape[0]:
            raise ValueError(f"Geometry features cover {features.shape[0]} tokens, the vision tower produced {pooled.shape[0]}")
        if self.cross:
            if grid is None:
                raise ValueError("Cross-attention geometry input needs the vision forward's grid_thw")
            dtype = self.projector.q.weight.dtype
            delta = self.projector(pooled.to(dtype), features.to(device=pooled.device, dtype=dtype), grid)
        else:
            weight = self.projector.fc1.weight
            delta = self.projector(features.to(device=pooled.device, dtype=weight.dtype))
        merged = pooled + delta.to(pooled.dtype)
        self.calls += 1
        if hasattr(output, "pooler_output"):
            output.pooler_output = merged
            return output
        return (output[0], merged, *output[2:])

    def manifest(self):
        return {"schema": SCHEMA, "settings": self.settings,
                "parameters": sum(p.numel() for p in self.projector.parameters()),
                "tensors": {name: list(t.shape) for name, t in self.projector.state_dict().items()}}


def attach(model, settings, name="geometry_input"):
    """Register a GeometryInput under `model.<name>` (so FSDP and the optimizer see its parameters) and hook the tower."""
    vision = vision_module(model)
    output_dim = int(getattr(vision.config, "out_hidden_size"))
    if hasattr(model, name):
        raise ValueError(f"Model already has an attribute {name}")
    module = GeometryInput(settings, output_dim)
    setattr(model, name, module)
    module._handle = vision.register_forward_hook(module.hook, with_kwargs=True)
    return module


def save(module, directory):
    """Write the projector weights and their manifest (publication and checkpoints). Returns the manifest dict."""
    from safetensors.torch import save_file

    directory = Path(directory)
    weights = directory / WEIGHTS_NAME
    state = {name: tensor.detach().to("cpu", torch.float32).contiguous() for name, tensor in module.projector.state_dict().items()}
    save_file(state, str(weights))
    manifest = {**module.manifest(), "weights": {"path": WEIGHTS_NAME, "sha256": file_sha256(weights)}}
    (directory / MANIFEST_NAME).write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return manifest


def load(model, directory, settings, device=None):
    """Evaluator side: attach a frozen GeometryInput and load the published projector with exact names and sha256."""
    from safetensors.torch import load_file

    directory = Path(directory)
    manifest = json.loads((directory / MANIFEST_NAME).read_text())
    if manifest.get("schema") != SCHEMA or normalize(manifest.get("settings")) != normalize(settings):
        raise ValueError("Published geometry settings differ from the evaluated configuration")
    weights = directory / manifest["weights"]["path"]
    if manifest["weights"]["path"] != WEIGHTS_NAME or file_sha256(weights) != manifest["weights"]["sha256"]:
        raise ValueError("Published geometry projector differs from its manifest")
    module = attach(model, settings)
    state = load_file(str(weights), device="cpu")
    expected = module.projector.state_dict()
    if set(state) != set(expected) or any(tuple(state[k].shape) != tuple(v.shape) or state[k].dtype != torch.float32
                                          for k, v in expected.items()):
        raise ValueError("Published geometry projector tensors differ from geometry-input-v1")
    module.projector.load_state_dict(state, strict=True)
    if device is not None:
        module.to(device)
    module.requires_grad_(False)
    module.eval()
    return module
