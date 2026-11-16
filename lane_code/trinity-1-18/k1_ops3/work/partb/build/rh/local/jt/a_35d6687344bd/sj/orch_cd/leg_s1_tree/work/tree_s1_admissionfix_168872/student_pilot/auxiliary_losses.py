"""Small readouts on the student's final language-norm states.

Pose, depth, count, object and camera heads train only and are dropped at
inference. Query-token heads also run inside generation, where a query token in
the reasoning calls them and their formatted output is appended as the value.
"""
import math

import torch
from torch import nn
from torch.nn import functional as F

from . import auxiliary_reason as reason
from . import camera_config
from .auxiliary_config import enabled, mixing_active, normalize, ramp, reason_enabled, weight

QUERY_SLOTS = 4
TERMS = ('pose', 'depth', 'count', 'object', 'reason', 'camera')
CAMERA_COMPONENTS = ('pose', 'gravity', 'scale', 'point_depth')
# Regression readout column for each query kind; TIME uses the pointer head.
REGRESSION_COLUMN = [reason.REGRESSION_KINDS.index(kind) if kind in reason.REGRESSION_KINDS else -1
                     for kind in reason.KINDS]
# ANGLE reads the two columns after the regression outputs, (sin, cos); COORD reads the next one.
ANGLE_COLUMNS = slice(len(reason.REGRESSION_KINDS), len(reason.REGRESSION_KINDS) + 2)
COORD_COLUMN = len(reason.REGRESSION_KINDS) + 2


def readout(inputs, width, outputs):
    return nn.Sequential(nn.Linear(inputs, width), nn.GELU(), nn.Linear(width, outputs))


