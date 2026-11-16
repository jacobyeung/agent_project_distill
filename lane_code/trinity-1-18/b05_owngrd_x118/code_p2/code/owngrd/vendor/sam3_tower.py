"""Opt-in frozen SAM 3 image tower. No SAM import or weight load at import time."""
from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager, nullcontext
import hashlib
import json
from pathlib import Path
import re
import sys
from unittest.mock import patch

import torch
import torch.nn.functional as F

CHECKPOINT_SHA256 = '9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e'
UPSTREAM_REVISION = '5dd401d1c5c1d5c3eedff06d41b77af824517619'
SINGULAR = {'kitchen cabinets': 'kitchen cabinet', 'cabinets': 'cabinet', 'chairs': 'chair',
            'tables': 'table', 'doors': 'door', 'windows': 'window', 'shelves': 'shelf',
            'bookshelves': 'bookshelf', 'desks': 'desk', 'beds': 'bed', 'sofas': 'sofa',
            'couches': 'couch', 'curtains': 'curtain', 'blinds': 'window blind',
            'books': 'book', 'pillows': 'pillow', 'lamps': 'lamp', 'boxes': 'box',
            'pictures': 'picture', 'towels': 'towel', 'clothes': 'clothing',
            'clothes dryers': 'clothes dryer', 'pipes': 'pipe'}


def normalize_phrase(label: str) -> str:
    label = ' '.join(label.lower().replace('_', ' ').split())
    return SINGULAR.get(label, label)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


@dataclass(frozen=True)
class ClipFeatures:
    """CPU image features, reusable across names. Caller owns the clip lifetime."""
    frames: tuple[dict, ...]
    sizes: tuple[tuple[int, int], ...]  # (height, width)
    owner: object


@dataclass(frozen=True)
class FrameDetections:
    """CPU tensors; boxes are source-pixel xyxy; masks are N x H x W bool."""
    presence: float
    scores: torch.Tensor  # independent instance probability, as in ttower
    joint_scores: torch.Tensor
    boxes: torch.Tensor
    masks: torch.Tensor
    query_ids: torch.Tensor
    all_scores: torch.Tensor


