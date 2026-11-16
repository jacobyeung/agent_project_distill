"""Opt-in single-image re-reads from the same LM during routed generate().

The caller supplies original RGB anchors and their source-frame identities.
Each query has its own native image cache. The routed video cache stays private.
The hrp.selector dependency comes from the delivered hrp_infer lane.
"""
from dataclasses import dataclass
import hashlib
import json
import math

import numpy as np
import torch

from hrp.selector import from_points, select
from .ground_lifting import OwnGeometryAdapter, public_centres, render_ground
from .carrier_c1_routing import RenderError


@dataclass(frozen=True)
class Config:
    frames: dict  # {1-based anchor slot: uint8 RGB array or PIL RGB image}
    frame_indices: tuple  # All 32 source-frame indices, identical to the video batch.
    max_pixels: int = 602112
    radius_m: float = .5
    min_support: int = 1
    max_queries: int = 256  # Hard per-generate budget, including null/invalid reads.
    max_new_tokens: int = 48

    def validate(self, batch):
        expected = batch.get('hrp_frame_indices')
        if hasattr(expected, 'tolist'):
            expected = expected.tolist()
        if (expected is None or tuple(expected) != tuple(self.frame_indices)
                or len(self.frame_indices) != 32 or any(type(i) is not int or i < 0 for i in self.frame_indices)
                or list(self.frame_indices) != sorted(set(self.frame_indices))):
            raise ValueError('HRP requires the video batch’s exact 32 source-frame indices')
        if not self.frames or any(type(k) is not int or not 1 <= k <= 32 for k in self.frames):
            raise ValueError('HRP frames must be keyed by anchor slots 1..32')
        if type(self.max_pixels) is not int or self.max_pixels < 65536:
            raise ValueError('HRP max_pixels must be at least 65536')
        if not math.isfinite(self.radius_m) or self.radius_m <= 0:
            raise ValueError('HRP radius must be positive')
        if any(type(n) is not int or n < 1 for n in (self.min_support, self.max_queries, self.max_new_tokens)):
            raise ValueError('HRP support and budgets must be positive integers')
        for image in self.frames.values():
            a = np.asarray(image)
            if a.dtype != np.uint8 or a.ndim != 3 or a.shape[2] != 3 or min(a.shape[:2]) < 1:
                raise ValueError('HRP requires original uint8 RGB images')


def parse_point(raw):
    """Accept one native JSON point or null; never choose among multiple instances."""
    try:
        value = json.loads(raw)
    except (ValueError, TypeError):
        return None, 'invalid'
    if isinstance(value, list):
        if not value:
            return None, 'null'
        if len(value) != 1:
            return None, 'multiple'
        value = value[0]
    if not isinstance(value, dict) or 'point_2d' not in value:
        return None, 'invalid'
    point = value['point_2d']
    if point is None:
        return None, 'null'
    if (not isinstance(point, list) or len(point) != 2
            or any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1000 for v in point)
            or max(point) <= 10):
        return None, 'invalid'
    return point, 'point'


class Geometry(OwnGeometryAdapter):
    def has(self, frame):
        if self.geometry is None:
            return False
        try:
            self.cam(frame)
            self.geometry.fov(frame)
            return True
        except (ValueError, RenderError):
            return False