class AuxiliaryHeads(nn.Module):
    def __init__(self, hidden_size, config, camera=None, vit_dim=None):
        super().__init__()
        self.settings = normalize(config if config is not None else {})
        width = self.settings['head_width']
        if self.settings['pose_weight']:
            self.pose = nn.Sequential(nn.Linear(3 * hidden_size, width), nn.GELU(), nn.Linear(width, 9))
            with torch.no_grad():
                self.pose[-1].bias.copy_(torch.tensor([1., 0., 0., 0., 1., 0., 0., 0., 0.]))
        if self.settings['depth_weight']:
            self.depth = nn.Sequential(nn.Linear(hidden_size, width), nn.GELU(), nn.Linear(width, 1))
        if weight(self.settings, 'count'):
            # Per temporal group: [h_g, q_c, h_g * q_c]; whole video: [mean_g h_g, q_c].
            self.count_group = readout(3 * hidden_size, width, 1)
            self.count_scene = readout(2 * hidden_size, width, 1)
        if weight(self.settings, 'object'):
            self.object_query = nn.Linear(hidden_size, width)
            self.object_key = nn.Linear(hidden_size, width)
            self.object_value = nn.Linear(hidden_size, width)
            self.object = readout(width + hidden_size, width, 6)
        if reason_enabled(self.settings):
            self.reason_value = nn.ModuleDict({kind.lower(): readout(hidden_size, width, 1)
                                               for kind in reason.REGRESSION_KINDS})
            self.reason_time_query = readout(hidden_size, width, width)
            self.reason_time_key = nn.Linear(hidden_size, width)
            self.reason_angle = readout(hidden_size, width, 2)
            self.reason_coord = readout(hidden_size, width, 1)
        if camera_config.enabled(camera):
            from .camera_head import CameraSupervision
            self.camera = CameraSupervision(hidden_size, camera, vit_dim=vit_dim)
        self.width = width
        self.factor = self.camera_factor = 1.0
        self.reason_table = None
        self.camera_carrier = self.camera_final_layer = None
        self.last_terms = {}

    @property
    def needs_tokens(self):
        return hasattr(self, 'object')

    @property
    def has_reason(self):
        return hasattr(self, 'reason_value')

    @property
    def uses_group_features(self):
        """Whether a head reads the pooled per-group features (they assume 16 temporal groups); the camera head does not."""
        return any(hasattr(self, name) for name in ('pose', 'depth', 'count_group', 'object')) or self.has_reason

    @property
    def has_camera(self):
        return hasattr(self, 'camera')

    def set_step(self, step, total_steps):
        self.factor = ramp(step, total_steps, self.settings)
        if self.has_camera:
            self.camera_factor = camera_config.ramp(step, total_steps, self.camera.settings)
            self.camera.backbone_scale = camera_config.backbone_gradient_scale(step, self.camera.settings)

    def mixing(self, step, total_steps):
        return self.has_reason and mixing_active(step, total_steps, self.settings)

    def forward(self, features, targets, hidden=None, tokens=None, token_mask=None, layer_states=None, visual_grids=None,
                vit_grids=None):
        # [B, T, G, G, H], pooled from the processor's actual merged spatial grid.
        if features.ndim != 5 or features.shape[2:4] != (4, 4):
            raise ValueError('Expected B,T,4,4,H video features')
        result = features.new_zeros(features.shape[0], dtype=torch.float32)
        terms = {}
        frames = features.float().mean(dim=(2, 3))
        if hasattr(self, 'pose'):
            first = frames[:, :1].expand_as(frames)
            prediction = self.pose(torch.cat((first, frames, frames - first), dim=-1))
            target, mask = required(targets, 'aux_pose'), required(targets, 'aux_pose_mask')
            if target.shape != prediction.shape or mask.shape != prediction.shape[:2]:
                raise ValueError('Pose target shape mismatch')
            # Equal weight for the rotation and translation groups, not their dimensions.
            rotation = masked_row_loss(prediction[..., :6], target[..., :6], mask)
            translation = masked_row_loss(prediction[..., 6:], target[..., 6:], mask)
            terms['pose'] = rotation + translation
            result = result + self.settings['pose_weight'] * terms['pose']
        if hasattr(self, 'depth'):
            prediction = self.depth(features.float()).squeeze(-1)
            target, mask = required(targets, 'aux_depth'), required(targets, 'aux_depth_mask')
            if target.shape != prediction.shape or mask.shape != prediction.shape:
                raise ValueError('Depth target shape mismatch')
            terms['depth'] = masked_row_loss(prediction.unsqueeze(-1), target.unsqueeze(-1), mask)
            result = result + self.settings['depth_weight'] * terms['depth']
        if hasattr(self, 'count_group') or hasattr(self, 'object'):
            if hidden is None:
                raise ValueError('Category heads require the final language-norm states')
            query, present = category_queries(hidden, required(targets, 'aux_category_tokens'))
        if hasattr(self, 'count_group'):
            terms['count'] = self.count_loss(frames, query, present, targets)
            result = result + self.settings['count_weight'] * terms['count']
        if hasattr(self, 'object'):
            if tokens is None or token_mask is None:
                raise ValueError('The object head requires the prompt video token states')
            terms['object'] = self.object_loss(tokens, token_mask, query, present, targets)
            result = result + self.settings['object_weight'] * terms['object']
        if self.has_reason:
            if hidden is None:
                raise ValueError('Query-token heads require the final language-norm states')
            terms['reason'] = self.reason_loss(hidden, frames, targets)
            result = result + self.settings['reason_weight'] * terms['reason']
        total = self.factor * result
        if self.has_camera:
            if hidden is None:
                raise ValueError('The camera head requires the final language-norm states')
            # The camera term already carries its absolute pose, gravity, scale and depth weights.
            terms['camera'] = self.camera.loss(hidden, targets, layer_states, visual_grids=visual_grids, vit_grids=vit_grids)
            total = total + self.camera_factor * terms['camera']
        self.last_terms = {name: value.detach() for name, value in terms.items()}
        return total, terms

    def count_outputs(self, frames, query):
        """log1p counts per category: per temporal group [B,Q,16,1] and whole video [B,Q,1]."""
        groups = frames[:, None].expand(-1, query.shape[1], -1, -1)
        category = query[:, :, None].expand_as(groups)
        group_prediction = self.count_group(torch.cat((groups, category, groups * category), dim=-1))
        scene_input = torch.cat((frames.mean(dim=1)[:, None].expand(-1, query.shape[1], -1), query), dim=-1)
        return group_prediction, self.count_scene(scene_input)

    def count_loss(self, frames, query, present, targets):
        group_prediction, scene_prediction = self.count_outputs(frames, query)
        group_count, group_mask = required(targets, 'aux_group_count'), required(targets, 'aux_group_count_mask')
        scene_count, scene_mask = required(targets, 'aux_scene_count'), required(targets, 'aux_scene_count_mask')
        if group_count.shape != group_prediction.shape[:3] or scene_count.shape != scene_prediction.shape[:2]:
            raise ValueError('Count target shape mismatch')
        group_mask, scene_mask = group_mask & present[..., None], scene_mask & present
        group = masked_row_loss(group_prediction, torch.log1p(group_count.float().clamp_min(0))[..., None], group_mask)
        scene = masked_row_loss(scene_prediction, torch.log1p(scene_count.float().clamp_min(0))[..., None], scene_mask)
        return group + scene

    def object_loss(self, tokens, token_mask, query, present, targets):
        prediction = self.object_readout(tokens, token_mask, query)
        target, mask = required(targets, 'aux_object'), required(targets, 'aux_object_mask')
        if target.shape != prediction.shape or mask.shape != prediction.shape[:2]:
            raise ValueError('Object target shape mismatch')
        mask = mask & present
        # Equal weight for the centroid and log-extent groups.
        return masked_row_loss(prediction[..., :3], target[..., :3], mask) + masked_row_loss(prediction[..., 3:], target[..., 3:], mask)

    def object_readout(self, tokens, token_mask, query):
        keys, values = self.object_key(tokens), self.object_value(tokens)
        scores = torch.einsum('bqw,bnw->bqn', self.object_query(query), keys) / math.sqrt(self.width)
        attention = scores.masked_fill(~token_mask[:, None], float('-inf')).softmax(dim=-1)
        pooled = torch.einsum('bqn,bnw->bqw', attention, values)
        return self.object(torch.cat((pooled, query), dim=-1))

    def reason_outputs(self, hidden, frames, positions):
        """Regression, angle and coordinate outputs [B,Q,4+2+1] and temporal-group scores [B,Q,16] at query positions."""
        rows = torch.arange(hidden.shape[0], device=hidden.device)[:, None]
        states = hidden[rows, positions.clamp_min(0)].float()
        values = torch.cat([*(self.reason_value[kind.lower()](states) for kind in reason.REGRESSION_KINDS),
                            self.reason_angle(states), self.reason_coord(states)], dim=-1)
        keys = self.reason_time_key(frames)
        scores = torch.einsum('bqw,bgw->bqg', self.reason_time_query(states), keys) / math.sqrt(self.width)
        return values, scores

    def reason_loss(self, hidden, frames, targets):
        positions, kinds = required(targets, 'aux_reason_pos'), required(targets, 'aux_reason_kind')
        values, times = required(targets, 'aux_reason_value').float(), required(targets, 'aux_group_times').float()
        if kinds.shape != positions.shape or values.shape != positions.shape or times.shape != (positions.shape[0], reason.GROUPS):
            raise ValueError('Query-token target shape mismatch')
        valid = positions >= 0
        if torch.any(positions >= hidden.shape[1]) or torch.any(valid & (kinds < 0)):
            raise ValueError('Query positions or kinds are invalid')
        outputs, scores = self.reason_outputs(hidden, frames, positions)
        column = torch.tensor(REGRESSION_COLUMN, device=kinds.device)[kinds.clamp_min(0)]
        prediction = outputs.gather(-1, column.clamp_min(0)[..., None]).squeeze(-1)
        index = {kind: reason.KIND_INDEX[kind] for kind in reason.KINDS}
        target = torch.where(kinds == index['COUNT'], torch.log1p(values.clamp_min(0)),
                             torch.where(kinds == index['SIZE'], torch.log(values.clamp(*reason.CLIP['SIZE'])),
                                         torch.log(values.clamp(*reason.CLIP['DIST']))))
        is_time, is_angle, is_coord = kinds == index['TIME'], kinds == index['ANGLE'], kinds == index['COORD']
        regression, angle, coord = valid & ~is_time & ~is_angle & ~is_coord, valid & is_angle, valid & is_coord
        if not torch.isfinite(target[regression]).all():
            raise ValueError('Invalid query-token value target')
        # Mask before arithmetic, as for the sidecar heads.
        target = torch.where(regression, target, prediction.detach())
        regression_loss = F.smooth_l1_loss(prediction, target, reduction='none')
        group = (times[:, None, :] - values[..., None]).abs().argmin(dim=-1)
        time_loss = F.cross_entropy(scores.reshape(-1, scores.shape[-1]), group.reshape(-1), reduction='none').view_as(group)
        # ANGLE regresses the unit vector (sin, cos); SmoothL1 averaged over its two components.
        radians = torch.deg2rad(values)
        unit = torch.stack((torch.sin(radians), torch.cos(radians)), dim=-1)
        turn = outputs[..., ANGLE_COLUMNS]
        unit = torch.where(angle[..., None], unit, turn.detach())
        angle_loss = F.smooth_l1_loss(turn, unit, reduction='none').mean(dim=-1)
        # COORD regresses asinh(meters / scale): robust to the long tail of large offsets.
        offset = outputs[..., COORD_COLUMN]
        scaled = torch.where(coord, torch.asinh(values / reason.COORD_SCALE), offset.detach())
        coord_loss = F.smooth_l1_loss(offset, scaled, reduction='none')
        zero = torch.zeros_like(regression_loss)
        per_query = torch.where(valid & is_time, time_loss,
                                torch.where(regression, regression_loss,
                                            torch.where(angle, angle_loss, torch.where(coord, coord_loss, zero))))
        return per_query.sum(dim=1) / valid.sum(dim=1).clamp_min(1)

    def reason_texts(self, hidden, frames, targets):
        """Formatted head predictions per row, one string per valid query, in position order."""
        positions, kinds = targets['aux_reason_pos'], targets['aux_reason_kind']
        outputs, scores = self.reason_outputs(hidden, frames, positions)
        texts = []
        for row in range(positions.shape[0]):
            times = targets['aux_group_times'][row].tolist()
            row_texts = []
            for q in range(positions.shape[1]):
                if int(positions[row, q]) < 0:
                    continue
                row_texts.append(self.format(reason.KINDS[int(kinds[row, q])], outputs[row, q], scores[row, q], times))
            texts.append(row_texts)
        return texts

    def format(self, kind, outputs, scores, times):
        if kind == 'TIME':
            return reason.format_value(kind, int(scores.detach().argmax()), times)
        if kind == 'ANGLE':
            return reason.format_value(kind, outputs[ANGLE_COLUMNS].detach().tolist())
        if kind == 'COORD':
            return reason.format_value(kind, float(outputs[COORD_COLUMN].detach()))
        return reason.format_value(kind, float(outputs[reason.REGRESSION_KINDS.index(kind)].detach()))

    def manifest(self):
        result = {'settings': self.settings, 'inference_required': self.has_reason}
        if self.has_camera:
            result['camera'] = {'settings': self.camera.settings, 'inference_required': False,
                                'carrier': {'token': camera_config.CARRIER_TOKEN, 'id': self.camera_carrier}}
        if self.has_reason:
            result['query_tokens'] = {reason.KINDS[kind]: {'token': reason.QUERY_TOKENS[reason.KINDS[kind]], 'id': token}
                                      for token, kind in self.reason_table['query'].items()}
        return result


