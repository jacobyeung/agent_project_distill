"""Frozen native G3T inference and the fixed tower-to-read-layer bridge.

The plain Python owner deliberately keeps every tower module outside the
student's module tree. Attach after loading the student, before generate().
"""
from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import torch
from torch.nn import functional as F

from .tower_scale import estimate_scale
from .tower_errors import TowerError, tower_guard

REVISION = 'c55e91a04f1cbbad67359072536351201fd19e8b'
WEIGHTS_SHA256 = 'd460957bb1c8a8c228d83ab10bad8a6dbcf80b03f29d7fbebf9c0f2c1c25f702'
CONFIG_SHA256 = '5aeb2acd008d41a1cac52e10216fbf35e8dfeb2ce26b89bb24e7ccc4ee0817d7'
SOURCE_SHA256 = 'df1ea59a73b0ad08b51670bfa37da84eace99b9d0c45c8d270f7052b42e98701'
NATIVE_INPUT = 'native_square_pad_bicubic_1024_bilinear_518_v1'
GRID_UV = np.linspace(0, 1000, 51, dtype=np.float32)


def validate_pose_source(value):
    if value not in ('own', 'tower'):
        raise TowerError("pose_source must be 'own' or 'tower'")


def _numpy(value):
    return value.detach().cpu().numpy() if isinstance(value, torch.Tensor) else np.asarray(value)


def _anchors(indices, slots, n):
    indices, slots = _numpy(indices), _numpy(slots)
    if (indices.shape != (n,) or indices.dtype.kind not in 'iu'
            or np.any(np.diff(indices) <= 0) or indices[0] < 0):
        raise TowerError('Tower native frame indices must strictly increase')
    if (slots.shape != (32,) or slots.dtype.kind not in 'iu' or slots[0] != 0
            or np.any(np.diff(slots) <= 0) or slots[-1] >= n):
        raise TowerError('Tower requires 32 increasing LM anchor slots starting at 0')
    return indices.copy(), slots.copy()


def _lm_indices(batch, expected):
    keys = [key for key in ('frame_indices', 'tower_lm_frame_indices') if key in batch]
    if not keys:
        raise TowerError('Tower requires LM native frame_indices or tower_lm_frame_indices')
    for key in keys:
        indices = _numpy(batch[key])
        if indices.shape == (1, 32):
            indices = indices[0]
        if (indices.shape != (32,) or indices.dtype.kind not in 'iu'
                or not np.array_equal(indices, expected)):
            raise TowerError('Own and tower frame indices differ: ' + key)


