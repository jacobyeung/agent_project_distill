"""Pose-path camera projector and optional training-only patch alignment."""
import math

import torch
from torch import nn
from torch.nn import functional as F

from .camera_head import gather_positions


def validate(settings):
    if (not isinstance(settings, dict) or not {'cam', 'patch'} <= set(settings)
            or set(settings) - {'cam', 'clip', 'patch', 'projector', 'loss', 'targets', 'schedule'}):
        raise ValueError('Alignment requires cam and patch settings')
    cam = settings['cam']
    if (not isinstance(cam, dict) or set(cam) != {'layer', 'weight'}
            or cam['layer'] not in ('final', 'middle') or type(cam['weight']) not in (int, float)
            or not math.isfinite(cam['weight']) or cam['weight'] < 0):
        raise ValueError('Camera alignment requires final or middle and a nonnegative weight')
    patch = settings['patch']
    if patch is not None:
        if (not isinstance(patch, dict) or set(patch) != {'weight'}
                or type(patch['weight']) not in (int, float)
                or not math.isfinite(patch['weight']) or patch['weight'] <= 0):
            raise ValueError('Patch alignment requires a positive weight')
    clip = settings.get('clip')
    if clip is not None:
        if (not isinstance(clip, dict) or set(clip) != {'weight'}
                or type(clip['weight']) not in (int, float)
                or not math.isfinite(clip['weight']) or clip['weight'] < 0):
            raise ValueError('Clip alignment requires a nonnegative weight')
        if settings.get('schedule', {'kind': 'constant'}) != {'kind': 'constant'}:
            raise ValueError('Clip alignment requires a constant schedule')
    projector = _projector_spec(settings)
    if (not isinstance(projector, dict) or set(projector) != {'depth', 'width'}
            or type(projector['depth']) is not int or not 1 <= projector['depth'] <= 8
            or not (projector['width'] in ('hidden', '2H') or type(projector['width']) is int
                    and 1 <= projector['width'] <= 16384)):
        raise ValueError('Projector requires depth 1..8 and a positive width, hidden or 2H')
    if settings.get('loss', 'cosine') not in ('cosine', 'centered_cosine'):
        raise ValueError('Alignment loss must be cosine or centered_cosine')
    selected = target_set(settings)
    if (not isinstance(selected, list) or any(v not in ('cam', 'patch') for v in selected)
            or len(selected) != len(set(selected)) or 'patch' in selected and patch is None):
        raise ValueError('Target set must select cam and/or a configured patch target')
    if clip is not None and (settings.get('loss') != 'centered_cosine' or 'cam' not in selected):
        raise ValueError('Clip alignment requires centered_cosine and camera targets')
    schedule = settings.get('schedule', {'kind': 'constant'})
    if not isinstance(schedule, dict):
        raise ValueError('Alignment schedule requires a kind')
    kind = schedule.get('kind')
    if kind == 'constant':
        if set(schedule) != {'kind'}:
            raise ValueError('Constant alignment schedule takes no ramp settings')
    elif kind in ('linear', 'cosine'):
        if (set(schedule) != {'kind', 'start_step', 'end_step', 'start_factor', 'end_factor'}
                or any(type(schedule[k]) is not int for k in ('start_step', 'end_step'))
                or not 0 <= schedule['start_step'] < schedule['end_step']
                or any(type(schedule[k]) not in (int, float) or not math.isfinite(schedule[k])
                       or schedule[k] < 0 for k in ('start_factor', 'end_factor'))):
            raise ValueError('Alignment ramp requires ordered steps and finite nonnegative factors')
    else:
        raise ValueError('Unknown alignment schedule')
    return settings


def target_set(settings):
    return settings.get('targets', ['cam'] + (['patch'] if settings['patch'] is not None else []))


def patch_enabled(settings):
    return 'patch' in target_set(settings)


def _projector_spec(settings):
    # The new clip setting selects the merged default; old receipts retain H.
    return settings.get('projector', {'depth': 2,
        'width': '2H' if settings.get('clip') is not None else 'hidden'})


def schedule_factor(settings, step):
    schedule = settings.get('schedule', {'kind': 'constant'})
    if schedule['kind'] == 'constant':
        return 1.
    fraction = min(1., max(0., (step-schedule['start_step']) /
                          (schedule['end_step']-schedule['start_step'])))
    if schedule['kind'] == 'cosine':
        fraction = (1-math.cos(math.pi*fraction))/2
    return schedule['start_factor'] + fraction*(schedule['end_factor']-schedule['start_factor'])


def set_step(model, step):
    if hasattr(model, 'align_settings'):
        model.align_factor = schedule_factor(model.align_settings, step)