def required(targets, key):
    if key not in targets:
        raise ValueError('Missing auxiliary target: ' + key)
    return targets[key]


def category_queries(hidden, token_mask):
    """Mean final-norm state over each category name's prompt tokens: [B,Q,H] and presence [B,Q]."""
    if token_mask.ndim != 3 or token_mask.shape[0] != hidden.shape[0] or token_mask.shape[2] != hidden.shape[1]:
        raise ValueError('Category token mask must be B,Q,L')
    counts = token_mask.sum(dim=-1)
    rows, slots, positions = torch.nonzero(token_mask, as_tuple=True)
    flat = hidden.new_zeros(token_mask.shape[0] * token_mask.shape[1], hidden.shape[-1], dtype=torch.float32)
    flat = flat.index_add(0, rows * token_mask.shape[1] + slots, hidden[rows, positions].float())
    query = flat.view(*token_mask.shape[:2], -1) / counts.clamp_min(1)[..., None]
    return query, counts > 0


def masked_row_loss(prediction, target, mask):
    if mask.dtype != torch.bool or not torch.isfinite(prediction).all() or not torch.isfinite(target[mask]).all():
        raise ValueError('Invalid auxiliary prediction, mask, or supervised target')
    # Mask before arithmetic: NaN targets at missing cells cannot poison gradients.
    target = torch.where(mask.unsqueeze(-1), target.float(), prediction.detach().float())
    value = F.smooth_l1_loss(prediction.float(), target, reduction='none').mean(dim=-1)
    value = torch.where(mask, value, torch.zeros_like(value)).flatten(1)
    return value.sum(1) / mask.flatten(1).sum(1).clamp_min(1)


