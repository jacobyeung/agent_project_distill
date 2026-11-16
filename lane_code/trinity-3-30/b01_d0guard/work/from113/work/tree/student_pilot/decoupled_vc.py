"""Private trainable vision copy, preserving V's exact BF16 feature computation."""
import copy
from contextlib import nullcontext

import torch
from torch.func import functional_call
from torch.utils.checkpoint import checkpoint

from .decoupled_v import VisionOnly, RECIPE
from .p3_heads import PrefixCapture

VC_RECIPE = {**RECIPE, 'encoder_learning_rate': 1e-5}
# 4h batch cap: 1200 * 10.5s + 240s startup + 120s exports = 12960s,
# leaving 1440s (10% of the allocation). Keep the legacy recipe immutable.
VC_BATCH4H_RECIPE = {**VC_RECIPE, 'steps': 1200, 'milestones': [200, 400, 800, 1200]}


class VisionCopy(VisionOnly):
    def __init__(self, config, visual):
        # Own both config and tensors, even when the caller passes a live base encoder.
        config = copy.deepcopy(config)
        config.p3['feature_backing'] = 'decoupled_vc'
        super().__init__(config, copy.deepcopy(visual))
        self.model.visual.float().requires_grad_(True)
        self.gradient_checkpointing = True

    def train(self, mode=True):
        super().train(mode)
        self.model.visual.train(mode)
        return self


def capture_features(model, view, batch):
    """Cast masters inside the checkpoint closure so recomputation has the same dtype.

    Native FP32 rotary buffers stay FP32. Casting every parameter explicitly also
    preserves BF16 layer-norm behavior, unlike autocast over FP32 module storage.
    """
    visual = model.model.visual

    def compute(pixels):
        parameters = {n: p.to(torch.bfloat16) for n, p in visual.named_parameters()}
        with PrefixCapture(view, batch) as capture:
            functional_call(visual, parameters, (pixels.to(torch.bfloat16),),
                            {'grid_thw': batch['video_grid_thw']})
            capture.finish()
        return (capture.states, capture.grids[0], *capture.vits[0])

    training = model.training and torch.is_grad_enabled()
    with nullcontext() if training else torch.no_grad():
        if training and model.gradient_checkpointing:
            values = checkpoint(compute, batch['pixel_values_videos'], use_reentrant=False)
        else:
            values = compute(batch['pixel_values_videos'])
    result = PrefixCapture(view, batch)
    result.states, result.grids, result.vits = values[0], [values[1]], [list(values[2:])]
    result.forward_count = 1
    return result


def parameter_groups(model, recipe):
    groups = [dict(params=list(model.auxiliary_heads.parameters()),
                   lr=recipe['learning_rate'], initial_lr=recipe['learning_rate'], name='heads')]
    if model.config.p3['feature_backing'] == 'decoupled_vc':
        groups.append(dict(params=list(model.model.visual.parameters()),
                           lr=recipe['encoder_learning_rate'],
                           initial_lr=recipe['encoder_learning_rate'], name='encoder_copy'))
    return groups


def freeze_for_inference(model):
    """Materialize the frozen BF16 compute copy once; preserve native rotary buffers."""
    model.requires_grad_(False).eval()
    for parameter in model.model.visual.parameters():
        parameter.data = parameter.data.to(torch.bfloat16)
    return model
