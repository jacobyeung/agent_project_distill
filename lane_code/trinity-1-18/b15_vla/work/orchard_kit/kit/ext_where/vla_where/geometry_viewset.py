"""ViewSetG3T (schema 6.5): the pinned G3T tower run on any number S >= 1 of views in one call.

Views, in order (schema 6.2): [wrist_t, agent_t, wrist history newest first]; view 0 fixes the gauge and one call gives
one scale for all views. It constructs `student_pilot.tower_read.FrozenG3TTower(settings)` and calls `_load()` for the
pins (REVISION, WEIGHTS_SHA256, CONFIG_SHA256, SOURCE_SHA256), then runs `tower.module` itself:
  - preprocessing as FrozenG3TTower.run: PNG round trip, load_and_preprocess_images_square(..., 1024), bilinear 518;
  - _tower_native.selected_layers(model.aggregator, inputs[None]);
  - the local and global camera heads on blocks[23][:, :, :1];
  - camera composition as _tower_native.convert lines 76-86 (w2c = lift(g2c) @ lift(w2g), FP32), without its
    N in {32, 64, 96} check;
  - model.depth_head on all S views;
  - _tower_native.native_sample(..., endpoints=False) at native pixel centres ('native'), or the tower's 51 x 51
    endpoint grid ('grid51', used by the T-11 parity test).
It never calls FrozenG3TTower.run, which requires 32/64/96 dense frames and 32 strictly increasing anchors.

Per view it returns T_view0<-view (4 x 4, G3T units), FoV (vertical, horizontal; radians), K at the native raster,
depth [H, W], confidence [H, W] and the gravity up vector (camera frame; convert's encode_gravity uses world up
(0, -1, 0) in the gravity frame).
"""
import hashlib
import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import torch
from torch.nn import functional as F

from . import geometry as G

DEFAULT_TREE = Path('/scratch/jjyeung/orch_cd/integ_v3/work/tree')
SIZE = 518


@dataclass
class ViewSetResult:
    views: list                 # [(role, step)], view 0 = ('wrist', t)
    T0: np.ndarray              # [S, 4, 4] T_view0<-view, G3T units (T0[0] = identity)
    fov: np.ndarray             # [S, 2] (vertical, horizontal) radians
    K: np.ndarray               # [S, 3, 3] intrinsics at each view's native raster
    depth: list                 # S x [H, W] optical-axis depth, G3T units (or metres when metric_flag is set)
    conf: list                  # S x [H, W] confidence, or None (all pixels confident: GT backends)
    metric_flag: Optional[str] = None  # None = G3T units (scale from proprio_handeye); else the flag of a metric source
    up: Optional[np.ndarray] = None    # [S, 3] gravity up in each camera frame (the gravity frame's up is (0, -1, 0))
    mirror: bool = False               # frames are the true camera frames reflected by diag(-1, 1, 1) (schema 0)
    extra: dict = field(default_factory=dict)

    def index(self, role, step):
        return self.views.index((role, step))

    def centre(self, i):
        """C_G3T of view i in view 0's gauge."""
        return self.T0[i][:3, 3]


class CameraCheckError(ValueError):
    """A view failed _tower_native.convert's per-view camera checks (schema 6.5 step 4); the chunk gets no_lift."""


def check_cameras(local, global_, coords):
    """convert's validity checks per view, without its N in {32, 64, 96} check."""
    bad = []
    for k in range(len(local)):
        l, g, c = local[k], global_[k], coords[k]
        if not (np.isfinite(l).all() and np.isfinite(g).all() and np.isfinite(c).all()
                and np.linalg.norm(l[:4]) >= 1e-6 and np.linalg.norm(g[3:]) >= 1e-6
                and (l[4:] > 0).all() and (l[4:] < np.pi).all()
                and (c[:2] >= 0).all() and (c[2:] <= 1024).all() and (c[2:] > c[:2]).all()):
            bad.append(k)
    if bad:
        raise CameraCheckError(f'G3T camera checks failed for views {bad}')


def _import_vendor(tree):
    from student_pilot.c1r_ref import source_import
    source_import(Path(tree) / 'student_pilot' / 'g3t_vendor')


def _lift4(extri):
    bottom = torch.tensor([0., 0., 0., 1.], dtype=extri.dtype, device=extri.device)
    return torch.cat((extri, bottom.expand(*extri.shape[:-2], 1, 4)), dim=-2)


