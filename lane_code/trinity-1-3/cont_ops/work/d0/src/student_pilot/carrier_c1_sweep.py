"""Identity-bound pose-only recipe and dense A1 row selection."""
import copy
import math

import numpy as np

from .carrier_c1 import RECIPE


def capped_steps(timing, resume_every_seconds=1800, *, start_step=0, elapsed_seconds=None,
                 total_steps=None, milestones=None):
    """Count updates that fit this allocation, without changing the LR horizon.

    Reserve 900 seconds beyond measured startup, updates, periodic/final saves
    and the milestones crossed from the absolute resume step. A budget stop
    saves an exact checkpoint; m100/m200/m400/m800 export inference weights.
    `total_steps`/`milestones` default to the fixed recipe's (a warm-started pose-only
    run supplies its own horizon and milestones).
    """
    total_steps = RECIPE['steps'] if total_steps is None else total_steps
    milestones = RECIPE['milestones'] if milestones is None else milestones
    required = ('startup_seconds', 'p95_step_seconds', 'checkpoint_seconds', 'export_seconds')
    if (type(resume_every_seconds) not in (int, float) or not math.isfinite(resume_every_seconds)
            or resume_every_seconds <= 0):
        raise ValueError('resume_every_seconds must be finite and positive')
    if any(type(timing.get(k)) not in (int, float) or not math.isfinite(timing[k]) or timing[k] < 0
           for k in required) or timing['p95_step_seconds'] <= 0:
        raise ValueError('Schedule needs finite measured startup/update/checkpoint/export times')
    elapsed = timing['startup_seconds'] if elapsed_seconds is None else max(timing['startup_seconds'], elapsed_seconds)
    available = RECIPE['wall_seconds'] - RECIPE['stop_before_seconds'] - elapsed
    def cost(n):
        end = start_step + n
        exports = sum(start_step < m <= end for m in milestones)
        # Include exports in the elapsed interval, but exclude time spent saving
        # resume states. Reserve a final save even before the first interval.
        saves = max(1, math.ceil((n*timing['p95_step_seconds'] +
                                  exports*timing['export_seconds']) / resume_every_seconds))
        return (n * timing['p95_step_seconds'] + saves*timing['checkpoint_seconds']
                + exports*timing['export_seconds'])
    low, high = 0, max(0, min(total_steps-start_step, int(available / timing['p95_step_seconds'])))
    while low < high:
        mid = (low + high + 1)//2
        if cost(mid) <= available:
            low = mid
        else:
            high = mid-1
    if low < 1 and elapsed_seconds is None:
        raise ValueError('No optimizer step fits the four-hour cap')
    return low


