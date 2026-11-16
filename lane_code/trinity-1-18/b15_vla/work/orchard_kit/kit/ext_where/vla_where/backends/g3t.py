"""Geometry from the frozen G3T tower (the integ_v3 tree's vendored VGGT model) on one instant plus the chunk window.

Frames, in order: the agent view (the reference camera), the wrist frames of obs.history (oldest first), the current
wrist frame. One aggregator pass gives every frame's camera and depth in G3T's own unit, so the agent/wrist pose, the
wrist depth and the wrist trajectory share one unit and the provider's scale s converts all three to metres.

The preprocessing and operations are the tree's (student_pilot.tower_read.FrozenG3TTower.run): square padding to
1024 (vggt.utils.load_fn.load_and_preprocess_images_square), bilinear resize to the tower input, the pinned aggregator
layer selection (_tower_native.selected_layers), camera token of block 23 into the local and global camera heads, the
DPT depth head, and native_sample back to source pixels. Only the frame count differs: the tree reads 32/64/96-frame
clips, U1 reads 2 + history frames of the same chunk. Camera composition follows _tower_native.convert:
world-to-camera = lift(gravity-to-camera, local head) @ lift(world-to-gravity, global head), OpenCV axes.
"""
import hashlib
import io
from pathlib import Path

import numpy as np
import torch
from torch.nn import functional as F

from .. import geometry as G
from .base import GeometryResult

DEFAULT_TREE = Path('/scratch/jjyeung/orch_cd/integ_v3/work/tree')


def _import_vendor(tree):
    from student_pilot.c1r_ref import source_import
    source_import(Path(tree) / 'student_pilot' / 'g3t_vendor')


def _lift4(extri):
    bottom = torch.tensor([0., 0., 0., 1.], dtype=extri.dtype, device=extri.device)
    return torch.cat((extri, bottom.expand(*extri.shape[:-2], 1, 4)), dim=-2)


def preprocess(frames, size=518):
    """uint8 HWC frames -> ([S, 3, size, size] tensor, [S, 4] native-canvas boxes on the 1024 square)."""
    from PIL import Image
    from vggt.utils.load_fn import load_and_preprocess_images_square
    inputs, coords = [], []
    for frame in frames:
        value = np.asarray(frame)
        if value.dtype != np.uint8 or value.ndim != 3 or value.shape[2] != 3:
            raise ValueError('G3T frames must be uint8 HWC RGB')
        stream = io.BytesIO()
        Image.fromarray(value).save(stream, format='PNG')
        stream.seek(0)
        square, box = load_and_preprocess_images_square([stream], 1024)
        inputs.append(F.interpolate(square, size=(size, size), mode='bilinear', align_corners=False)[0])
        coords.append(box[0, :4].numpy())
    return torch.stack(inputs), np.stack(coords).astype(np.float64)


def native_K(intr_square, box_1024, native_hw, size):
    """Model intrinsics on the size x size square -> intrinsics on the native raster (continuous pixels)."""
    box = np.asarray(box_1024, dtype=np.float64) * (size / 1024.)
    h, w = native_hw
    sx, sy = w / (box[2] - box[0]), h / (box[3] - box[1])
    K = np.asarray(intr_square, dtype=np.float64).copy()
    return np.array([[K[0, 0] * sx, 0, (K[0, 2] - box[0]) * sx], [0, K[1, 1] * sy, (K[1, 2] - box[1]) * sy], [0, 0, 1]])


