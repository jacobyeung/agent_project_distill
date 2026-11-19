"""Registered online G3T geometry for the student's CAM carriers.

Disagreement is |atan2(f_x, f_z)| for the third row of the local g2c
rotation. It measures optical-axis yaw in the camera's gravity frame. The
canonical local head encodes roll/pitch only (X^G = R_x R_z X^C), so yaw
claimed by this head belongs to the global head and provides a GT-free signal.
"""
from contextlib import contextmanager, nullcontext
import copy
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.checkpoint import checkpoint
from torch.overrides import TorchFunctionMode

from .c1r_ref import source_import, REPOSITORY, REVISION

VENDOR = Path(__file__).parent / 'g3t_vendor'
INPUT = 'vision_patch_unpatchify_first_of_group_square_pad_bilinear_518_v1'
NATIVE_INPUT = 'native_square_pad_bicubic_1024_bilinear_518_v1'
FEATURE = 'cam_l23_2048_pose9_disagreement1_v1'


class _ScalarSchedule(TorchFunctionMode):
    """Keep the vendored constructor's scalar drop-path schedule readable on meta."""
    def __torch_function__(self, func, types, args=(), kwargs=None):
        kwargs = {} if kwargs is None else kwargs
        if func is torch.linspace:
            kwargs = {**kwargs, 'device': 'cpu'}
        return func(*args, **kwargs)


def vendor_digest():
    """Hash sorted Python paths relative to g3t_vendor, including the vggt prefix."""
    root = VENDOR
    lines = [f'{p.relative_to(root).as_posix()}\0{hashlib.sha256(p.read_bytes()).hexdigest()}\n'
             for p in sorted(root.rglob('*.py'))]
    return hashlib.sha256(''.join(lines).encode()).hexdigest()


def _keys(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys.split()):
        raise ValueError('Unknown or missing GX configuration key')


def _positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def reference_binding_pin(value):
    """Validate the parent's independently verified control binding identity."""
    _keys(value, 'sha256 config_sha256 trainer_commit')
    if (any(not isinstance(value[k], str) or re.fullmatch(r'[0-9a-f]{64}', value[k]) is None
            for k in ('sha256', 'config_sha256'))
            or not isinstance(value['trainer_commit'], str) or not value['trainer_commit'].strip()):
        raise ValueError('Invalid GX reference_binding pin')
    return value