@dataclass(frozen=True)
class TowerState:
    raw_pose9: np.ndarray
    depth_grid: np.ndarray
    depth_conf_grid: np.ndarray
    frame_indices: np.ndarray
    anchor_slots: np.ndarray
    depth_slots: np.ndarray = None
    points_grid: np.ndarray = None
    grid_uv: np.ndarray = None

    @tower_guard
    def __post_init__(self):
        raw = np.asarray(self.raw_pose9, dtype=np.float64)
        if (raw.ndim != 2 or raw.shape[1] != 9 or len(raw) not in (32, 64, 94, 96)
                or not np.isfinite(raw).all()
                or not np.allclose(np.linalg.norm(raw[:, 3:7], axis=1), 1, atol=1e-3)
                or np.any(raw[:, 7:] <= 0) or np.any(raw[:, 7:] >= np.pi)
                or not np.allclose(raw[0, :6], 0, atol=2e-5)
                or not np.isclose(abs(raw[0, 6]), 1, atol=2e-5)):
            raise TowerError('Tower pose9 must be finite, unit-quaternion, frame-1-relative [N,9]')
        indices, slots = _anchors(self.frame_indices, self.anchor_slots, len(raw))
        arrays = dict(raw_pose9=raw, frame_indices=indices, anchor_slots=slots,
                      depth_grid=np.asarray(self.depth_grid), depth_conf_grid=np.asarray(self.depth_conf_grid),
                      grid_uv=GRID_UV if self.grid_uv is None else np.asarray(self.grid_uv))
        depth_slots = slots if self.depth_slots is None else np.asarray(self.depth_slots)
        if not (np.array_equal(depth_slots, slots) or np.array_equal(depth_slots, np.arange(len(raw)))):
            raise TowerError("Invalid depth slots")
        arrays["depth_slots"] = depth_slots
        if any(arrays[k].shape != (len(depth_slots), 51, 51) for k in ('depth_grid', 'depth_conf_grid')):
            raise TowerError('Tower depth and confidence require the 32 native 51x51 anchor grids')
        if not np.array_equal(arrays['grid_uv'], GRID_UV):
            raise TowerError('Tower grid coordinates differ')
        if self.points_grid is not None:
            points = np.asarray(self.points_grid)
            if points.shape != (len(depth_slots), 51, 51, 3):
                raise TowerError('Tower points require [32,51,51,3] in frame 1')
            arrays['points_grid'] = points
        for key, value in arrays.items():
            value = value.copy()
            value.flags.writeable = False
            object.__setattr__(self, key, value)

    @classmethod
    @tower_guard
    def from_npz(cls, path):
        with np.load(path, allow_pickle=False) as data:
            state = cls(data['raw_pose'], data['depth_grid'], data['depth_conf_grid'],
                        data['frame_indices'], data['anchor_slots'],
                        data['depth_slots'] if 'depth_slots' in data else None,
                        data['points_grid'] if 'points_grid' in data else None, data['grid_uv'])
            if 'raw_pose32' in data and not np.allclose(
                    state.raw_pose9[state.anchor_slots], data['raw_pose32'], atol=1e-6, rtol=0):
                raise TowerError('Cached dense poses differ from LM anchors')
            return state

    def validate_batch(self, batch):
        for key, value in (('tower_frame_indices', self.frame_indices),
                           ('tower_anchor_slots', self.anchor_slots)):
            if key not in batch:
                raise TowerError('Tower requires explicit ' + key)
            if not np.array_equal(_numpy(batch[key]), value):
                raise TowerError('Cached tower selection differs: ' + key)
        _lm_indices(batch, self.frame_indices[self.anchor_slots])

    @tower_guard
    def scaled_pose9(self, own_depth_grid):
        scale, _, _ = estimate_scale(self.depth_grid, self.depth_conf_grid, own_depth_grid)
        if not np.isfinite(scale) or scale <= 0:
            raise TowerError('Invalid tower metric scale')
        raw = self.raw_pose9[self.anchor_slots].copy()
        raw[:, :3] *= scale
        return raw, scale


@tower_guard
def g3t_to_c1_pose9(local_pose, global_pose, coords_1024):
    """Use rkit's FP32 camera composition and float64 C1 reference encoding."""
    from ._tower_native import convert
    return convert(local_pose, global_pose, coords_1024)


def _hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


