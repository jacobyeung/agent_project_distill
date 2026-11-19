"""Permanent native LM-carrier learning guard: 32 rows, 200 optimizer steps."""
import json
import math
import os
from pathlib import Path
import time
import unittest

import torch

from tests.test_carrier_c1 import fixture
from student_pilot.carrier_c1 import parameter_groups
from student_pilot.carrier_c1_data import C1_A, PLACEMENTS


def overfit(placement=C1_A):
    torch.manual_seed(31)
    model, single, target = fixture(depth_labels=False, placement=placement,
                                     training_mode='pose_only', depth_enabled=False)
    # Thirty-two distinct image rows encode absolute yaw, never relative pose,
    # row identity or GT. Sixteen cyclic origins require comparing to frame 1.
    generator=torch.Generator().manual_seed(29)
    projection=torch.randn(4,24,generator=generator)
    pixels,quaternions=[],[]
    for offset in (0.,.12):
        yaw=torch.linspace(-1.4,1.4,16)+offset
        for origin in range(16):
            angles=yaw[torch.roll(torch.arange(16),-origin)]
            signal=torch.stack((angles.sin(),angles.cos(),(2*angles).sin(),(2*angles).cos()),-1)
            pixels.append((signal@projection).repeat_interleave(4,dim=0))
            relative=(angles[0]-angles).repeat_interleave(2)
            q=torch.zeros(32,4);q[:,1]=torch.sin(relative/2);q[:,3]=torch.cos(relative/2)
            quaternions.append(q)
    batch={k:torch.cat([v]*32,dim=0) for k,v in single.items()}
    batch['pixel_values_videos']=torch.cat(pixels)
    targets={k:torch.cat([v]*32,dim=0) for k,v in target.items()}
    targets['aux_camera_target'][...,3:7]=torch.stack(quaternions)
    # This guard tests the carrier/pose path only; its native update/gradient
    # tests separately cover the private depth branch and production LR groups.
    targets['aux_gravity_mask'].fill_(False)
    targets['aux_camera_scale'].fill_(0.)
    optimizer=torch.optim.AdamW(parameter_groups(model),weight_decay=.01)
    for group in optimizer.param_groups:
        group['lr']=1e-3
    model.model.language_model.gradient_checkpointing_disable()
    def measure():
        model.eval()
        with torch.no_grad():
            hidden=model.hidden(batch).float()
            head=model.auxiliary_heads.pose
            states=head.carrier_states(hidden,batch['aux_camera_positions'])
            pred=head.predict(states)[-1]
            q=torch.nn.functional.normalize(pred[...,3:7],dim=-1)
            error=2*torch.acos((q*targets['aux_camera_target'][...,3:7]).sum(-1).abs().clamp(max=1))*180/math.pi
        return float(error.mean()),float(error.mean(-1).max())
    initial,_=measure(); started=time.perf_counter(); timings=[]
    for step in range(200):
        tick=time.perf_counter();model.train();optimizer.zero_grad(set_to_none=True)
        result=model(batch,targets)
        result['loss'].backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
        optimizer.step();timings.append(time.perf_counter()-tick)
    final,worst=measure()
    report=dict(rows=32,steps=200,frames_per_row=32,native_lm=True,source='synthetic_absolute_yaw_pixels',
                carrier_placement=placement, training_mode='pose_only',
                guard_lr=1e-3,initial_mean_rotation_deg=initial,final_mean_rotation_deg=final,
                worst_row_mean_rotation_deg=worst,seconds=time.perf_counter()-started,
                step_seconds=timings,gpu_fit_measured=False)
    output=os.environ.get('C1_OVERFIT_REPORT')
    if output:
        path=Path(output)
        output=path.with_name(path.stem+'_'+chr(ord('a')+PLACEMENTS.index(placement))+path.suffix)
        with Path(output).open('x') as handle:
            json.dump(report,handle)
    print(json.dumps({k:v for k,v in report.items() if k!='step_seconds'}))
    return report


class NativeCarrierOverfitTests(unittest.TestCase):
    def test_32_rows_200_steps_rotation_below_30_degrees(self):
        for placement in PLACEMENTS:
            with self.subTest(placement=placement):
                report=overfit(placement)
                self.assertGreater(report['initial_mean_rotation_deg'],30.)
                self.assertLess(report['final_mean_rotation_deg'],30.)
        # The guard uses pooled mean rotation, matching its stated threshold;
        # retain the worst row in the report so it cannot hide a difficult row.


if __name__=='__main__':
    unittest.main()