@torch.no_grad()
def read_image(model, processor, image, name, config):
    """Native single-image prompt; no video/GT values enter the image query."""
    from .verify_pass import native_view
    model=native_view(model)
    from PIL import Image
    if not isinstance(image, Image.Image):
        image = Image.fromarray(np.asarray(image))
    prompt = ('Point to the {obj} in this image. Output the point as JSON {{"point_2d": [x, y]}} '
              'with integer coordinates on a 0-1000 grid. If there is no {obj} in the image, '
              'output {{"point_2d": null}}.').format(obj=name)
    messages = [{'role': 'user', 'content': [{'type': 'image'}, {'type': 'text', 'text': prompt}]}]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    encoded = processor(text=[text], images=[image], return_tensors='pt', padding=True,
                        size=dict(shortest_edge=65536, longest_edge=config.max_pixels))
    allowed = ('input_ids', 'attention_mask', 'pixel_values', 'image_grid_thw', 'mm_token_type_ids')
    device = model.get_input_embeddings().weight.device
    batch = {k: v.to(device) for k, v in encoded.items() if k in allowed}
    if 'pixel_values' not in batch or 'image_grid_thw' not in batch:
        raise ValueError('HRP processor did not produce an image batch')
    prefix = batch['input_ids'].shape[1]
    if prefix + config.max_new_tokens > model.config.text_config.max_position_embeddings:
        raise ValueError('HRP image query exceeds context')
    # Qwen stores multimodal position offsets on the shared model, outside KV.
    # Restoring the exact object also protects the outer cache on exceptions.
    from .reread_isolation import isolated
    ids=isolated(model,lambda:model.generate(**batch,do_sample=False,max_new_tokens=config.max_new_tokens,
                                             return_dict_in_generate=False))
    suffix = ids[0, prefix:].tolist()
    eos = processor.tokenizer.eos_token_id
    capped = len(suffix) >= config.max_new_tokens and (not suffix or suffix[-1] != eos)
    raw = processor.tokenizer.decode(suffix, skip_special_tokens=True)
    point, status = parse_point(raw)
    return dict(raw_output=raw, point_2d=None if capped else point,
                parse_status='capped' if capped else status, generated_tokens=len(suffix))


def render(name, rows, geometry, registry, radius, min_support):
    candidates = from_points(rows)
    try:
        selection = select(candidates, geometry, radius)
    except (ValueError, RenderError):
        return name + ': not seen', dict(status='invalid_geometry')
    if (selection['position'] is None or selection['support'] < min_support
            or selection['status'] == 'ambiguous'):
        return name + ': not seen', selection
    frame = selection['best_frame']
    candidate = next(candidates[i] for i in selection['candidate_indices'] if candidates[i].frame == frame)
    try:
        camera, f1 = public_centres(geometry, frame, np.asarray(selection['position']))
        spread = float(geometry.lift(frame, np.asarray(candidate.uv)[None])[2][0])
        if not math.isfinite(spread) or spread < 0:
            return name + ': not seen', selection
        result = dict(name=name, seen=True, frames=selection['frames_kept'], best=frame,
                      camera=camera, f1=f1, spread=spread, size=None)
        return render_ground(result, registry), selection
    except (ValueError, RenderError):
        return name + ': not seen', selection


class Backend:
    def __init__(self, model, processor, geometry, config):
        self.model, self.processor, self.config = model, processor, config
        self.geometry = Geometry(geometry)
        self.by_name, self.queries = {}, []
        self.query_count = 0

    def ground(self, name, registry):
        if name not in self.by_name:
            # Refuse the whole object before partial reads when the budget ends.
            if self.query_count + len(self.config.frames) > self.config.max_queries:
                raise RenderError('hrp_query_budget')
            rows = []
            for frame, image in sorted(self.config.frames.items()):
                self.query_count += 1
                value = read_image(self.model, self.processor, image, name, self.config)
                rgb = np.asarray(image)
                rows.append(dict(frame=frame, source_index=self.config.frame_indices[frame-1],
                                 obj=name, source='hrp_reread', source_hw=list(rgb.shape[:2]),
                                 pixel_sha256=hashlib.sha256(rgb.tobytes()).hexdigest(), **value))
            item = dict(name=name, backend='hrp_reread', rows=rows,
                        frame_indices=list(self.config.frame_indices), max_pixels=self.config.max_pixels,
                        radius_m=self.config.radius_m, min_support=self.config.min_support)
            self.by_name[name] = item
            self.queries.append(item)
        item = self.by_name[name]
        text, selection = render(name, item['rows'], self.geometry, registry,
                                 item['radius_m'], item['min_support'])
        item['selection'] = selection
        return text


class ReplayBackend:
    def __init__(self, queries, geometry, registry):
        self.queries, self.geometry, self.registry = queries, Geometry(geometry), registry

    def ground(self, name):
        q = self.queries[name]
        return render(name, q['rows'], self.geometry, self.registry, q['radius_m'], q['min_support'])[0]