def attach(model, settings, training=True):
    """Attach FP32 projectors before creating optimizer groups or FSDP."""
    import copy
    validate(settings)
    hidden = model.config.text_config.hidden_size
    def projector():
        spec = _projector_spec(settings)
        width = {'hidden': hidden, '2H': 2*hidden}.get(spec['width'], spec['width'])
        dimensions = [hidden] + [width]*(spec['depth']-1) + [2048]
        layers = []
        for i, (before, after) in enumerate(zip(dimensions, dimensions[1:])):
            if i:
                layers.append(nn.GELU())
            layers.append(nn.Linear(before, after))
        network = nn.Sequential(*layers).float()
        # Pre-norm states can be much smaller than final states. Start biases
        # at zero so a constant offset cannot bury their initial frame signal.
        for layer in network:
            if isinstance(layer, nn.Linear):
                nn.init.zeros_(layer.bias)
        return network
    model.auxiliary_heads.pose.projector = projector()
    model.auxiliary_heads.pose.projector_fp32 = True
    model.pose_source_layer = settings['cam']['layer']
    if training and patch_enabled(settings):
        model.auxiliary_heads.align_patch = projector()
    if training:
        model.align_settings = copy.deepcopy(settings)
    return model


def training_only_modules(model):
    return ['align_patch'] if hasattr(model.auxiliary_heads, 'align_patch') else []


def inference_heads(state, modules):
    """Remove only declared, known training modules; keep strict head loading."""
    if (not isinstance(modules, list) or len(set(modules)) != len(modules)
            or any(name != 'align_patch' for name in modules)):
        raise ValueError('Unknown training_only_modules')
    actual = {name for name in ('align_patch',) if any(k.startswith(name + '.') for k in state)}
    if actual != set(modules):
        raise ValueError('Training module declaration differs from head tensors')
    return {k: v for k, v in state.items() if not any(k.startswith(name + '.') for name in modules)}


def cosine_loss(prediction, teacher, mask, loss='cosine'):
    if prediction.shape != teacher.shape or prediction.shape[-1] != 2048 or mask.shape != prediction.shape[:-1]:
        raise ValueError('Alignment target shape mismatch')
    if not mask.any() or not torch.isfinite(teacher[mask]).all() or (teacher[mask].norm(dim=-1) == 0).any():
        raise ValueError('Alignment requires finite nonzero teacher vectors and valid frames')
    if loss == 'centered_cosine':
        # Feature centering matches the mean removal in the head's token norm;
        # it is per vector, never a mean learned from held-out examples.
        prediction = prediction.float() - prediction.float().mean(-1, keepdim=True)
        teacher = teacher.detach().float() - teacher.detach().float().mean(-1, keepdim=True)
        if (teacher[mask].norm(dim=-1) == 0).any():
            raise ValueError('Centered teacher vectors must be nonzero')
    elif loss != 'cosine':
        raise ValueError('Unknown alignment loss')
    cosine = F.cosine_similarity(prediction.float(), teacher.detach().float(), dim=-1)
    # Each row contributes equally even if a future batch contains masked slots.
    counts = mask.sum(-1).clamp_min(1)
    mean = ((cosine * mask).sum(-1) / counts).mean()
    return 1 - mean, mean


def clip_ccc_loss(prediction, teacher, mask):
    """Score CAMs 2-32 after channel normalization and clip-mean removal.

    Each clip contributes equally. The reference CAM and masked slots never
    enter normalization, means, energies or diagnostics. Teacher tokens stay
    detached; the prediction remains the raw tensor consumed by the pose head.
    """
    if (prediction.ndim != 3 or prediction.shape != teacher.shape
            or prediction.shape[-1] != 2048 or mask.shape != prediction.shape[:-1]
            or mask.dtype != torch.bool):
        raise ValueError('Clip alignment target shape mismatch')
    valid = mask.clone()
    valid[:, :1] = False
    valid[:, 32:] = False
    if not valid.any(-1).all():
        raise ValueError('Clip alignment requires valid CAMs after the reference')
    # Mask before arithmetic: even nonfinite padding cannot pollute a clip.
    keep = valid[..., None]
    p = torch.where(keep, prediction.float(), 0.)
    q = torch.where(keep, teacher.detach().float(), 0.)
    if not torch.isfinite(q[valid]).all():
        raise ValueError('Clip alignment requires finite teacher vectors')
    p = p - p.mean(-1, keepdim=True)
    q = q - q.mean(-1, keepdim=True)
    if (q[valid].norm(dim=-1) == 0).any():
        raise ValueError('Centered teacher vectors must be nonzero')
    p, q = F.normalize(p, dim=-1, eps=1e-8), F.normalize(q, dim=-1, eps=1e-8)
    count = valid.sum(-1, keepdim=True)
    p_mean, q_mean = p.sum(1) / count, q.sum(1) / count
    dp = torch.where(keep, p - p_mean[:, None], 0.)
    dq = torch.where(keep, q - q_mean[:, None], 0.)
    p_energy, q_energy = dp.square().sum((1, 2)), dq.square().sum((1, 2))
    ccc = 2*(dp*dq).sum((1, 2)) / (p_energy + q_energy + 1e-6)
    return (1 - ccc).mean(), dict(
        align_ccc=ccc.mean(),
        # Stabilize this diagnostic only when teacher motion vanishes.
        align_spread_ratio=(p_energy / q_energy.clamp_min(1e-6)).sqrt().mean(),
        align_teacher_shared_share=q_mean.square().sum(-1).mean(),
        align_near_static_clips=(q_energy < 1e-4).sum().float())