class G3TGeometry:
    """module: the G3T model (aggregator, local_camera_head, global_camera_head, depth_head); load_pinned() builds it
    from the tree's pinned config and weights exactly as FrozenG3TTower._load does."""

    def __init__(self, module, *, size=518, device='cpu', dtype='bf16', tree=DEFAULT_TREE, weights_sha=None):
        _import_vendor(tree)
        self.module = module.to(device).eval().requires_grad_(False)
        self.size, self.device, self.dtype, self.tree = size, torch.device(device), dtype, Path(tree)
        self._sha = weights_sha

    @classmethod
    def load_pinned(cls, weights_path, config_path, *, device='cuda', dtype='bf16', tree=DEFAULT_TREE):
        from student_pilot.tower_read import FrozenG3TTower, WEIGHTS_SHA256
        tower = FrozenG3TTower(dict(weights_path=str(weights_path), config_path=str(config_path), device=device,
                                    dtype=dtype))
        tower._load()
        return cls(tower.module, device=device, dtype=dtype, tree=tree, weights_sha=WEIGHTS_SHA256)

    def sha(self):
        if self._sha is None:
            digest = hashlib.sha256()
            for key, value in sorted(self.module.state_dict().items()):
                digest.update(key.encode() + b'\0' + value.detach().float().cpu().numpy().tobytes())
            self._sha = digest.hexdigest()
        return hashlib.sha256(f'g3t|{self._sha}|{self.size}|{self.dtype}'.encode()).hexdigest()

    @torch.inference_mode()
    def run(self, obs):
        from student_pilot._tower_native import selected_layers, native_sample
        from vggt.utils.pose_enc import pose_encoding_to_extri_intri
        frames = [obs.agent] + [h['wrist'] for h in obs.history] + [obs.wrist]
        inputs, coords = preprocess(frames, self.size)
        inputs = inputs.to(self.device)
        model = self.module
        autocast = self.device.type == 'cuda' and self.dtype == 'bf16'
        with torch.autocast(self.device.type, dtype=torch.bfloat16, enabled=autocast):
            blocks, start = selected_layers(model.aggregator, inputs[None])
        with torch.autocast(self.device.type, enabled=False):
            camera = [blocks[23][:, :, :1].float()]
            local = model.local_camera_head(camera)[-1].float()
            global_ = model.global_camera_head(camera)[-1].float()
            g2c, intr = pose_encoding_to_extri_intri(local, (self.size, self.size), pose_encoding_type='noT_quaR_FoV')
            w2g, _ = pose_encoding_to_extri_intri(global_, (self.size, self.size),
                                                  pose_encoding_type='absT_quaRy_noFoV', build_intrinsics=False)
            w2c = (_lift4(g2c) @ _lift4(w2g))[0].double().cpu().numpy()
        with torch.autocast(self.device.type, dtype=torch.bfloat16, enabled=autocast):
            depth, conf = model.depth_head(blocks, images=inputs[None], patch_start_idx=start,
                                           frames_chunk_size=len(frames))
        T_agent = [w2c[0] @ G.inv(w2c[k]) for k in range(len(frames))]
        out_depth, out_conf, K = {}, {}, {}
        for view, k in (('agent', 0), ('wrist', len(frames) - 1)):
            hw = frames[k].shape[:2]
            box = coords[k:k + 1]
            out_depth[view] = native_sample(depth[0, k:k + 1], box, hw, hw, endpoints=False)[0, ..., 0].cpu().numpy().astype(np.float64)
            out_conf[view] = native_sample(conf[0, k:k + 1, ..., None], box, hw, hw, endpoints=False)[0, ..., 0].cpu().numpy().astype(np.float64)
            K[view] = native_K(intr[0, k].double().cpu().numpy(), coords[k], hw, self.size)
        centres = np.array([T[:3, 3] for T in T_agent[1:]])
        return GeometryResult(depth=out_depth, T_agent_cam={'agent': np.eye(4), 'wrist': T_agent[-1]},
                              history_centres=centres, K=K, conf=out_conf, metric=False)


def tiny_module(seed=13, tree=DEFAULT_TREE):
    """The tree's tiny real-architecture G3T (tests/test_tower_read.py): 24-block aggregator of width 8 at 28 px."""
    _import_vendor(tree)
    from vggt.models.aggregator import Aggregator
    from vggt.heads.camera_head import CameraHead
    from vggt.heads.dpt_head import DPTHead
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
    return model