def normalize(block):
    _keys(block, 'schema mode encoder input feature connector finetune' +
          (' encoder_dtype' if isinstance(block, dict) and 'encoder_dtype' in block else '') +
          (' fail_fast' if isinstance(block, dict) and 'fail_fast' in block else '') +
          (' patch_fusion' if isinstance(block, dict) and 'patch_fusion' in block else '') +
          (' gf1' if isinstance(block, dict) and 'gf1' in block else ''))
    cfg = copy.deepcopy(block)
    if 'encoder_dtype' in cfg and (cfg['mode'] != 'frozen' or cfg['encoder_dtype'] != 'bf16'):
        raise ValueError('GX encoder_dtype accepts only bf16 in frozen mode')
    if 'gf1' in cfg:
        from .gf1 import normalize as normalize_gf1
        cfg['gf1'] = normalize_gf1(cfg['gf1'])
        if cfg['mode'] != 'frozen' or cfg['input'] != INPUT or 'patch_fusion' in cfg:
            raise ValueError('GF1 requires frozen student camera input without legacy patch fusion')
    if 'patch_fusion' in cfg:
        fusion = cfg['patch_fusion']
        _keys(fusion, 'pool projector hidden align_steps' +
              (' checkpointing' if isinstance(fusion, dict) and 'checkpointing' in fusion else ''))
        if 'checkpointing' in fusion and (cfg['mode'] != 'frozen' or type(fusion['checkpointing']) is not bool):
            raise ValueError('GX patch_fusion checkpointing requires a boolean in frozen mode')
        if (fusion['pool'] != 'roi_area_merged_grid_v1'
                or fusion['projector'] != 'layernorm_linear_gelu_linear_zero_out_v1'
                or type(fusion['hidden']) is not int or fusion['hidden'] != 1024
                or type(fusion['align_steps']) is not int or fusion['align_steps'] < 0):
            raise ValueError('Invalid GX patch_fusion settings')
    if (cfg['schema'] != 'gx-carrier-v1' or cfg['mode'] not in ('frozen', 'finetune')
            or cfg['input'] not in (INPUT, NATIVE_INPUT) or cfg['feature'] != FEATURE):
        raise ValueError('Unsupported GX contract')
    enc = cfg['encoder']
    _keys(enc, 'repository revision source_sha256 weights config')
    if (enc['repository'] != REPOSITORY or enc['revision'] != REVISION
            or enc['source_sha256'] != vendor_digest()):
        raise ValueError('GX source pin differs')
    for name in ('weights', 'config'):
        _keys(enc[name], 'path sha256')
        if (not isinstance(enc[name]['path'], str) or not enc[name]['path']
                or not isinstance(enc[name]['sha256'], str)
                or not re.fullmatch('[0-9a-f]{64}', enc[name]['sha256'])):
            raise ValueError('Invalid GX asset pin')
    conn = cfg['connector']
    _keys(conn, 'out_init rms_cam rms_scale')
    if (conn['out_init'] != 'zero' or conn['rms_cam'] != 'warm_start_carrier_median_rms_v1'
            or not _positive(conn['rms_scale'])):
        raise ValueError('Invalid GX connector')
    conn['rms_scale'] = float(conn['rms_scale'])
    ft = cfg['finetune']
    if (ft is not None) != (cfg['mode'] == 'finetune'):
        raise ValueError('GX finetune settings must match mode')
    if ft is not None:
        _keys(ft, 'lr_scale hold_steps warmup_steps scope checkpointing clip_norm')
        if (not _positive(ft['lr_scale']) or not _positive(ft['clip_norm'])
                or type(ft['hold_steps']) is not int or ft['hold_steps'] < 0
                or type(ft['warmup_steps']) is not int or ft['warmup_steps'] < 1
                or ft['scope'] not in ('aggregator', 'aggregator_blocks')
                or type(ft['checkpointing']) is not bool):
            raise ValueError('Invalid GX finetune settings')
        for key in ('lr_scale', 'clip_norm'):
            ft[key] = float(ft[key])
    fail = cfg.get('fail_fast')
    if fail is not None:
        _keys(fail, 'step min_delta_ratio max_loss_ratio' +
              (' reference reference_binding' if isinstance(fail, dict) and 'reference' in fail else ''))
        if (type(fail['step']) is not int or fail['step'] < 1
                or any(type(fail[k]) not in (int, float) or not math.isfinite(fail[k])
                       for k in ('min_delta_ratio', 'max_loss_ratio'))):
            raise ValueError('Invalid GX fail-fast settings')
        if 'reference' in fail and (not isinstance(fail['reference'], str)
                                    or not Path(fail['reference']).is_absolute()):
            raise ValueError('GX fail-fast reference must be an absolute output path')
        if 'reference' in fail:
            reference_binding_pin(fail['reference_binding'])
        for key in ('min_delta_ratio', 'max_loss_ratio'):
            fail[key] = float(fail[key])
    return cfg


def validate_arm(settings, training_mode, frame_layout, depth_enabled):
    """Admit frozen final GX; patch fusion explicitly selects its alignment stage."""
    if 'gf1' in settings:
        if training_mode != 'final' or frame_layout != 'duplicate':
            raise ValueError('GF1 requires final mode and duplicate LM frame layout')
        return
    if training_mode == 'final':
        if (settings['mode'] != 'frozen' or settings['input'] != INPUT or frame_layout != 'duplicate'):
            raise ValueError('Final GX requires frozen mode, duplicate and student unpatchify input')
        if 'patch_fusion' in settings and settings['patch_fusion']['align_steps'] != 50:
            raise ValueError('Final GX patch_fusion requires 50 alignment steps')
    elif training_mode != 'pose_only' or frame_layout not in ('duplicate', 'paired') or depth_enabled:
        raise ValueError('GX requires pose_only, duplicate/paired and no depth')