def video_features(hidden, batch, video_token_id, merge_size, tokens=False, any_groups=False, max_groups=16):
    """Pooled per-group features. Camera-only callers may expand capacity explicitly; rows pad to the batch's
    largest group count, at least 16. Legacy heads and RGB32 retain [B,16,4,4,H]."""
    ids, labels = batch['input_ids'], batch['labels']
    grids = batch['video_grid_thw']
    if hidden.shape[:2] != ids.shape or grids.shape != (ids.shape[0], 3):
        raise ValueError('Auxiliary heads require one video per row and full prompt hidden states')
    result, visual_tokens = [], []
    group_slots = max(16, int(grids[:, 0].max())) if any_groups else 16
    for i, (t, h, w) in enumerate(grids.tolist()):
        if not (t == 16 or any_groups and 1 <= t <= max_groups) or h % merge_size or w % merge_size:
            raise ValueError('Unexpected temporal or spatial video grid')
        h, w = h // merge_size, w // merge_size
        positions = torch.where((ids[i] == video_token_id) & batch['attention_mask'][i].bool())[0]
        if positions.numel() != t * h * w or torch.any(labels[i, positions] != -100):
            raise ValueError('Video token count or prompt masking mismatch')
        supervised = torch.where(labels[i] != -100)[0]
        if supervised.numel() and positions[-1] >= supervised[0]:
            raise ValueError('Auxiliary visual states must precede every assistant target')
        visual = hidden[i, positions].reshape(t, h, w, -1).permute(0, 3, 1, 2).float()
        pooled = F.adaptive_avg_pool2d(visual, (4, 4)).permute(0, 2, 3, 1)
        if t < group_slots:
            pooled = torch.cat((pooled, pooled.new_zeros(group_slots - t, *pooled.shape[1:])))
        result.append(pooled)
        if tokens:
            visual_tokens.append(hidden[i, positions].float())
    features = torch.stack(result)
    if not tokens:
        return features
    width = max(item.shape[0] for item in visual_tokens)
    padded = features.new_zeros(len(visual_tokens), width, features.shape[-1])
    mask = torch.zeros(len(visual_tokens), width, dtype=torch.bool, device=features.device)
    for i, item in enumerate(visual_tokens):
        padded[i, :item.shape[0]] = item
        mask[i, :item.shape[0]] = True
    return features, padded, mask


