"""Reviewer refutation tests (review_owngrd). Each asserts the behavior the design/brief requires; failures are findings."""
import copy
import pytest
import torch

from conftest import TEACHER_K1
from test_head_kit import tiny_batch, synthetic_target
from owngrd.data import GroundingDataset, teacher_candidates
from owngrd.head import Config, GroundingHead
from owngrd.losses import compute_losses
from owngrd.train import Metrics, seed_all


def _forward(target):
    seed_all(5)
    cfg = Config.tiny()
    head = GroundingHead(cfg)
    out = head(**tiny_batch(cfg), selection_targets=[target])
    out['presence'].retain_grad()
    return cfg, out


@pytest.mark.parametrize('why,teacher', [('disputed_absent', .95), ('miss', .05)])
def test_F2_disagreement_frame_gets_no_presence_gradient(why, teacher):
    # Brief step 2: presence only where GT and SAM 3 agree; design 3.1: DISPUTED has no loss.
    target = synthetic_target()
    target['frames'][3].update(presence=None, why=why, teacher_presence=teacher)
    cfg, out = _forward(target)
    losses, _ = compute_losses(out, [target], cfg)
    losses['total'].backward()
    assert float(out['presence'].grad[0, 3].abs()) == 0.0, f'{why} frame trained toward SAM 3 presence {teacher}'


def test_F1_losses_run_under_cuda_autocast():
    # train.py:115-118 runs compute_losses inside torch.autocast('cuda', bf16); simulate that dispatch on CPU.
    target = synthetic_target()
    cfg, out = _forward(target)
    torch.set_autocast_enabled('cuda', True)
    try:
        with torch._C._IncludeDispatchKeyGuard(torch._C.DispatchKey.AutocastCUDA):
            compute_losses(out, [target], cfg)
    finally:
        torch.set_autocast_enabled('cuda', False)


def _metric_out(selection):
    masks = torch.full((1, 1, 1, 8, 8), -10.)
    return dict(candidates=[[[(0, 0)]]], selection=[torch.tensor(selection)], masks=masks)


def test_F3_false_presence_respects_selector_none():
    m = Metrics()
    absent = dict(gt_instances=[], clip_presence=0, decoder=[dict(gt_masks={})])
    m.add(_metric_out([-5., 5.]), [absent], dict(selection_skipped={}, matches=[[[]]]))
    assert m.result()['false_presence_absent_at85'] == 0.0, 'selector chose none, counted as false presence'


def test_F3_on_target_share_excludes_absent_pairs():
    m = Metrics()
    present_mask = torch.zeros(8, 8)
    present_mask[2:6, 2:6] = 1
    masks = torch.full((1, 1, 1, 8, 8), -10.)
    masks[0, 0, 0, 2:6, 2:6] = 10.
    present = dict(gt_instances=[7], clip_presence=1, decoder=[dict(gt_masks={7: present_mask})])
    m.add(dict(candidates=[[[(0, 0)]]], selection=[torch.tensor([5., -5.])], masks=masks), [present],
          dict(selection_skipped={}, matches=[[[]]]))
    absent = dict(gt_instances=[], clip_presence=0, decoder=[dict(gt_masks={})])
    m.add(dict(candidates=[[]], selection=[torch.tensor([0.])], masks=masks), [absent],
          dict(selection_skipped={}, matches=[[[]]]))
    assert m.result()['on_target_share_at85'] == 1.0, 'correct abstention on an absent pair lowers on-target share'


def test_F4_teacher_candidates_carry_no_source_fingerprint():
    target = synthetic_target()
    for f in target['decoder']:
        for p in f['proposals']:
            p['weight'] = 1.
    feats = [c['features'] for c in teacher_candidates(target)]
    assert feats and not all(f[4] == 0. for f in feats), 'teacher candidates always have iou feature exactly 0 (decoder: sigmoid in (0,1))'


def test_F5_selection_only_confuser_trains_no_match_negative():
    target = synthetic_target()
    for frame in target['decoder']:
        frame['targets'] = []
        frame['hardneg'][0].update(selection_only=True, weight=.25)
    cfg, out = _forward(target)
    match = out['match'].detach().clone().requires_grad_(True)
    masks = out['masks'].detach().clone()
    masks[0, :, 0] = -20.
    masks[0, :, 0, 5:, 5:] = 20.   # query 0 sits on the confuser instance in every frame
    out = dict(out, match=match, masks=masks)
    losses, _ = compute_losses(out, [target], cfg)
    losses['match'].backward()
    assert float(match.grad[0, :, 0].abs().sum()) == 0.0, 'confuser query trained as a full-weight match negative'


def test_F6_teacher_k1_manifest_cannot_train(tmp_path):
    # The only teacher manifest holds 53 heldout captures; train refuses it, and no tool writes a train-only one.
    GroundingDataset(TEACHER_K1, tmp_path, tmp_path, 'train')