class G3TEncoder(nn.Module):
    """Frozen FP32/BF16 storage or FP32 trainable masters; deterministic eval operations."""
    def __init__(self, settings, architecture=None, image_size=518, verify_full=True):
        super().__init__()
        self.settings = normalize(settings)
        if architecture is None:
            from .rehearsal import tower_architecture
            architecture = tower_architecture(self.settings)
        cls = source_import(VENDOR)
        self.image_size, self.verify_full, self.verified = image_size, verify_full and 'gf1' not in settings, False
        with _ScalarSchedule() if torch.empty(0).device.type == 'meta' else nullcontext():
            if architecture is None:
                model = cls(enable_point=False, enable_depth=False)
                self.aggregator = model.aggregator
                self.local_camera_head = model.local_camera_head
                self.global_camera_head = model.global_camera_head
            else:
                from vggt.models.aggregator import Aggregator
                from vggt.heads.camera_head import CameraHead
                self.aggregator = Aggregator(**architecture['aggregator'])
                self.local_camera_head = CameraHead(**architecture['head'], pose_encoding_type='noT_quaR_FoV')
                self.global_camera_head = CameraHead(**architecture['head'], pose_encoding_type='absT_quaRy_noFoV')
        self.float().requires_grad_(False)
        if self.settings.get('encoder_dtype') == 'bf16':
            # Cast only parameters: normalization/rotary buffers keep their native precision.
            # Pinned FP32 tensors copy directly into this storage, one tensor at a time.
            for parameter in self.parameters():
                parameter.data = parameter.data.to(torch.bfloat16)
        if settings['mode'] == 'finetune':
            scope = settings['finetune']['scope']
            for name, param in self.aggregator.named_parameters():
                param.requires_grad_(name != 'patch_embed.mask_token' and
                    (scope == 'aggregator' or name.startswith(('frame_blocks.', 'global_blocks.'))
                     or name in ('camera_token', 'register_token')))
        self.train(False)

    def train(self, mode=True):
        return super().train(False)

    def load_pinned(self, weights_path, verify=True):
        from safetensors import safe_open
        from .p3_provenance import sha256
        sha = sha256(weights_path) if verify else self.settings['encoder']['weights']['sha256']
        if verify and sha != self.settings['encoder']['weights']['sha256']:
            raise ValueError('GX weights pin differs')
        prefixes = ('aggregator.', 'local_camera_head.', 'global_camera_head.')
        live = self.state_dict()
        loaded = {}
        with safe_open(str(weights_path), framework='pt', device='cpu') as f, torch.no_grad():
            keys = set(f.keys())
            if any(not k.startswith(prefixes + ('depth_head.', 'point_head.')) for k in keys):
                raise ValueError('Unexpected G3T checkpoint prefix')
            selected = {k for k in keys if k.startswith(prefixes)}
            if selected != set(live):
                raise ValueError('G3T checkpoint keys differ')
            for key in sorted(selected):
                if tuple(f.get_slice(key).get_shape()) != tuple(live[key].shape):
                    raise ValueError('G3T checkpoint shape differs: ' + key)
                value = f.get_tensor(key)
                if value.dtype != torch.float32:
                    raise ValueError('G3T checkpoint must be FP32')
                # One tensor at a time: eight ranks never hold a second full copy in host memory.
                live[key].copy_(value)
                loaded[key] = value.numel()
                del value
        if set(loaded) != set(self.state_dict()):
            raise ValueError('G3T checkpoint did not cover the module')
        return dict(sha256=sha, tensors=len(loaded), parameters=sum(loaded.values()),
                    **({'encoder_dtype': self.settings['encoder_dtype']} if 'encoder_dtype' in self.settings else {}),
                    groups={p[:-1]: dict(tensors=sum(k.startswith(p) for k in loaded),
                        parameters=sum(v for k, v in loaded.items() if k.startswith(p))) for p in prefixes})

    def _call(self, block, *args):
        ft = self.settings['finetune']
        if ft and ft['checkpointing'] and torch.is_grad_enabled():
            return checkpoint(block, *args, use_reentrant=False)
        return block(*args)

    def _patches(self, images):
        patch = self.aggregator.patch_embed
        if hasattr(patch, 'prepare_tokens_with_masks'):
            tokens = patch.prepare_tokens_with_masks(images, None)
            for block in patch.blocks:
                tokens = self._call(block, tokens)
            return patch.norm(tokens)[:, patch.num_register_tokens + 1:]
        return self._call(patch, images)

    def _lean(self, images):
        from vggt.models.aggregator import slice_expand_and_flatten
        a = self.aggregator
        if a.aa_block_size != 1 or list(a.aa_order) != ['frame', 'global'] or a.patch_start_idx != 5:
            raise ValueError('Unsupported GX aggregator layout')
        s, _, h, w = images.shape
        normalized = ((images[None] - a._resnet_mean) / a._resnet_std).view(s, 3, h, w)
        tokens = torch.cat([slice_expand_and_flatten(a.camera_token, 1, s),
                            slice_expand_and_flatten(a.register_token, 1, s), self._patches(normalized)], 1)
        _, p, c = tokens.shape
        pos = None
        if a.rope is not None:
            pos = a.position_getter(s, h // a.patch_size, w // a.patch_size, device=images.device) + 1
            pos = torch.cat([torch.zeros(s, 5, 2, device=images.device, dtype=pos.dtype), pos], 1)
        bank = []
        gf1 = self.settings.get('gf1')
        if gf1 and max(gf1['layers']) >= len(a.frame_blocks):
            raise ValueError('GF1 layer exceeds the tower depth')
        for layer_index, (frame, global_) in enumerate(zip(a.frame_blocks, a.global_blocks)):
            tokens = self._call(frame, tokens.reshape(s, p, c), pos)
            cam_frame = tokens[:, 0]
            if 'patch_fusion' in self.settings or (gf1 and layer_index in gf1['layers']):
                patch_frame = tokens[:, 5:]
            tokens = self._call(global_, tokens.reshape(1, s * p, c),
                                None if pos is None else pos.reshape(1, s * p, 2))
            if gf1 and layer_index in gf1['layers']:
                bank.append(torch.cat([patch_frame, tokens.reshape(s, p, c)[:, 5:]], -1))
        cam = torch.cat([cam_frame, tokens.reshape(s, p, c)[:, 0]], -1).float()
        if gf1:
            return cam, torch.stack(bank)
        if 'patch_fusion' in self.settings:
            return cam, torch.cat([patch_frame, tokens.reshape(s, p, c)[:, 5:]], -1).float()
        return cam

    def _camera(self, head, tokens):
        if self.settings.get('encoder_dtype') != 'bf16':
            return head(tokens)[-1][0]
        # Preserve FP32 head arithmetic, expanding one quantized head per call.
        # functional_call restores the BF16 storage and keeps no FP32 master copy.
        state = {name: value.float() for name, value in head.named_parameters()}
        state.update({name: value.float() if value.is_floating_point() else value
                      for name, value in head.named_buffers()})
        return torch.func.functional_call(head, state, (tokens,), strict=True)[-1][0]

    def _autocast(self, device):
        return torch.autocast(device, dtype=torch.bfloat16,
                              enabled=device == 'cuda' or self.settings.get('encoder_dtype') == 'bf16')

    def _forward(self, images):
        device = images.device.type
        with self._autocast(device):
            cam = self._lean(images)
            if 'patch_fusion' in self.settings or 'gf1' in self.settings:
                cam, patches = cam
        with torch.autocast(device, enabled=False):
            tokens = [cam[None, :, None].float()]
            local = self._camera(self.local_camera_head, tokens)
            global_ = self._camera(self.global_camera_head, tokens)
        result = (cam, local.float(), global_.float())
        return (*result, patches) if ('patch_fusion' in self.settings or 'gf1' in self.settings) else result

    def forward(self, images, coords=None):
        if images.ndim != 4 or tuple(images.shape[1:]) != (3, self.image_size, self.image_size):
            raise ValueError('Invalid GX image shape')
        if self.verify_full and not self.verified and not os.environ.get('GX_SKIP_PARITY'):
            # Once per process, before any graph exists: the lean path must equal the native modules bitwise.
            with torch.no_grad():
                lean = self._forward(images)
                device = images.device.type
                with self._autocast(device):
                    tokens, _ = self.aggregator(images[None])
                with torch.autocast(device, enabled=False):
                    last = [tokens[-1].float()]
                    native = (last[0][0, :, 0], self._camera(self.local_camera_head, last).float(),
                              self._camera(self.global_camera_head, last).float())
                    if 'gf1' in self.settings:
                        native += (torch.stack([tokens[i][0, :, 5:] for i in self.settings['gf1']['layers']]),)
                    if 'patch_fusion' in self.settings:
                        native += (last[0][0, :, 5:],)
                del tokens, last
                # Bitwise equality is expected (same kernels, same order); a GPU kernel difference beyond
                # rounding would mean the lean path is wrong, so only a material gap stops the run.
                diffs = [float((a - b).abs().max()) for a, b in zip(lean, native)]
                scales = [float(b.abs().max()) for b in native]
                self.parity = dict(bitwise=all(torch.equal(a, b) for a, b in zip(lean, native)), max_abs_diff=diffs)
                if not self.parity['bitwise']:
                    print(json.dumps({'warning': 'lean G3T path not bitwise equal to native', **self.parity}), flush=True)
                if any(not math.isfinite(d) or d > 1e-3 * max(1., v) for d, v in zip(diffs, scales)):
                    raise ValueError('Lean G3T path differs from native forward')
                del lean, native
            self.verified = True
        with torch.no_grad() if self.settings['mode'] == 'frozen' else nullcontext():
            return self._forward(images)


def student_frames(pixel_values_videos, video_grid_thw, vision_config, image_mean, image_std):
    """Invert Qwen's merged patch order and recover the first frame of each of 32 groups."""
    p, tp, m = (getattr(vision_config, key) for key in
                ('patch_size', 'temporal_patch_size', 'spatial_merge_size'))
    mean = torch.as_tensor(image_mean, device=pixel_values_videos.device).float().view(1, 3, 1, 1)
    std = torch.as_tensor(image_std, device=pixel_values_videos.device).float().view(1, 3, 1, 1)
    videos, offset = [], 0
    for grid in video_grid_thw:
        gt, gh, gw = map(int, grid)
        if gt != 32 or gh <= 0 or gw <= 0 or gh % m or gw % m:
            raise ValueError('GX requires 32 valid temporal groups')
        n = gt * gh * gw
        patches = pixel_values_videos[offset:offset+n].float()
        frames = patches.reshape(gt, gh//m, gw//m, m, m, 3, tp, p, p)
        frames = frames.permute(0, 6, 5, 1, 3, 7, 2, 4, 8).reshape(gt, tp, 3, gh*p, gw*p)[:, 0]
        videos.append((frames * std + mean).clamp(0, 1))
        offset += n
    if offset != len(pixel_values_videos):
        raise ValueError('GX video patch count differs from grid')
    return videos


def native_square_518(frames, expected_frames=32):
    """Use the vendored square loader on augmented RGB, retaining only 518-pixel tensors."""
    from PIL import Image
    source_import(VENDOR)
    from vggt.utils.load_fn import load_and_preprocess_images_square
    if len(frames) != expected_frames:
        raise ValueError(f'Native GX requires {expected_frames} viewpoint frames')
    images, coords = [], []
    for frame in frames:
        with io.BytesIO() as buffer:
            Image.fromarray(frame).save(buffer, format='PNG')
            buffer.seek(0)
            square, box = load_and_preprocess_images_square([buffer], 1024)
        images.append(F.interpolate(square, (518, 518), mode='bilinear', align_corners=False).half())
        coords.append(box[:, :4])
    return torch.cat(images), torch.cat(coords).float()


def square_518(frames, size=518):
    """Centre-pad in source pixels, then resize once; coordinates use a 1024-square raster."""
    h, w = frames.shape[-2:]
    side = max(h, w)
    left, top = (side-w)//2, (side-h)//2
    square = F.pad(frames.float(), (left, side-w-left, top, side-h-top))
    coords = frames.new_tensor([left, top, left+w, top+h], dtype=torch.float32) * (1024 / side)
    return F.interpolate(square, (size, size), mode='bilinear', align_corners=False, antialias=False), \
        coords[None].expand(len(frames), -1)


def pose9(local, global_, coords):
    """Return mean-radius-normalized and raw first-camera-relative xyzw/FoV poses."""
    source_import(VENDOR)
    from vggt.utils.pose_enc import pose_encoding_to_extri_intri
    from vggt.utils.rotation import mat_to_quat
    g2c, _ = pose_encoding_to_extri_intri(local[None], (518, 518), 'noT_quaR_FoV', False)
    w2g, _ = pose_encoding_to_extri_intri(global_[None], (518, 518), 'absT_quaRy_noFoV', False)
    def lift(extri):
        bottom = extri.new_tensor([0., 0., 0., 1.]).expand(*extri.shape[:-2], 1, 4)
        return torch.cat([extri, bottom], -2)
    world = (lift(g2c) @ lift(w2g))[0].double()
    relative = world @ torch.linalg.inv(world[0])
    q = F.normalize(mat_to_quat(relative[:, :3, :3]), dim=-1)
    q = torch.where(q[:, 3:] < 0, -q, q)
    box = coords.double() / 1024
    hw = torch.stack([box[:, 3]-box[:, 1], box[:, 2]-box[:, 0]], -1)
    fov = 2 * torch.atan(hw * torch.tan(local[:, 4:].double()/2))
    raw = torch.cat([relative[:, :3, 3], q, fov], -1)
    scale = raw[1:, :3].norm(dim=-1).mean().clamp_min(1e-6)
    normalized = torch.cat([raw[:, :3]/scale, raw[:, 3:]], -1)
    return normalized.to(local.dtype), raw


def disagreement(local):
    source_import(VENDOR)
    from vggt.utils.rotation import quat_to_mat
    forward = quat_to_mat(local[:, :4])[:, 2]
    return torch.atan2(forward[:, 0], forward[:, 2]).abs()[:, None]


def features(encoder, images, coords):
    encoded = encoder(images, coords)
    cam, local, global_ = encoded[:3]
    if not all(torch.isfinite(value).all() for value in encoded):
        raise ValueError('Nonfinite G3T feature')
    with torch.no_grad():
        pose, _ = pose9(local.detach(), global_.detach(), coords)
        d = disagreement(local.detach())
    result = torch.cat([cam, pose.float(), d.float()], -1)
    if not torch.isfinite(result).all():
        raise ValueError('Nonfinite G3T feature')
    return (result, encoded[3]) if ('patch_fusion' in encoder.settings or 'gf1' in encoder.settings) else result


def pool_patches_online(patches, coords_1024, video_grid_thw, slot_map, *, dtype=None):
    """c1r_ref.pool_patches with a selectable output dtype (kept here so c1r_ref, which the dense-cache
    loader binds by file hash, stays byte-identical). Area-pool a square teacher grid over its valid ROI,
    then merge spatially and temporally.

    The processor grid is UNMERGED [T,2h,2w]. Each source token is constant on
    its 1/37-square cell. Output [T,h,w,D] flattens directly in LM video-token order.
    Pool one distinct frame at a time to bound FP32 working memory. The default
    cache output is FP16; online fusion requests FP32 without breaking autograd.
    """
    import torch
    patches = torch.as_tensor(patches)
    coords = torch.as_tensor(coords_1024, device=patches.device, dtype=torch.float32)
    grid = np.asarray(video_grid_thw)
    mapping = np.asarray(slot_map)
    if (grid.shape != (3,) or grid.dtype.kind not in 'iu' or (grid <= 0).any()
            or grid[1] % 2 or grid[2] % 2 or mapping.shape != (int(grid[0]) * 2,)
            or mapping.dtype.kind not in 'iu' or (mapping < 0).any() or (mapping >= len(patches)).any()
            or patches.ndim != 3 or patches.shape[1] != 37 * 37 or not patches.is_floating_point()
            or coords.shape != (len(patches), 4) or not torch.isfinite(coords).all()
            or (coords[:, :2] < 0).any() or (coords[:, 2:] > 1024).any()
            or (coords[:, 2:] <= coords[:, :2]).any()):
        raise ValueError('Invalid patch grid, slot map or valid ROI')
    temporal, rows, cols = map(int, grid)
    height, width, dim = rows // 2, cols // 2, patches.shape[-1]
    edges = torch.arange(38, device=patches.device, dtype=torch.float32) * (1024 / 37)
    def weights(start, end, cells):
        bounds = torch.linspace(0, 1, cells + 1, device=patches.device) * (end-start) + start
        overlap = (torch.minimum(bounds[1:, None], edges[None, 1:]) -
                   torch.maximum(bounds[:-1, None], edges[None, :-1])).clamp_min(0)
        return overlap / (bounds[1:] - bounds[:-1])[:, None]
    # Accumulate by temporal patch, so duplicate slots never duplicate teacher inference.
    pooled = torch.zeros((temporal, height, width, dim), device=patches.device, dtype=torch.float32)
    for frame, ((x1, y1, x2, y2), block) in enumerate(zip(coords, patches.unbind(0))):
        block = block.float().reshape(37, 37, dim)
        if not torch.isfinite(block).all():
            raise ValueError('Nonfinite teacher patches')
        x, y = weights(x1, x2, cols), weights(y1, y2, rows)
        unmerged = torch.einsum('ai,ijd,bj->abd', y, block, x)
        merged = unmerged.reshape(height, 2, width, 2, dim).mean((1, 3))
        for slot in np.flatnonzero(mapping == frame):
            pooled[int(slot) // 2].add_(merged, alpha=0.5)
    return pooled.to(dtype=torch.float16 if dtype is None else dtype)


def pool_patch_features(patches, coords, grid):
    """One viewpoint per temporal group, in Qwen's temporal/row/column order."""
    grid = torch.as_tensor(grid).detach().cpu().numpy()
    if grid.shape != (3,) or grid[0] != 32 or len(patches) != 32:
        raise ValueError('GX patch fusion requires 32 temporal groups and viewpoints')
    with torch.autocast(patches.device.type, enabled=False):
        pooled = pool_patches_online(patches, coords, grid,
                              [g for g in range(32) for _ in range(2)], dtype=torch.float32)
    return pooled.reshape(-1, patches.shape[-1])


class PatchFusion(nn.Module):
    """Zero-initialized patch delta; scoped hooks retain no batch state on the module."""
    def __init__(self, output_dim, hidden=1024):
        super().__init__()
        self.norm = nn.LayerNorm(2048)
        self.fc1 = nn.Linear(2048, hidden)
        self.act = nn.GELU()
        self.fc2 = nn.Linear(hidden, output_dim)
        nn.init.zeros_(self.fc2.weight)
        nn.init.zeros_(self.fc2.bias)

    def forward(self, features):
        return self.fc2(self.act(self.fc1(self.norm(features))))

    def pool_project(self, *inputs):
        """Recompute ROI pooling and the projector together during backward."""
        pooled = torch.cat([pool_patch_features(*inputs[i:i+3]) for i in range(0, len(inputs), 3)])
        return self(pooled.to(device=self.fc1.weight.device, dtype=self.fc1.weight.dtype))

    @contextmanager
    def inject(self, visual, features, video_grid, metrics, *, checkpointing=False):
        pending = features
        def hook(module, args, kwargs, output):
            nonlocal pending
            grid = kwargs.get('grid_thw', args[1] if len(args) > 1 else None)
            # Qwen passes the original modality grid through to the shared tower.
            if grid is not video_grid:
                return output
            value, pending = pending, None
            if value is None:
                raise ValueError('GX patch features were consumed twice')
            pooled = output.pooler_output if hasattr(output, 'pooler_output') else output[1]
            if int((grid.prod(-1) // 4).sum()) != len(pooled):
                raise ValueError('GX patch features and merged video token count differ')
            if checkpointing:
                inputs = tuple(tensor for row in value for tensor in row)
                delta = (checkpoint(self.pool_project, *inputs, use_reentrant=False) if torch.is_grad_enabled()
                         else self.pool_project(*inputs)).to(pooled.dtype)
            else:
                if value.shape != (pooled.shape[0], 2048):
                    raise ValueError('GX patch features and merged video token count differ')
                delta = self(value.to(device=pooled.device, dtype=self.fc1.weight.dtype)).to(pooled.dtype)
            if delta.shape != pooled.shape:
                raise ValueError('GX patch features and merged video token count differ')
            with torch.no_grad():
                metrics['patch_delta_ratio'] = float(delta.float().square().mean().sqrt() /
                    pooled.float().square().mean().sqrt().clamp_min(1e-12))
            merged = pooled + delta
            if hasattr(output, 'pooler_output'):
                output.pooler_output = merged
                return output
            return (output[0], merged, *output[2:])
        handle = visual.register_forward_hook(hook, with_kwargs=True)
        try:
            yield
            if pending is not None:
                raise ValueError('GX patch features were not consumed by the video forward')
        finally:
            handle.remove()
            pending = None


def learning_rate_ramp(settings, step):
    ft = settings['finetune']
    return min(1., max(0., (step-ft['hold_steps']) / ft['warmup_steps']))
