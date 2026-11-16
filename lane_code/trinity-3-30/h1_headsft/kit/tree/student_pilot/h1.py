"""Opt-in faithful camera SFT and routing camera supervision."""
import copy
import re
from collections import Counter

import numpy as np
import torch

from . import carrier_c1_routing as routing
from .camera_targets import trajectory_scale
from .h1_faithful import camera, canonical_row, printed_camera, faithful, own_values
from generator.derivgen_v7.derivgen.materialize import materialize, MaterializeRefusal

CAMERA_TYPES = routing.CAMERA_MOTION


def validate(cfg):
    h = cfg.get('h1', {})
    if not isinstance(h, dict) or set(h) - {'faithful_own_camera_rows', 'routing_pose_targets',
                                           'camera_types', 'stop_after_step', 'metrics', 'r0_rooms'}:
        raise ValueError('Unknown H1 configuration')
    for key in ('faithful_own_camera_rows', 'routing_pose_targets', 'metrics'):
        if key in h and type(h[key]) is not bool:
            raise ValueError('h1.' + key + ' must be boolean')
    if tuple(h.get('camera_types', CAMERA_TYPES)) != CAMERA_TYPES:
        raise ValueError('H1 camera_types must be the three camera motion types in canonical order')
    stop = h.get('stop_after_step')
    if stop is not None and (type(stop) is not int or not 1 <= stop <= cfg['recipe']['steps']):
        raise ValueError('h1.stop_after_step must be within the unchanged LR horizon')
    if h.get('faithful_own_camera_rows'):
        s = cfg['scheduled_sampling']
        if s['max_own_probability'] != .5 or s['force_from_step'] != 1:
            raise ValueError('H1 S1 requires max_own_probability=0.5 and force_from_step=1')
    if h.get('r0_rooms') is not None:
        from .h1_r0 import Reserve
        Reserve(h['r0_rooms'])
    return h


def pose_targets(row, batch, settings):
    """Reuse the pose stream target contract, masking missing camera labels."""
    raw = row.get('routing', row)
    valid = camera(raw, settings) and 'gt_pose9' in raw and 'gt_up' in raw
    reason = None if valid else ('missing_gt_fields' if camera(raw, settings) else 'non_camera')
    p = np.asarray(raw['gt_pose9'], dtype=np.float32) if valid else np.tile([0,0,0,0,0,0,1,1,1], (32,1))
    up = np.asarray(raw['gt_up'], dtype=np.float32) if valid else np.array([0,-1,0], dtype=np.float32)
    if p.shape != (32,9) or up.shape != (3,) or not np.isfinite(p).all() or not np.isfinite(up).all():
        raise ValueError('H1 routing GT must be finite gt_pose9[32,9] and gt_up[3]')
    if valid and (not np.allclose(np.linalg.norm(p[:,3:7], axis=1), 1, atol=1e-4)
                  or not np.isclose(np.linalg.norm(up), 1, atol=1e-4)):
        raise ValueError('H1 routing GT quaternion and gravity must be unit vectors')
    positions = batch['aux_camera_positions']
    if positions.shape != (1,32) or (valid and not (positions >= 0).all()):
        raise ValueError('H1 pose targets require all 32 frame carriers')
    mask = np.full(32, valid)
    targets = dict(aux_camera_target=torch.tensor(p, dtype=torch.float32)[None],
                   aux_camera_mask=torch.tensor(mask)[None],
                   aux_camera_scale=torch.tensor([trajectory_scale(p, mask) if valid else 0.]),
                   aux_gravity_target=torch.tensor(up, dtype=torch.float32)[None],
                   aux_gravity_mask=torch.tensor([valid]), h1_pose=torch.tensor(True))
    return targets, dict(supervised=int(valid), missing=int(reason == 'missing_gt_fields'), reason=reason)


def summarize(shapes):
    out = {}
    for row in shapes:
        h = row.get('h1')
        if h is None:
            continue
        d = out.setdefault(h['type'], dict(own=0, gt=0, refused=0, refusal_reasons={},
                                          answer_differs=0, pose_supervised=0, pose_missing=0, segments={}))
        d[h['values']] += 1
        if h.get('refused'):
            d['refused'] += 1
            r = h['refused']; d['refusal_reasons'][r] = d['refusal_reasons'].get(r, 0) + 1
        d['answer_differs'] += int(h.get('answer_differs', False))
        pose = row.get('h1_pose', {})
        d['pose_supervised'] += pose.get('supervised', 0)
        d['pose_missing'] += pose.get('missing', 0)
        for name, (loss, n) in row.get('segments', {}).items():
            sums = d['segments'].setdefault(name, [0., 0]); sums[0] += loss; sums[1] += n
    for d in out.values():
        d['faithful_answer_differs_from_gt_rate'] = d['answer_differs']/d['own'] if d['own'] else None
        d['segment_ce'] = {k: loss/n for k, (loss,n) in d['segments'].items() if n}
    return out


STOP_RULE = 'h1_own_camera_answer_differs_gt_35pct_steps1_50'
STOP_DEFINITION = dict(direction='option changes', displacement='relative difference > 0.10',
                       rotation='wrapped absolute difference > 10 degrees', threshold=.35,
                       window=[1,50], stop_step=100)


def global_answer_counts(shapes, device, distributed=False):
    """Sum successful own camera rows across ranks once per optimizer step."""
    rows=[s['h1'] for s in shapes if s.get('h1',{}).get('type') in CAMERA_TYPES
          and s['h1'].get('values')=='own']
    count=torch.tensor([sum(bool(r.get('answer_differs')) for r in rows),len(rows)],
                       dtype=torch.int64,device=device)
    if distributed:torch.distributed.all_reduce(count)
    differs,own=map(int,count.tolist())
    return dict(answer_differs=differs,own=own,share=differs/own if own else None)


class AnswerStop:
    def __init__(self):
        self.differs=0;self.own=0;self.last_step=0
    def update(self,step,counts):
        if step!=self.last_step+1:raise ValueError('H1 stop history must cover consecutive steps')
        self.last_step=step
        if step<=50:
            self.differs+=counts['answer_differs'];self.own+=counts['own']
        share=self.differs/self.own if self.own else None
        return dict(rule=STOP_RULE,definition=STOP_DEFINITION,window_answer_differs=self.differs,
                    window_own=self.own,window_share=share,
                    triggered=step>=50 and share is not None and share>.35)
    def replay(self,output,start_step):
        import json
        from pathlib import Path
        found={}
        for path in sorted(Path(output).glob('metrics_*.jsonl')):
            with path.open() as handle:
                for line in handle:
                    record=json.loads(line);step=record['step']
                    if step>start_step:continue
                    ranks=[r for r in record['ranks'] if r is not None]
                    counts=[r.get('h1_answer_counts') for r in ranks]
                    if not counts or any(c is None or c!=counts[0] for c in counts):
                        raise ValueError('H1 resume requires consistent all-reduced answer counts')
                    if step in found and found[step]!=counts[0]:raise ValueError('Conflicting H1 stop history')
                    found[step]=counts[0]
        state=None
        for step in range(1,start_step+1):
            if step not in found:raise ValueError('Missing H1 stop history at step '+str(step))
            state=self.update(step,found[step])
        return state
