"""Identity-bound pose-only recipe and dense A1 row selection."""
import copy
import math

import numpy as np

from .carrier_c1 import RECIPE


def capped_steps(timing, resume_every_seconds=1800, *, start_step=0, elapsed_seconds=None):
    """Count updates that fit this allocation, without changing the LR horizon.

    Reserve 900 seconds beyond measured startup, updates, periodic/final saves
    and the milestones crossed from the absolute resume step. A budget stop
    saves an exact checkpoint; m100/m200/m400/m800 export inference weights.
    """
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
        exports = sum(start_step < m <= end for m in RECIPE['milestones'])
        # Include exports in the elapsed interval, but exclude time spent saving
        # resume states. Reserve a final save even before the first interval.
        saves = max(1, math.ceil((n*timing['p95_step_seconds'] +
                                  exports*timing['export_seconds']) / resume_every_seconds))
        return (n * timing['p95_step_seconds'] + saves*timing['checkpoint_seconds']
                + exports*timing['export_seconds'])
    low, high = 0, max(0, min(RECIPE['steps']-start_step, int(available / timing['p95_step_seconds'])))
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
        if (not isinstance(mix, list) or set(mix) != {'pose', 'vqa', 'pointing', 'routing'}
                or world not in (8, 16, 32)):
            raise ValueError('Final mode needs a mix over pose/vqa/pointing/routing and world_size 8, 16 or 32')
        steps, milestones = cfg.get('steps', result['steps']), cfg.get('milestones', result['milestones'])
        if (type(steps) is not int or steps < 1 or not isinstance(milestones, list)
                or milestones != sorted(set(milestones)) or any(type(m) is not int or not 0 < m <= steps for m in milestones)):
            raise ValueError('Final mode needs integer steps and increasing milestones within them')
        weights = cfg.get('weights', {})
        result['weights']['routing'] = 1.
        if set(weights) - set(result['weights']) or any(type(v) not in (int, float) or v < 0 for v in weights.values()):
            raise ValueError('Final mode weights must name known nonnegative components')
        result.update(mix=list(mix), world_size=world, global_batch=world*len(mix), steps=steps,
                      milestones=milestones, scheduled_sampling=validate_schedule(cfg.get('scheduled_sampling')))
        result['weights'].update(weights)
        if not cfg.get('depth_enabled', True):
            result['weights'].update(depth=0., depth_fov=0.)
        return result
    if cfg.get('training_mode') != 'pose_only':
        raise ValueError('Unknown training_mode')
    capped_steps(cfg['schedule'], interval)  # Validate the measured allocation budget separately.
    result.update(mix=['pose']*4)
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