def teacher_rows(targets, rows):
    """Rows with a cached teacher target; absent key means every row is covered."""
    covered = targets.get('aux_g3t_valid')
    if covered is None:
        return None
    covered = torch.as_tensor(covered, dtype=torch.bool).reshape(-1)
    if covered.shape != (rows,):
        raise ValueError('aux_g3t_valid needs one flag per row')
    return covered


def uncovered_targets(rows=1, slots=32):
    """Teacher placeholders for rows outside the store: zero weight, never a stale token."""
    return {'aux_g3t_cam': torch.zeros(rows, slots, 2048), 'aux_g3t_valid': torch.zeros(rows, dtype=torch.bool)}


def alignment_loss(model, final, middle, batch, targets, projected=None):
    settings = model.align_settings
    covered = teacher_rows(targets, batch['aux_camera_positions'].shape[0])
    if covered is not None:
        targets = {k: v for k, v in targets.items() if k != 'aux_g3t_valid'}
    if covered is not None and covered.all():
        total, parts = alignment_loss(model, final, middle, batch, targets, projected)
        return total, {**parts, 'align_covered_rows': total.detach() * 0. + covered.sum()}
    if covered is not None:
        if patch_enabled(settings):
            raise ValueError('Patch alignment requires cached targets for every row')
        source = final if settings['cam']['layer'] == 'final' else middle
        zero = (source.sum() if projected is None else projected.sum()) * 0.
        if not covered.any():
            # Pose loss is untouched; this row adds no teacher term or gradient.
            parts = dict(align_cam=zero, align_cos=zero, align_patch=zero)
            if settings.get('clip') is not None:
                parts.update(align_clip=zero, align_ccc=zero, align_spread_ratio=zero,
                             align_teacher_shared_share=zero, align_near_static_clips=zero)
            return zero, {**parts, 'align_covered_rows': zero}
        # Average the teacher terms over covered rows only.
        keep = lambda value: value[covered]
        batch = {**batch, 'aux_camera_positions': keep(batch['aux_camera_positions'])}
        targets = {**targets, 'aux_camera_mask': keep(targets['aux_camera_mask']),
                   'aux_g3t_cam': keep(targets['aux_g3t_cam'])}
        final = keep(final) if final is not None else None
        middle = keep(middle) if middle is not None else None
        projected = keep(projected) if projected is not None else None
        total, parts = alignment_loss(model, final, middle, batch, targets, projected)
        return total, {**parts, 'align_covered_rows': zero + covered.sum()}
    source = final if settings['cam']['layer'] == 'final' else middle
    positions = batch['aux_camera_positions']
    valid = (positions >= 0) & targets['aux_camera_mask']
    # Replicated master heads always compute in FP32, including under autocast.
    with torch.autocast(device_type=source.device.type, enabled=False):
        states = gather_positions(source.float(), positions)
        prediction = model.auxiliary_heads.pose.projector(states) if projected is None else projected
        cam = cosine = prediction.sum()*0.
        loss = settings.get('loss', 'cosine')
        if 'cam' in target_set(settings):
            teacher = targets['aux_g3t_cam']
            if settings.get('clip') is not None:
                # Retain the old formula byte for byte outside the new mode.
                cam, cosine = cosine_loss(torch.where(valid[..., None], prediction, 0.),
                    torch.where(valid[..., None], teacher, 0.), valid, loss)
            else:
                cam, cosine = cosine_loss(prediction, teacher, valid, loss)
        clip = diagnostics = None
        if settings.get('clip') is not None:
            clip, diagnostics = clip_ccc_loss(prediction, targets['aux_g3t_cam'], valid)
        patch = cam * 0.
        if patch_enabled(settings):
            visual = batch['mm_token_type_ids'] == 2
            if middle.shape[0] != 1 or 'aux_g3t_patch' not in targets:
                raise ValueError('Patch alignment requires one row and its cached target')
            prediction = model.auxiliary_heads.align_patch(final[visual].float())
            teacher = targets['aux_g3t_patch']
            patch, _ = cosine_loss(prediction[None], teacher[None],
                                   torch.ones((1, len(prediction)), device=source.device, dtype=torch.bool), loss)
    total = settings['cam']['weight'] * cam
    if clip is not None:
        total = total + settings['clip']['weight'] * clip
    if patch_enabled(settings):
        total = total + settings['patch']['weight'] * patch
    if 'schedule' in settings:
        total = total * getattr(model, 'align_factor', schedule_factor(settings, 0))
    components = dict(align_cam=cam, align_cos=cosine, align_patch=patch)
    if clip is not None:
        components.update(align_clip=clip, **diagnostics)
    return total, components
