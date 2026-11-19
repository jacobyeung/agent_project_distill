"""Local G3T camera-token inference and strict clip-cache binding."""
import importlib
from pathlib import Path
import sys

import numpy as np

REPOSITORY = 'thatbrguy/g3t'
REVISION = 'c55e91a04f1cbbad67359072536351201fd19e8b'
INPUT = 'square_pad_1024_bilinear_518'
KEYS = frozenset({'cam_token_l23', 'local_pose_enc', 'global_pose_enc', 'coords_1024',
                  'frames_tar_sha256', 'ordinals', 'qid'})


def source_import(source_dir):
    """Refuse a pre-imported package from a different source directory."""
    root = Path(source_dir).resolve()
    if not (root / 'vggt/models/g3t.py').is_file():
        raise ValueError('Missing local teacher source')
    for name, module in tuple(sys.modules.items()):
        if name == 'vggt' or name.startswith('vggt.'):
            file = getattr(module, '__file__', None)
            if file and not Path(file).resolve().is_relative_to(root):
                raise ValueError('Another teacher source is already imported')
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return importlib.import_module('vggt.models.g3t').G3T


def camera_forward(model, inputs, verify_full=False, *, video_grid_thw=None, coords=None, slot_map=None):
    """Use the sidecar aggregator/head operation order for any even clip length."""
    import torch
    cuda = inputs.device.type == 'cuda'
    with torch.inference_mode():
        with torch.autocast('cuda', dtype=torch.bfloat16, enabled=cuda):
            tokens, patch_start = model.aggregator(inputs[None])
        with torch.amp.autocast('cuda', enabled=False):
            local = model.local_camera_head(tokens)[-1]
            global_ = model.global_camera_head(tokens)[-1]
        if verify_full:
            with torch.autocast('cuda', dtype=torch.bfloat16, enabled=cuda):
                full = model(inputs[None])
            if not (torch.equal(local, full['local_pose_enc']) and torch.equal(global_, full['global_pose_enc'])):
                raise ValueError('Teacher camera path differs from full forward')
    n = len(inputs)
    if patch_start != 5 or len(tokens) <= 23 or tuple(tokens[23].shape[:2]) != (1, n):
        raise ValueError('Teacher layer or special-token layout changed')
    block = tokens[23]
    if block.ndim != 4 or block.shape[-1] != 2048:
        raise ValueError('Teacher camera width changed')
    result = {'cam_token_l23': block[0, :, 0, :].to(dtype=torch.float16).cpu().numpy(),
              'local_pose_enc': local[0].float().cpu().numpy(),
              'global_pose_enc': global_[0].float().cpu().numpy()}
    if video_grid_thw is not None:
        result['patch_pooled'] = pool_patches(block[0, :, 5:, :], coords, video_grid_thw, slot_map).cpu().numpy()
    return result


class Teacher:
    def __init__(self, source_dir, weights_dir, device):
        import torch
        root = Path(weights_dir).resolve()
        if not (root / 'config.json').is_file() or not (root / 'model.safetensors').is_file():
            raise ValueError('Teacher needs local configuration and weights')
        cls = source_import(source_dir)
        self.model = cls.from_pretrained(str(root), local_files_only=True).eval().to(device)
        self.device = torch.device(device)
        self.verified = False
        self.preprocess = importlib.import_module('vggt.utils.load_fn').load_and_preprocess_images_square

    def extract(self, images, *, video_grid_thw=None, slot_map=None):
        """Accept JPEG byte streams or image paths, exactly as the upstream loader does."""
        import torch
        import torch.nn.functional as functional
        images, coords = self.preprocess(images, 1024)
        with torch.inference_mode():
            inputs = functional.interpolate(images.to(self.device), size=(518, 518),
                                            mode='bilinear', align_corners=False)
            result = camera_forward(self.model, inputs, verify_full=not self.verified and video_grid_thw is None,
                                    video_grid_thw=video_grid_thw, coords=coords[:, :4], slot_map=slot_map)
        self.verified = True
        result['coords_1024'] = np.ascontiguousarray(coords.float().cpu().numpy()[:, :4])
        validate_arrays(result, len(images))
        return result


def validate_arrays(data, n):
    for key, shape, dtype in (('cam_token_l23', (n, 2048), np.float16),
                              ('local_pose_enc', (n, 6), np.float32),
                              ('global_pose_enc', (n, 5), np.float32),
                              ('coords_1024', (n, 4), np.float32)):
        array = data[key]
        if array.shape != shape or array.dtype != dtype or not np.isfinite(array).all():
            raise ValueError('Invalid teacher array: ' + key)