class FrozenG3TTower:
    def __init__(self, settings, *, module=None):
        allowed = {'weights_path', 'config_path', 'device', 'dense_frames', 'depth_chunk_size', 'dtype'}
        if set(settings) - allowed:
            raise TowerError('Unknown tower settings')
        self.settings = dict(settings)
        self.device = torch.device(settings.get('device', 'cpu'))
        self.dense_frames = settings.get('dense_frames', 64)
        self.chunk = settings.get('depth_chunk_size', 8)
        self.dtype = settings.get('dtype', 'bf16')
        if (type(self.dense_frames) is not int or self.dense_frames not in (32, 64, 94, 96)
                or type(self.chunk) is not int or not 1 <= self.chunk <= 32
                or self.dtype not in ('bf16', 'fp32')):
            raise TowerError('Invalid tower frame count, chunk size or dtype')
        if module is None and not {'weights_path', 'config_path'} <= set(settings):
            raise TowerError('Tower requires local pinned weights and config')
        self.module = module
        if module is not None:
            self.module.to(self.device).eval().requires_grad_(False)

    @torch.inference_mode()
    @tower_guard
    def _load(self):
        if self.module is not None:
            return
        from .c1r_ref import source_import
        from .g3t_online import VENDOR, vendor_digest
        if vendor_digest() != SOURCE_SHA256:
            raise TowerError('Tower G3T source pin differs')
        for key, expected in (('config_path', CONFIG_SHA256), ('weights_path', WEIGHTS_SHA256)):
            if _hash(self.settings[key]) != expected:
                raise TowerError('Tower asset pin differs: ' + key)
        config = json.loads(Path(self.settings['config_path']).read_text())
        expected = dict(embed_dim=1024, img_size=518, patch_size=14,
                        enable_depth=True, enable_point=True, enable_gravity_camera_heads=True)
        if config != expected:
            raise TowerError('Tower config differs from the governed architecture')
        cls = source_import(VENDOR)
        model = cls(**config).float().eval().requires_grad_(False)
        from safetensors import safe_open
        live = model.state_dict()
        with safe_open(str(self.settings['weights_path']), framework='pt', device='cpu') as data:
            if set(data.keys()) != set(live):
                raise TowerError('Tower checkpoint keys differ')
            for key, target in live.items():
                value = data.get_tensor(key)
                if value.shape != target.shape or not value.is_floating_point():
                    raise TowerError('Tower checkpoint tensor differs: ' + key)
                target.copy_(value)
        model.to(self.device)
        self.module = model

    @torch.inference_mode()
    @tower_guard
    def run(self, batch, *, all_depth=False):
        from PIL import Image
        frames = batch.get('tower_native_frames')
        if frames is None or len(frames) != self.dense_frames:
            raise TowerError('Tower requires dense native RGB frames; never use student patches')
        if type(self.dense_frames) is not int or self.dense_frames not in (32, 64, 94, 96):
            raise TowerError('Invalid tower dense frame count')
        if 'tower_anchor_slots' not in batch:
            raise TowerError('Tower requires explicit tower_anchor_slots')
        slots = batch['tower_anchor_slots']
        if 'tower_frame_indices' not in batch:
            raise TowerError('Tower requires explicit native frame indices')
        indices, slots = _anchors(batch['tower_frame_indices'], slots, len(frames))
        # Validate metadata before preprocessing or loading large weights.
        _lm_indices(batch, indices[slots])
        self._load()
        from .c1r_ref import source_import
        source_import(Path(__file__).parent / 'g3t_vendor')
        from vggt.utils.load_fn import load_and_preprocess_images_square
        from ._tower_native import selected_layers, native_sample
        inputs, coords, native_hw = [], [], None
        for frame in frames:
            if isinstance(frame, Image.Image):
                image = frame
            else:
                value = np.asarray(frame)
                if value.dtype != np.uint8 or value.ndim != 3 or value.shape[2] != 3:
                    raise TowerError('Tower frames must be native uint8 HWC RGB')
                image = Image.fromarray(value)
            if image.mode != 'RGB':
                raise TowerError('Tower frames must be native RGB')
            hw = (image.height, image.width)
            if native_hw is not None and hw != native_hw:
                raise TowerError('Tower requires a common native raster size')
            native_hw = hw
            stream = io.BytesIO()
            image.save(stream, format='PNG')
            stream.seek(0)
            square, box = load_and_preprocess_images_square([stream], 1024)
            inputs.append(F.interpolate(square.to(self.device), size=(518, 518), mode='bilinear',
                                        align_corners=False)[0])
            coords.append(box[0, :4].numpy())
        inputs, coords = torch.stack(inputs), np.stack(coords)
        model = self.module.eval()
        owner = getattr(self, '_gf1_owner', None)
        if owner is not None:
            from .gf1 import share_head_tower
            share_head_tower(owner, self)
        autocast = self.device.type == 'cuda' and self.dtype == 'bf16'
        if owner is not None:
            encoder = owner.auxiliary_heads.geometry_encoder
            autocast = self.device.type == 'cuda' or encoder.settings.get('encoder_dtype') == 'bf16'
        with torch.autocast(self.device.type, dtype=torch.bfloat16, enabled=autocast):
            if owner is None:
                blocks, start = selected_layers(model.aggregator, inputs[None])
            else:
                layers = sorted(set((4, 11, 17, 23)) | set(owner.geometry_online['gf1']['layers']))
                blocks, start = selected_layers(model.aggregator, inputs[None], layers=layers)
        with torch.autocast(self.device.type, enabled=False):
            camera = [blocks[23][:, :, :1].float()]
            if owner is None:
                local = model.local_camera_head(camera)[-1][0].float().cpu().numpy()
                global_ = model.global_camera_head(camera)[-1][0].float().cpu().numpy()
            else:
                local = encoder._camera(model.local_camera_head, camera).float().cpu().numpy()
                global_ = encoder._camera(model.global_camera_head, camera).float().cpu().numpy()
        result = g3t_to_c1_pose9(local, global_, coords)
        depths, confidences, points = [], [], []
        depth_slots = np.arange(len(frames)) if all_depth else slots
        for offset in range(0, len(depth_slots), self.chunk):
            selected = depth_slots[offset:offset + self.chunk]
            small = [b[:, selected].contiguous() if b is not None else None for b in blocks]
            images, box = inputs[selected][None], coords[selected]
            with torch.autocast(self.device.type, dtype=torch.bfloat16, enabled=autocast):
                depth, conf = model.depth_head(small, images=images, patch_start_idx=start,
                                               frames_chunk_size=self.chunk)
            depths.append(native_sample(depth[0], box, native_hw, (51, 51))[..., 0].cpu().numpy())
            confidences.append(native_sample(conf[0, ..., None], box, native_hw, (51, 51))[..., 0].cpu().numpy())
            del depth, conf
            if getattr(model, 'point_head', None) is not None:
                with torch.autocast(self.device.type, dtype=torch.bfloat16, enabled=autocast):
                    value, conf = model.point_head(small, images=images, patch_start_idx=start,
                                                  frames_chunk_size=self.chunk)
                points.append(native_sample(value[0], box, native_hw, (51, 51)).cpu().numpy())
                del value, conf
        points = np.concatenate(points) if points else None
        if points is not None:
            transform = result['world_to_frame0']
            points = (points @ transform[:3, :3].T + transform[:3, 3]).astype(np.float32)
        state = TowerState(result['raw_pose'], np.concatenate(depths), np.concatenate(confidences),
                           indices, slots, depth_slots, points)
        state.validate_batch(batch)
        if owner is not None:
            from .gf1 import bind_head_features
            bind_head_features(owner, batch, blocks, start, inputs, coords, slots, local, global_)
        return state