def _map_tensors(value, fn):
    if isinstance(value, torch.Tensor):
        return fn(value)
    if isinstance(value, dict):
        return {k: _map_tensors(v, fn) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return type(value)(_map_tensors(v, fn) for v in value)
    if value is None:
        return None
    raise TypeError(f'Unexpected SAM image feature type: {type(value)}')


def _addmm_act_float32(activation, linear, mat1):
    """SAM's fused MLP without its unconditional bf16 casts, for fp32 controls."""
    if activation not in (torch.nn.ReLU, torch.nn.GELU, F.relu, F.gelu):
        raise ValueError('Unsupported SAM fused activation')
    x = mat1.float()
    y = torch.ops.aten._addmm_activation(
        linear.bias.detach().float(), x.reshape(-1, x.shape[-1]), linear.weight.detach().float().t(),
        beta=1, alpha=1, use_gelu=activation in (torch.nn.GELU, F.gelu))
    return y.reshape(*x.shape[:-1], y.shape[-1])


def postprocess(outputs, size, *, legacy=False):
    """Use SAM's sigmoid precision, then order by (-score, query id)."""
    h, w = size
    scores = outputs['pred_logits'].sigmoid().reshape(-1).float()
    presence = float(outputs['presence_logit_dec'].sigmoid().item())
    if not torch.isfinite(scores).all() or not 0 <= presence <= 1:
        raise ValueError('SAM produced nonfinite probabilities')
    joint = scores * presence
    # Scores are in ascending query-id order. Stable sorting makes the second
    # key explicit, including ties across the retention cap in bf16.
    order = torch.argsort(scores, descending=True, stable=True)
    keep = order[(scores if legacy else joint)[order] >= (.3 if legacy else .2)]
    keep = keep[:5 if legacy else 10]
    # Match box_cxcywh_to_xyxy before the float conversion used by ttower.
    cx, cy, bw, bh = outputs['pred_boxes'].reshape(-1, 4).unbind(-1)
    boxes = torch.stack((cx - .5*bw, cy - .5*bh, cx + .5*bw, cy + .5*bh), -1).float()
    boxes *= boxes.new_tensor([w, h, w, h])
    native = outputs['pred_masks'].reshape(-1, *outputs['pred_masks'].shape[-2:])
    masks = [
        (F.interpolate(native[i][None, None].float(), (h, w), mode='bilinear',
                       align_corners=False).sigmoid()[0, 0] > .5).cpu()
        for i in keep.tolist()
    ]
    return FrameDetections(presence, scores[keep].cpu(), joint[keep].cpu(),
                           boxes[keep].cpu(), torch.stack(masks) if masks else
                           torch.empty((0, h, w), dtype=torch.bool), keep.cpu(), scores.cpu())


class Sam3Tower:
    """Plain object: its frozen module is invisible to parent nn.Module traversal.

    encode runs the image backbone once per image and offloads reusable features
    to CPU. Native image batching is an explicit diagnostic override. detect
    transfers one frame at a time, bounding GPU residency.
    The parent model's train(), to(), optimizer and FSDP never manage this tower.
    """
    def __init__(self, settings, *, backend=None):
        self.settings = dict(settings)
        allowed = {'checkpoint_path', 'receipt_path', 'source_root', 'device', 'precision',
                   'image_batch_size', 'native_image_batch'}
        if set(self.settings) - allowed:
            raise ValueError('Unknown SAM 3 tower setting')
        self.device = torch.device(self.settings.get('device', 'cuda'))
        self.precision = self.settings.get('precision', 'bf16' if self.device.type == 'cuda' else 'float32')
        if self.precision not in {'bf16', 'float32'}:
            raise ValueError('precision must be bf16 or float32')
        self.image_batch_size = self.settings.get('image_batch_size', 1)
        self.native_image_batch = self.settings.get('native_image_batch', False)
        if type(self.image_batch_size) is not int or not 1 <= self.image_batch_size <= 8:
            raise ValueError('image_batch_size must be an integer from 1 to 8')
        if type(self.native_image_batch) is not bool:
            raise ValueError('native_image_batch must be a bool')
        self._owner = object()
        self._backend = backend
        self.receipt = None
        if backend is None:
            if not {'checkpoint_path', 'receipt_path', 'source_root'} <= self.settings.keys():
                raise ValueError('SAM 3 needs local checkpoint, source root and receipt')
            if self.device.type not in {'cuda', 'cpu'}:
                raise ValueError('SAM 3 requires a CUDA or CPU device')
        else:
            self._freeze()

    def _freeze(self):
        self._backend.model.to(self.device).eval().requires_grad_(False)

    def _load(self):
        if self._backend is not None:
            self._backend.model.eval().requires_grad_(False)
            return
        root = Path(self.settings['source_root']).resolve()
        checkpoint = Path(self.settings['checkpoint_path']).resolve()
        if not str(root).startswith(('/scratch/', '/dev/shm/')) or not str(checkpoint).startswith(('/scratch/', '/dev/shm/')):
            raise ValueError('Stage SAM source and checkpoint on local /scratch before inference')
        receipt = json.loads(Path(self.settings['receipt_path']).read_text())
        if (receipt['checkpoint_sha256'] != CHECKPOINT_SHA256 or
                receipt['sam3_upstream_revision'] != UPSTREAM_REVISION):
            raise ValueError('Unexpected SAM checkpoint or upstream revision pin')
        if sha256(checkpoint) != CHECKPOINT_SHA256:
            raise ValueError('SAM checkpoint content differs from receipt')
        required = {'sam3/model_builder.py', 'sam3/model/sam3_image_processor.py',
                    'sam3/model/sam3_image.py', 'sam3/model/vl_combiner.py',
                    'sam3/model/box_ops.py', 'sam3/model/data_misc.py'}
        if set(receipt['source_files']) != required:
            raise ValueError('Incomplete SAM implementation receipt')
        for name, expected in receipt['source_files'].items():
            if not re.fullmatch('[0-9a-f]{64}', expected) or sha256(root/name) != expected:
                raise ValueError('SAM source content differs: ' + name)
        if 'sam3' in sys.modules:
            if Path(sys.modules['sam3'].__file__).resolve().parent != root/'sam3':
                raise ValueError('Another SAM package was imported before tower attachment')
        sys.path.insert(0, str(root))
        from sam3.model_builder import build_sam3_image_model
        from sam3.model.sam3_image_processor import Sam3Processor
        model = build_sam3_image_model(checkpoint_path=str(checkpoint), load_from_HF=False,
                                      device=str(self.device), eval_mode=True,
                                      enable_inst_interactivity=False)
        self._backend = Sam3Processor(model, resolution=1008, device=str(self.device))
        self._freeze()
        self.receipt = receipt

    @contextmanager
    def _autocast(self):
        # Upstream addmm_act casts to bf16 even with autocast disabled, making
        # its following float32 Linear fail. Scope the fp32 control to this call.
        vitdet = sys.modules.get('sam3.model.vitdet')
        control = (patch.object(vitdet, 'addmm_act', _addmm_act_float32)
                   if self.precision == 'float32' and vitdet is not None else nullcontext())
        with control, torch.autocast(self.device.type, dtype=torch.bfloat16,
                                     enabled=self.precision == 'bf16'):
            yield

    @torch.inference_mode()
    def encode(self, frames):
        """Encode a nonempty sequence of native RGB PIL images, once per clip."""
        from PIL import Image
        frames = list(frames)
        if not frames or any(not isinstance(f, Image.Image) or f.mode != 'RGB' for f in frames):
            raise ValueError('encode requires nonempty native RGB PIL frames')
        self._load()
        encoded = []
        for offset in range(0, len(frames), self.image_batch_size):
            group = frames[offset:offset + self.image_batch_size]
            batches = [group] if self.native_image_batch else [[im] for im in group]
            for batch in batches:
                with self._autocast():
                    state = (self._backend.set_image_batch(batch) if self.native_image_batch
                             else self._backend.set_image(batch[0]))
                backbone = state['backbone_out']
                # The grounding path uses only these pyramids; SAM2 features are unused.
                image = {k: backbone[k] for k in ('backbone_fpn', 'vision_pos_enc')}
                for i in range(len(batch)):
                    def take(t):
                        if t.ndim != 4 or t.shape[0] != len(batch):
                            raise ValueError('Expected SAM image features with shape B,C,H,W')
                        return t[i:i+1].detach().to('cpu', copy=True)
                    encoded.append(_map_tensors(image, take))
                del state, backbone, image
        return ClipFeatures(tuple(encoded), tuple((f.height, f.width) for f in frames), self._owner)

    @torch.inference_mode()
    def _detect(self, features, phrase, *, legacy=False):
        if not isinstance(features, ClipFeatures) or features.owner is not self._owner:
            raise ValueError('Features must come from this Sam3Tower instance')
        phrase = normalize_phrase(phrase)
        if not phrase:
            raise ValueError('SAM phrase must not be empty')
        self._load()
        results = []
        with self._autocast():
            text = self._backend.model.backbone.forward_text([phrase], device=str(self.device))
        for stored, size in zip(features.frames, features.sizes):
            backbone = _map_tensors(stored, lambda t: t.to(self.device))
            backbone['vision_features'] = backbone['backbone_fpn'][-1]
            backbone.update(text)
            with self._autocast():
                raw = self._backend.model.forward_grounding(
                    backbone_out=backbone, find_input=self._backend.find_stage,
                    geometric_prompt=self._backend.model._get_dummy_prompt(), find_target=None)
                results.append((postprocess(raw, size), postprocess(raw, size, legacy=True))
                               if legacy is None else postprocess(raw, size, legacy=legacy))
            del raw, backbone
        return results

    def detect(self, features, phrase):
        """Return per-frame presence and up to ten proposals with joint >= 0.2."""
        return self._detect(features, phrase)

    def detect_cache_reference(self, features, phrase):
        """Validation only: ttower's independent >= 0.3, cap-five mask contract."""
        return self._detect(features, phrase, legacy=True)


def attach_sam3_tower(model, settings=None, *, enabled=False, backend=None):
    """Explicit inference flag; disabled attachment is a no-op, with no imports."""
    if type(enabled) is not bool:
        raise ValueError('enabled must be a bool')
    if not enabled:
        return None
    if hasattr(model, 'sam3_tower'):
        raise ValueError('SAM 3 tower is already attached')
    tower = Sam3Tower(settings or {}, backend=backend)
    model.sam3_tower = tower
    return tower