def verify_npz(path, row, frames_sha256):
    with np.load(path, allow_pickle=False) as data:
        expected_keys = KEYS_V2 if row.get('schema') == 'c1r-clip-row-v2' else KEYS
        if set(data.files) != expected_keys:
            raise ValueError('Teacher cache keys changed')
        validate_arrays(data, row['N'])
        if (data['ordinals'].dtype != np.int64 or data['ordinals'].tolist() != row['ordinals']
                or data['qid'].shape != () or str(data['qid'].item()) != row['qid']
                or data['frames_tar_sha256'].shape != ()
                or str(data['frames_tar_sha256'].item()) != frames_sha256):
            raise ValueError('Teacher cache clip binding mismatch')
        if expected_keys == KEYS_V2:
            validate_cache_v2(data, row)
    return True


KEYS_V2 = KEYS | frozenset({'patch_pooled', 'video_grid_thw', 'camera', 'camera_mask',
    'trajectory_scale', 'gravity', 'gravity_mask', 'anchor_slots', 'slot_map', 'viewpoints', 'slots',
    'layout', 'row_sha256', 'processor_sha256'})


def pool_patches(patches, coords_1024, video_grid_thw, slot_map):
    """Area-pool a square teacher grid over its valid ROI, then merge spatially and temporally.

    The processor grid is UNMERGED [T,2h,2w]. Each source token is constant on
    its 1/37-square cell. Output [T,h,w,D] flattens directly in LM video-token order.
    Pool one distinct frame at a time to bound FP32 working memory.
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
    for frame, (x1, y1, x2, y2) in enumerate(coords):
        block = patches[frame].float().reshape(37, 37, dim)
        if not torch.isfinite(block).all():
            raise ValueError('Nonfinite teacher patches')
        x, y = weights(x1, x2, cols), weights(y1, y2, rows)
        unmerged = torch.einsum('ai,ijd,bj->abd', y, block, x)
        merged = unmerged.reshape(height, 2, width, 2, dim).mean((1, 3))
        for slot in np.flatnonzero(mapping == frame):
            pooled[int(slot) // 2].add_(merged, alpha=0.5)
    return pooled.to(dtype=torch.float16)


def validate_cache_v2(data, row):
    import hashlib
    import json
    import re
    validate_arrays(data, len(row['ordinals']))
    if (data['ordinals'].dtype != np.int64 or data['ordinals'].tolist() != row['ordinals']
            or data['qid'].shape != () or str(data['qid'].item()) != row['qid']
            or data['frames_tar_sha256'].shape != ()
            or not re.fullmatch(r'[0-9a-f]{64}', str(data['frames_tar_sha256'].item()))):
        raise ValueError('Teacher clip identity mismatch')
    coords = data['coords_1024']
    if ((coords[:, :2] < 0).any() or (coords[:, 2:] > 1024).any()
            or (coords[:, 2:] <= coords[:, :2]).any()):
        raise ValueError('Teacher valid ROI mismatch')
    grid = data['video_grid_thw']
    if (grid.shape != (3,) or grid.dtype != np.int64 or (grid <= 0).any()
            or grid[1] % 2 or grid[2] % 2 or int(grid[0]) * 2 != len(row['slots'])):
        raise ValueError('Teacher processor grid mismatch')
    patches = data['patch_pooled']
    if (patches.shape != (int(grid[0]), int(grid[1]) // 2, int(grid[2]) // 2, 2048)
            or patches.dtype != np.float16 or not np.isfinite(patches).all()):
        raise ValueError('Teacher pooled patch mismatch')
    for key in ('viewpoints', 'slots', 'slot_map', 'anchor_slots'):
        if data[key].dtype != np.int64 or data[key].tolist() != row[key]:
            raise ValueError('Teacher slot binding mismatch')
    digest = hashlib.sha256(json.dumps(row, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    if (data['layout'].shape != () or str(data['layout'].item()) != row['layout']
            or data['row_sha256'].shape != () or str(data['row_sha256'].item()) != digest
            or data['processor_sha256'].shape != () or not re.fullmatch(r'[0-9a-f]{64}', str(data['processor_sha256'].item()))):
        raise ValueError('Teacher row or processor binding mismatch')
    for key, shape, dtype in (('camera', (32, 9), np.float64), ('camera_mask', (32,), np.bool_),
                              ('trajectory_scale', (), np.float64), ('gravity', (3,), np.float64),
                              ('gravity_mask', (), np.bool_)):
        if data[key].shape != shape or data[key].dtype != dtype or not np.isfinite(data[key]).all():
            raise ValueError('Teacher target mismatch: ' + key)
    if (not data['camera_mask'].all() or not data['gravity_mask'].item()
            or data['trajectory_scale'].item() < 0):
        raise ValueError('Teacher target validity mismatch')