def visual_grids(hidden, batch, video_token_id, merge_size):
    """Per row, the states at its visual tokens in their spatial layout [t, h / m, w / m, H] (no pooling)."""
    ids, grids = batch['input_ids'], batch['video_grid_thw']
    if hidden.shape[:2] != ids.shape or grids.shape != (ids.shape[0], 3):
        raise ValueError('Visual grids require one video per row and full prompt hidden states')
    result = []
    for i, (t, h, w) in enumerate(grids.tolist()):
        if h % merge_size or w % merge_size:
            raise ValueError('Unexpected spatial video grid')
        h, w = h // merge_size, w // merge_size
        positions = torch.where((ids[i] == video_token_id) & batch['attention_mask'][i].bool())[0]
        if positions.numel() != t * h * w:
            raise ValueError('Video token count differs from video_grid_thw')
        result.append(hidden[i, positions].reshape(t, h, w, hidden.shape[-1]))
    return result


def final_norm(module):
    norms = [child for name, child in module.named_modules() if name.endswith('language_model.norm')]
    if len(norms) != 1:
        raise ValueError('Expected exactly one final language norm')
    return norms[0]


def unwrap(model):
    return model.module if isinstance(model, torch.nn.parallel.DistributedDataParallel) else model


def attach(model, config, tokenizer=None, camera=None):
    """Call after LoRA allowlist validation and before optimizer/distributed wrapping."""
    if not enabled(config) and not camera_config.enabled(camera):
        return None
    cfg = normalize(config if config is not None else {})
    if getattr(model.config, 'model_type', None) != 'qwen3_5':
        raise ValueError('Auxiliary integration currently supports native Qwen3.5 only')
    final_norm(model)
    # Isolate head initialization so the matched control keeps its dropout RNG stream.
    vit_dim = getattr(getattr(model.config, 'vision_config', None), 'hidden_size', None)
    with torch.random.fork_rng(devices=[]):
        heads = AuxiliaryHeads(model.config.text_config.hidden_size, cfg, camera, vit_dim=vit_dim)
    if heads.has_camera:
        if tokenizer is None:
            raise ValueError('Camera tokens require the student tokenizer')
        from .camera_targets import carrier_id
        heads.camera_carrier = carrier_id(tokenizer)
        heads.camera_final_layer = model.config.text_config.num_hidden_layers
        if max(heads.camera.settings['feature_layers'] or [0]) > heads.camera_final_layer:
            raise ValueError('Camera feature layers exceed the student depth')
        from .camera_head import decoder_layers
        if sorted(decoder_layers(model)) != list(range(heads.camera_final_layer)):
            raise ValueError('Camera feature layers need every decoder layer of the student')
    if heads.has_reason:
        if tokenizer is None:
            raise ValueError('Query-token heads require the student tokenizer')
        heads.reason_table = reason.token_table(tokenizer)
        vocabulary = getattr(model.get_output_embeddings(), 'out_features', None)
        if vocabulary is not None and max(heads.reason_table['query']) >= vocabulary:
            raise ValueError('Query token ids exceed the student vocabulary')
    heads.to(device=next(model.parameters()).device, dtype=torch.float32)
    model.add_module('auxiliary_heads', heads)
    return heads


