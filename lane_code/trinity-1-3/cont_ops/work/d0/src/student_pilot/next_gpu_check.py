"""Call on one existing microbatch after backward, before clipping/zero_grad.

No optimizer mutation or extra backward; one vision pass and two head passes.
The parent can copy this helper into the next job's authorized diagnostic wrapper.
"""
import math
import torch
from student_pilot.decoupled_v import features


@torch.no_grad()
def check(model, batch, targets):
    camera = model.auxiliary_heads.camera
    capture = features(model, batch, allow_short=True)
    states = capture.states
    inputs = capture.pose_inputs()
    n = states.shape[1]
    mask = targets['aux_camera_mask'][:, :n].bool()
    gt = targets['aux_camera_target'][:, :n].float()
    deltas = []
    handle = camera.head.pose_branch.register_forward_hook(lambda m,a,o: deltas.append(o))
    try:
        stages = camera.predict_all(states, **inputs)[0]
    finally:
        handle.remove()
    logits = torch.stack(deltas).cumsum(0)[...,7:9]
    pred = stages[-1]
    q = torch.nn.functional.normalize(pred[...,3:7],dim=-1)
    qt = torch.nn.functional.normalize(gt[...,3:7],dim=-1)
    angle = 2*torch.acos((q*qt).sum(-1).abs().clamp(max=1.))*180/math.pi
    mag = 2*torch.acos(q[...,3].abs().clamp(max=1.))*180/math.pi
    gt_mag = 2*torch.acos(qt[...,3].abs().clamp(max=1.))*180/math.pi
    perm = torch.roll(torch.arange(n,device=states.device),-1)
    moved_inputs = dict(inputs)
    if 'frame_queries' in inputs:
        group_perm = torch.roll(torch.arange(n//2, device=states.device), -1)
        perm = (2*group_perm[:, None]+torch.arange(2, device=states.device)).flatten()
        moved_inputs['frame_queries'] = inputs['frame_queries'][perm]
        moved_inputs['spatial_grids'] = [g[group_perm] for g in inputs['spatial_grids']]
    elif 'spatial_grids' in inputs:
        moved_inputs['spatial_grids'] = [g[perm] for g in inputs['spatial_grids']]
    moved = camera.predict_all(states[:,perm], **moved_inputs)[0][-1]
    rotation_weight_grad = camera.head.pose_branch.fc2.weight.grad
    grad_norm = lambda sl: None if rotation_weight_grad is None else float(rotation_weight_grad[sl].float().norm())
    return dict(valid_groups=int(mask.sum()),
        rotation_error_median_deg=float(angle[mask].median()) if mask.any() else None,
        prediction_magnitude_median_deg=float(mag[mask].median()) if mask.any() else None,
        gt_magnitude_median_deg=float(gt_mag[mask].median()) if mask.any() else None,
        feature_frame_std=float(states.float().std(1).mean()),
        origin_permutation_pose_max_abs=float((moved-pred[:,perm]).abs().max()),
        nonpositive_fov_logits_per_stage=(logits<=0).sum(dim=(1,2)).tolist(),
        invalid_fov_frames=int(((pred[...,7:]<=0)|(pred[...,7:]>=math.pi)).any(-1).sum()),
        rotation_weight_grad_norm=grad_norm(slice(3,7)),fov_weight_grad_norm=grad_norm(slice(7,9)),
        component_losses_last_row={k:float(v.mean()) for k,v in camera.last_components.items()},
        settings={k:camera.settings.get(k) for k in ('pose_reference','fov_activation','pose_input')
                  if k != 'pose_input' or k in camera.settings})