def attach_tower(model, settings, *, module=None):
    tower = FrozenG3TTower(settings, module=module)
    model.tower_read = tower
    return tower


@tower_guard
def prepare_tower(model, batch):
    tower = getattr(model, 'tower_read', None)
    if not isinstance(tower, FrozenG3TTower):
        raise TowerError('Attach the frozen tower before tower decoding')
    tower._gf1_owner = model if 'gf1' in (getattr(model, 'geometry_online', None) or {}) else None
    return tower.run(batch)


@tower_guard
def apply_tower(heads, state, batch):
    """Scale from V-C on its endpoint grid; preserve the printed-query sequence."""
    if not isinstance(state, TowerState):
        raise TowerError('tower pose source requires a TowerState')
    state.validate_batch(batch)
    if heads.depth_map is None:
        raise TowerError('Tower scale requires the private V-C depth head')
    axis = torch.as_tensor(GRID_UV.copy(), device=heads.depth_map.device)
    yy, xx = torch.meshgrid(axis, axis, indexing='ij')
    uv = torch.stack((xx, yy), -1).reshape(1, -1, 2).expand(32, -1, -1)
    with torch.no_grad():
        own = heads.depth_head.query(heads.depth_map, uv).double().cpu().numpy().reshape(32, 51, 51)
    heads.pose9, heads.tower_scale = state.scaled_pose9(own)
    heads.tower_state = state