def camera_head_inputs(heads, unwrapped, batch, output, captured, vit_captured, need_depth):
    """What the camera heads read from one forward: (layer_states, visual grids, ViT grids).

    Training (capture) and the phase-2 head API (capture_camera_states) both call this, so the heads
    read the same states in both: carrier states at the configured layers, and for depth the row's
    final-norm visual-token grid plus its ViT block grids in raster order."""
    from .camera_head import gather_positions
    merge = unwrapped.config.vision_config.spatial_merge_size
    positions = batch['aux_camera_positions']
    layer_states = {k: gather_positions(states, positions) for k, states in captured.items()}
    if heads.camera_final_layer in (heads.camera.settings['feature_layers'] or []):
        layer_states[heads.camera_final_layer] = gather_positions(output, positions)
    grids = vit = None
    if need_depth:
        from .point_depth_head import vit_grids_by_row
        vit_layers = heads.camera.point_depth.settings['vit_layers']
        if set(vit_captured) != set(vit_layers):
            raise ValueError('The point-depth head did not capture every configured ViT block')
        if 'image_grid_thw' in batch or 'pixel_values' in batch:
            raise ValueError('The point-depth head reads video rows only')
        grids = visual_grids(output, batch, unwrapped.config.video_token_id, merge)
        per_layer = [vit_grids_by_row(vit_captured[k], batch['video_grid_thw'], merge) for k in vit_layers]
        vit = [[layer[row] for layer in per_layer] for row in range(len(grids))]
    return layer_states, grids, vit