def recipe_for(cfg):
    result = copy.deepcopy(RECIPE)
    interval = cfg.get('recipe', {}).get('resume_every_seconds', result['resume_every_seconds'])
    if type(interval) not in (int, float) or not math.isfinite(interval) or interval <= 0:
        raise ValueError('resume_every_seconds must be finite and positive')
    result['resume_every_seconds'] = interval
    if cfg.get('training_mode', 'mixed') == 'mixed':
        return result
    if cfg.get('training_mode') == 'final':
        from .carrier_c1_routing import validate_schedule
        mix, world = cfg.get('mix'), cfg.get('world_size')
        gf1 = (cfg.get('geometry_online') or {}).get('gf1')
        worlds = (1, 4) if gf1 else (4, 8, 16, 32)
        if gf1 and world != 4:
            raise ValueError('GF1 stages use world 4')
        streams = {'pose', 'vqa', 'pointing', 'routing'} | ({'mdg'} if 'mdg' in cfg else set())
        if (not isinstance(mix, list) or set(mix) != streams
                or type(world) is not int or world not in worlds):
            raise ValueError('Final mode needs a mix over pose/vqa/pointing/routing and world_size 4, 8, 16 or 32')
        # a298304 admits world 4. Expand each stream consecutively, as the
        # pose-only ca00f29 path does, to retain the reference world's row order.
        reference = cfg.get('reference_world_size', 32 if cfg.get('geometry_online') else world)
        if type(reference) is not int or reference not in (4, 8, 16, 32) or reference % world:
            raise ValueError('reference_world_size must be a supported multiple of world_size')
        if cfg.get('geometry_online'):
            from .g3t_online import normalize, validate_arm
            gx = normalize(cfg['geometry_online'])
            validate_arm(gx, 'final', cfg.get('frame_layout'), cfg.get('depth_enabled', True))
            if reference != 32 and not gf1:
                raise ValueError('Final GX must match CP1 reference_world_size 32')
        steps, milestones = cfg.get('steps', result['steps']), cfg.get('milestones', result['milestones'])
        if (type(steps) is not int or steps < 1 or not isinstance(milestones, list)
                or milestones != sorted(set(milestones)) or any(type(m) is not int or not 0 < m <= steps for m in milestones)):
            raise ValueError('Final mode needs integer steps and increasing milestones within them')
        weights = cfg.get('weights', {})
        result['weights']['routing'] = 1.
        if set(weights) - set(result['weights']) or any(type(v) not in (int, float) or v < 0 for v in weights.values()):
            raise ValueError('Final mode weights must name known nonnegative components')
        result.update(mix=[s for s in mix for _ in range(reference//world)],
                      world_size=world, global_batch=reference*len(mix), steps=steps,
                      milestones=milestones, scheduled_sampling=validate_schedule(cfg.get('scheduled_sampling')))
        result['weights'].update(weights)
        if reference != world:
            result['reference_world_size'] = reference
        if not cfg.get('depth_enabled', True):
            result['weights'].update(depth=0., depth_fov=0.)
        given = cfg.get('recipe', {})
        warmup = given.get('warmup_ratio', result['warmup_ratio'])
        wall = given.get('wall_seconds', result['wall_seconds'])
        reserve = given.get('stop_before_seconds', result['stop_before_seconds'])
        if (type(warmup) not in (int, float) or not math.isfinite(warmup) or not 0 <= warmup <= .5
                or type(wall) not in (int, float) or not math.isfinite(wall) or not 3600 <= wall <= 86400
                or type(reserve) not in (int, float) or not math.isfinite(reserve) or not 300 <= reserve <= wall/4):
            raise ValueError('Final mode warmup_ratio, wall_seconds or stop_before_seconds out of range')
        result.update(warmup_ratio=warmup, wall_seconds=wall, stop_before_seconds=reserve)
        if 'export_at_stop' in given:
            # Export an inference artifact with heads at the leg's last trained step.
            if type(given['export_at_stop']) is not bool:
                raise ValueError('Final mode export_at_stop must be boolean')
            result['export_at_stop'] = given['export_at_stop']
        from .e2e_recipe import apply
        return apply(cfg, result)
    if cfg.get('training_mode') != 'pose_only':
        raise ValueError('Unknown training_mode')
    if 'steps' in cfg or 'milestones' in cfg:
        # A warm-started pose-only run (init_artifact) sets its own LR horizon and milestones;
        # a GX run may also export its step-0 state (milestone 0).
        steps, milestones = cfg.get('steps'), cfg.get('milestones')
        low = 0 if cfg.get('geometry_online') is not None else 1
        if (type(steps) is not int or not 1 <= steps <= result['steps'] or not isinstance(milestones, list)
                or milestones != sorted(set(milestones)) or any(type(m) is not int or not low <= m <= steps for m in milestones)):
            raise ValueError('Pose-only steps/milestones need integer steps <= 800 and increasing milestones within them')
        result.update(steps=steps, milestones=milestones)
    if cfg.get('geometry_online') is not None:
        from .g3t_online import normalize
        gx = normalize(cfg['geometry_online'])
        if 'steps' not in cfg or 'milestones' not in cfg:
            raise ValueError('GX needs its own steps and milestones')
        if gx['finetune']:
            result['geometry_learning_rate'] = result['learning_rate'] * gx['finetune']['lr_scale']
    # Validate the measured allocation budget separately.
    capped_steps(cfg['schedule'], interval, total_steps=result['steps'], milestones=result['milestones'])
    world = cfg.get('world_size', 8)
    if world != 8 and (cfg.get('geometry_online') is None or world != 4):
        raise ValueError('Pose-only world_size is 8 (a GX arm may run at 4 with eight microsteps)')
    # The same 32 rows per update: eight ranks x four microsteps, or four ranks x eight.
    result.update(mix=['pose']*(32//world), world_size=world, global_batch=32)
    result['weights'].update(vqa=0., pointing=0.)
    if not cfg.get('depth_enabled', False):
        result['weights'].update(depth=0., depth_fov=0.)
    return result


def dense_pose_row(row, target):
    """Select A1's all_frames32 additions; never admit A0's even-only targets."""
    sample = row.get('pose_sample', {})
    mask = np.asarray(target.get('camera_mask', []), dtype=bool)
    camera = np.asarray(target.get('camera', []), dtype=float)
    return (row.get('category') == 'camera_pose_only'
            and sample.get('recording', {}).get('sampling', {}).get('variant') == 'all_frames32'
            and len(row.get('student_input', {}).get('frames', [])) == 32
            and mask.shape == (32,) and bool(mask.all())
            and camera.shape == (32, 9) and bool(np.isfinite(camera).all()))