def preprocess(frames, device='cpu'):
    """uint8 HWC frames -> ([S, 3, 518, 518], [S, 4] boxes on the 1024 canvas), as FrozenG3TTower.run does."""
    from PIL import Image
    from vggt.utils.load_fn import load_and_preprocess_images_square
    inputs, coords = [], []
    for frame in frames:
        value = np.asarray(frame)
        if value.dtype != np.uint8 or value.ndim != 3 or value.shape[2] != 3:
            raise ValueError('G3T frames must be native uint8 HWC RGB')
        stream = io.BytesIO()
        Image.fromarray(value).save(stream, format='PNG')
        stream.seek(0)
        square, box = load_and_preprocess_images_square([stream], 1024)
        inputs.append(F.interpolate(square.to(device), size=(SIZE, SIZE), mode='bilinear', align_corners=False)[0])
        coords.append(box[0, :4].numpy())
    return torch.stack(inputs), np.stack(coords)


def native_K(intr_518, box_1024, native_hw):
    """Intrinsics on the 518 square (convert's frame) -> intrinsics at the native raster (continuous pixels)."""
    box = np.asarray(box_1024, dtype=np.float64) * (SIZE / 1024.)
    h, w = native_hw
    sx, sy = w / (box[2] - box[0]), h / (box[3] - box[1])
    K = np.asarray(intr_518, dtype=np.float64)
    return np.array([[K[0, 0] * sx, 0, (K[0, 2] - box[0]) * sx], [0, K[1, 1] * sy, (K[1, 2] - box[1]) * sy], [0, 0, 1]])


class ViewSetG3T:
    def __init__(self, module, *, device='cpu', dtype='bf16', tree=DEFAULT_TREE, pins=None, mirror_x=False):
        """mirror_x: the images are the camera view mirrored left-right (LIBERO dataset orientation, schema 0). G3T
        then reconstructs the mirrored scene; outputs stay in G3T frames and carry `mirror=True`, and the provider maps
        metric points with M = diag(-1, 1, 1) (X_wrist = s M X_g)."""
        _import_vendor(tree)
        self.module = module.to(device).eval().requires_grad_(False)
        self.device, self.dtype, self.tree = torch.device(device), dtype, Path(tree)
        self.pins, self.mirror_x = pins, bool(mirror_x)
        self._sha = None

    @classmethod
    def load_pinned(cls, weights_path, config_path, *, device='cuda', dtype='bf16', tree=DEFAULT_TREE, mirror_x=False):
        from student_pilot import tower_read as T
        tower = T.FrozenG3TTower(dict(weights_path=str(weights_path), config_path=str(config_path), device=device,
                                      dense_frames=32, depth_chunk_size=8, dtype=dtype))
        tower._load()
        pins = dict(revision=T.REVISION, weights=T.WEIGHTS_SHA256, config=T.CONFIG_SHA256, source=T.SOURCE_SHA256)
        return cls(tower.module, device=device, dtype=dtype, tree=tree, pins=pins, mirror_x=mirror_x)

    def sha(self):
        if self._sha is None:
            if self.pins is not None:
                ident = '|'.join(f'{k}={self.pins[k]}' for k in sorted(self.pins))
            else:
                digest = hashlib.sha256()
                for key, value in sorted(self.module.state_dict().items()):
                    digest.update(key.encode() + b'\0' + value.detach().float().cpu().numpy().tobytes())
                ident = 'unpinned=' + digest.hexdigest()
            self._sha = hashlib.sha256(f'viewset_g3t|{ident}|{self.dtype}|mirror_x={self.mirror_x}'.encode()).hexdigest()
        return self._sha

    def pin(self):
        """Schema 9 G3T pins (weights, config, source); unpinned modules (tests) give their state-dict sha."""
        if self.pins is not None:
            return dict(config=self.pins['config'], source=self.pins['source'], weights=self.pins['weights'])
        return self.sha()

    @torch.inference_mode()
    def run(self, images, views=None, raster='native'):
        from student_pilot._tower_native import native_sample, selected_layers
        from vggt.utils.pose_enc import pose_encoding_to_extri_intri
        if not images:
            raise ValueError('ViewSetG3T needs at least one view')
        inputs, coords = preprocess(images, self.device)
        model = self.module
        autocast = self.device.type == 'cuda' and self.dtype == 'bf16'
        with torch.autocast(self.device.type, dtype=torch.bfloat16, enabled=autocast):
            blocks, start = selected_layers(model.aggregator, inputs[None])
        with torch.autocast(self.device.type, enabled=False):
            camera = [blocks[23][:, :, :1].float()]
            local = model.local_camera_head(camera)[-1][0].float().cpu()
            global_ = model.global_camera_head(camera)[-1][0].float().cpu()
            check_cameras(local.numpy(), global_.numpy(), coords)
            g2c, intr = pose_encoding_to_extri_intri(local[None].float(), (SIZE, SIZE),
                                                     pose_encoding_type='noT_quaR_FoV')
            w2g, _ = pose_encoding_to_extri_intri(global_[None].float(), (SIZE, SIZE),
                                                  pose_encoding_type='absT_quaRy_noFoV', build_intrinsics=False)
            w2c = (_lift4(g2c) @ _lift4(w2g))[0].double().numpy()
            intr = intr[0].double().numpy()
        with torch.autocast(self.device.type, dtype=torch.bfloat16, enabled=autocast):
            depth, conf = model.depth_head(blocks, images=inputs[None], patch_start_idx=start, frames_chunk_size=8)
        S = len(images)
        T0 = np.stack([w2c[0] @ np.linalg.inv(w2c[k]) for k in range(S)])
        K, fov, depths, confs = [], [], [], []
        for k in range(S):
            hw = tuple(np.asarray(images[k]).shape[:2])
            box = coords[k:k + 1]
            shape, endpoints = (hw, False) if raster == 'native' else ((51, 51), True)
            depths.append(native_sample(depth[0, k:k + 1], box, hw, shape, endpoints=endpoints)[0, ..., 0]
                          .cpu().numpy().astype(np.float64))
            confs.append(native_sample(conf[0, k:k + 1, ..., None], box, hw, shape, endpoints=endpoints)[0, ..., 0]
                         .cpu().numpy().astype(np.float64))
            K.append(native_K(intr[k], coords[k], hw))
            fov.append([2 * np.arctan(hw[0] / (2 * K[-1][1, 1])), 2 * np.arctan(hw[1] / (2 * K[-1][0, 0]))])
        up = np.stack([w2c[k][:3, :3] @ np.array([0.0, -1.0, 0.0]) for k in range(S)])
        return ViewSetResult(list(views) if views is not None else [(None, k) for k in range(S)], T0,
                             np.array(fov), np.stack(K), depths, confs, up=up, mirror=self.mirror_x,
                             extra=dict(local=local.numpy(), global_=global_.numpy(), coords=coords, w2c=w2c))