def camera_hooks(unwrapped, heads, batch, captured, vit_captured):
    """Carrier-embedding, decoder-layer and ViT-block hooks of the camera heads."""
    handles = Handles(camera_inputs(unwrapped, heads, batch))
    if heads.has_camera:
        from .camera_head import layer_hooks
        for handle in layer_hooks(unwrapped, heads.camera, heads.camera_final_layer, captured):
            handles.add(handle)
        if heads.camera.point_depth is not None:
            from .point_depth_head import vit_layer_hooks
            for handle in vit_layer_hooks(unwrapped, heads.camera.point_depth.settings['vit_layers'], vit_captured):
                handles.add(handle)
    return handles


def capture(model, batch):
    """Capture the final normalized states without retaining every decoder layer."""
    unwrapped = unwrap(model)
    heads = getattr(unwrapped, 'auxiliary_heads', None)
    if heads is None:
        if any(k.startswith('aux_') for k in batch):
            raise ValueError('Auxiliary targets supplied without heads')
        return None, []
    if not any(k.startswith('aux_') for k in batch):
        raise ValueError('Enabled heads require auxiliary targets for every training row')
    norm = final_norm(unwrapped)
    result = []

    def hook(module, args, output):
        merge = unwrapped.config.vision_config.spatial_merge_size
        features = video_features(output, batch, unwrapped.config.video_token_id, merge, tokens=heads.needs_tokens,
                                  any_groups=not heads.uses_group_features,
                                  max_groups=heads.camera.settings.get('max_groups', 16) if heads.has_camera else 16)
        tokens = token_mask = None
        if heads.needs_tokens:
            features, tokens, token_mask = features
        layer_states = grids = vit = None
        if heads.has_camera:
            need_depth = (heads.camera.point_depth is not None and 'aux_point_depth_mask' in batch
                          and bool(batch['aux_point_depth_mask'].any()))
            layer_states, grids, vit = camera_head_inputs(heads, unwrapped, batch, output, captured, vit_captured, need_depth)
        result.append(heads(features, batch, hidden=output, tokens=tokens, token_mask=token_mask,
                            layer_states=layer_states, visual_grids=grids, vit_grids=vit)[0])
    captured = {}
    vit_captured = {}
    handles = camera_hooks(unwrapped, heads, batch, captured, vit_captured)
    handles.add(norm.register_forward_hook(hook))
    return handles, result


def capture_camera_states(model, batch, forward_context=None):
    """One no-grad eval forward of a single row with camera carriers; returns what the camera heads read.

    Returns {'carrier_states': [16, H] (the configured layer or mix), 'visual_grid': [16, Hm, Wm, H] or None,
    'vit_grids': three [16, 2Hm, 2Wm, D_vit] or None}. Raises unless the batch is one row with all 16 carriers."""
    from contextlib import nullcontext

    unwrapped = unwrap(model)
    heads = getattr(unwrapped, 'auxiliary_heads', None)
    if heads is None or not heads.has_camera:
        raise ValueError('The model has no camera heads attached')
    positions = batch.get('aux_camera_positions')
    if positions is None or tuple(positions.shape) != (1, 16) or bool((positions < 0).any()):
        raise ValueError('Head sessions need one row with all 16 camera carriers (camera_targets.insert_carriers)')
    if batch['input_ids'].shape[0] != 1:
        raise ValueError('Head sessions read one row at a time')
    need_depth = heads.camera.point_depth is not None
    norm = final_norm(unwrapped)
    captured, vit_captured, out = {}, {}, {}

    def hook(module, args, output):
        layer_states, grids, vit = camera_head_inputs(heads, unwrapped, batch, output, captured, vit_captured, need_depth)
        out['carrier_states'] = heads.camera.carrier_states(output, positions, layer_states)[0].float()
        out['visual_grid'] = grids[0].float() if grids is not None else None
        out['vit_grids'] = [grid.float() for grid in vit[0]] if vit is not None else None
        for key in ('aux_g3t_cam_tokens', 'aux_g3t_pose_9d', 'aux_g3t_gravity_up', 'aux_g3t_step_scale'):
            if key in batch:
                out[key] = batch[key]
    handles = camera_hooks(unwrapped, heads, batch, captured, vit_captured)
    handles.add(norm.register_forward_hook(hook))
    was_training = model.training
    model.eval()
    try:
        with torch.no_grad(), (forward_context if forward_context is not None else nullcontext()):
            model(**{key: value for key, value in batch.items() if key != 'labels' and not key.startswith('aux_')},
                  logits_to_keep=1, use_cache=False, output_hidden_states=False, return_dict=True)
    finally:
        handles.remove()
        model.train(was_training)
    if 'carrier_states' not in out:
        raise ValueError('The final language norm did not run')
    return out