def pose9(result):
    """The tower's C1 pose9 rows (t, xyzw quaternion, FoV v, FoV h) of T_view<-view0, for parity with
    FrozenG3TTower.run (camera_targets.encode_cameras)."""
    from student_pilot.camera_targets import quaternion_xyzw
    rows = []
    for k in range(len(result.T0)):
        rel = G.inv(result.T0[k])
        rows.append(np.concatenate([rel[:3, 3], quaternion_xyzw(rel[:3, :3]), result.fov[k]]))
    return np.array(rows)


def tiny_module(seed=13, tree=DEFAULT_TREE, point_head=False):
    """The tree's tiny real-architecture G3T (tests/test_tower_read.py): 24-block aggregator of width 8 at 28 px."""
    _import_vendor(tree)
    from vggt.heads.camera_head import CameraHead
    from vggt.heads.dpt_head import DPTHead
    from vggt.models.aggregator import Aggregator
    torch.manual_seed(seed)
    model = torch.nn.Module()
    model.aggregator = Aggregator(img_size=28, embed_dim=8, depth=24, num_heads=2, mlp_ratio=1, patch_embed='conv')
    for name, encoding, bias in (('local_camera_head', 'noT_quaR_FoV', [0, 0, 0, 1, .3, .3]),
                                 ('global_camera_head', 'absT_quaRy_noFoV', [0, 0, 0, 0, 1])):
        head = CameraHead(dim_in=16, trunk_depth=1, num_heads=2, pose_encoding_type=encoding)
        with torch.no_grad():
            head.pose_branch.fc2.weight.mul_(.001)
            head.pose_branch.fc2.bias.copy_(torch.tensor(bias, dtype=torch.float32))
        setattr(model, name, head)
    model.depth_head = DPTHead(dim_in=16, features=8, out_channels=[8] * 4, output_dim=2, activation='exp')
    if point_head:
        model.point_head = DPTHead(dim_in=16, features=8, out_channels=[8] * 4, output_dim=4, activation='inv_log')
    return model


def tiny_patches():
    """Context managers that run the 518-px tower code at 28 px on CPU (the tree's tiny tower test does the same)."""
    from unittest import mock
    from vggt.utils.load_fn import load_and_preprocess_images_square as square
    original = F.interpolate

    def small_preprocess(images, size):
        value, coords = square(images, 28)
        coords[:, :4] *= 1024 / 28
        return value, coords

    def resize(*args, **kwargs):
        if kwargs.get('size') == (SIZE, SIZE):
            kwargs['size'] = (28, 28)
        return original(*args, **kwargs)

    return (mock.patch('vggt.utils.load_fn.load_and_preprocess_images_square', side_effect=small_preprocess),
            mock.patch.object(F, 'interpolate', side_effect=resize))