class Handles:
    """Several hook handles removed together."""

    def __init__(self, *handles):
        self.handles = [handle for handle in handles if handle is not None]

    def add(self, handle):
        if handle is not None:
            self.handles.append(handle)

    def remove(self):
        for handle in self.handles:
            handle.remove()
        self.handles = []


def camera_inputs(unwrapped, heads, batch):
    """Training-only: carrier embeddings become the learned camera tokens. None when no camera head."""
    if not getattr(heads, 'has_camera', False):
        if 'aux_camera_positions' in batch and bool((batch['aux_camera_positions'] >= 0).any()):
            raise ValueError('Camera tokens were inserted but no camera head is attached')
        return None
    if 'aux_camera_positions' not in batch:
        raise ValueError('The camera head requires camera targets for every training row')
    from .camera_head import embedding_hook
    return unwrapped.get_input_embeddings().register_forward_hook(embedding_hook(heads.camera, batch, heads.camera_carrier))


def reason_predict(model, batch, forward_context=None):
    """One no-grad forward in eval mode; returns formatted head values per row."""
    from contextlib import nullcontext

    # FSDP forwards missing attributes to its wrapped module, so heads and config resolve there too.
    unwrapped = unwrap(model)
    heads, settings = unwrapped.auxiliary_heads, unwrapped.config
    norm = final_norm(unwrapped)
    texts = []

    def hook(module, args, output):
        features = video_features(output, batch, settings.video_token_id, settings.vision_config.spatial_merge_size)
        texts.append(heads.reason_texts(output, features.float().mean(dim=(2, 3)), batch))
    handle = Handles(norm.register_forward_hook(hook), camera_inputs(unwrapped, heads, batch))
    was_training = model.training
    model.eval()
    try:
        with torch.no_grad(), (forward_context if forward_context is not None else nullcontext()):
            model(**{key: value for key, value in batch.items() if key != 'labels' and not key.startswith('aux_')},
                  logits_to_keep=1, use_cache=False, output_hidden_states=False, return_dict=True)
    finally:
        handle.remove()
        model.train(was_training)
    if len(texts) != 1:
        raise ValueError('Query-token prediction must run the final norm exactly once')
    return texts[0]


def mix_microbatch(model, heads, batch, weights, key, pad_token_id, forward_context=None, collective=False):
    """Prediction mixing for one micro-batch. With collective=True (the trainer's
    setting) the prediction forward runs on every rank and micro-batch, selected rows
    or not, so FSDP collectives match and every rank's step costs the same."""
    rows = reason.choose_rows(batch['aux_reason_pos'], weights, heads.settings['reason_mix_prob'], key)
    if not rows and not collective:
        return batch, {'rows': 0, 'queries': 0}
    texts = reason_predict(model, batch, forward_context)
    return reason.apply_mixing(batch, rows, texts, heads.reason_table, pad_token_id)
