"""Regression checks for loss routing, visibility ceilings, and resume bookkeeping."""
import json
from types import SimpleNamespace

import pytest
import torch

from test_head_kit import synthetic_target, tiny_batch
from owngrd.common import atomic_write_json
from owngrd.head import Config, GroundingHead
from owngrd.losses import compute_losses, distill_presence
from owngrd.train import Metrics, Stopper, epoch_order, recall_ceilings, rewind_log
from test_head_kit import stub_data


@pytest.mark.parametrize('why', ['disputed_absent', 'miss', 'sliver', 'invalid_frame'])
def test_forbidden_rows_have_no_presence_or_joint_distillation(why):
    cfg = Config.tiny()
    target = synthetic_target()
    for row in target['frames']:
        row.update(why=why, presence=1)
    out = GroundingHead(cfg)(**tiny_batch(cfg), selection_targets=[target])
    losses, _ = compute_losses(out, [target], cfg)
    assert losses['presence'].item() == losses['distill'].item() == 0


@pytest.mark.parametrize('role', ['gt', 'confuser', 'absent'])
def test_distillation_allowlist(role):
    for why in ('pos', 'miss', 'sliver', 'disputed_absent', 'invalid_frame', None):
        assert not distill_presence(dict(why=why), role)
    for why in ('uncertain_absent', 'not_annotatable'):
        assert distill_presence(dict(why=why), role)
    assert distill_presence(dict(why='absent'), role) == (role != 'gt')


def test_disputed_query_is_not_a_match_negative():
    cfg = Config.tiny()
    target = synthetic_target()
    out = GroundingHead(cfg)(**tiny_batch(cfg))
    masks = out['masks'].detach().clone()
    match = out['match'].detach().clone().requires_grad_(True)
    for f, frame in enumerate(target['decoder']):
        frame['targets'], frame['hardneg'], frame['soft'] = [], [], []
        disputed = frame['proposals'][0]
        disputed['cls'] = 'DISPUTED'
        masks[0, f, 0] = torch.where(disputed['mask'] > .5, 20., -20.)
    losses, _ = compute_losses(dict(out, masks=masks, match=match), [target], cfg)
    losses['match'].backward()
    assert match.grad[0, :, 0].abs().sum() == 0
    assert match.grad[0, :, 1:].abs().sum() > 0


def test_teacher_features_reach_selector():
    cfg = Config.tiny()
    model = GroundingHead(cfg)
    seen = []
    model.selector.register_forward_pre_hook(lambda module, args: seen.append(args[0].detach().clone()))
    out = model(**tiny_batch(cfg), selection_targets=[synthetic_target()])
    for i, candidate in enumerate(out['selection_candidates'][0]):
        if candidate['source'] == 'teacher':
            torch.testing.assert_close(seen[0][i], candidate['features'].detach())
            assert 0 < seen[0][i, 4] < 1


def test_recall_denominators_and_top_five():
    mask = torch.ones(8, 8)
    masks = torch.full((1, 1, 6, 8, 8), -10.)
    masks[0, 0, 5] = 10
    out = dict(candidates=[[[(0, q)] for q in range(6)]],
               masks=masks, selection=[torch.tensor([0.]*6+[1.])])
    target = dict(gt_instances=[7], clip_presence=1, decoder=[dict(gt_masks={7: mask})])
    details = dict(selection_skipped={}, matches=[[[]]])
    metric = Metrics()
    metric.add(out, [target], details)
    assert metric.result()['candidate_recall_at5'] == 0
    out['candidates'] = [[[(0, 5)]]]
    out['selection'] = [torch.tensor([5., -5.])]
    metric = Metrics()
    metric.add(out, [target], details)
    target = dict(target, gt_instances=[7, 8])
    metric.add(out, [target], details)
    result = metric.result()
    assert result['candidate_recall_at5'] == 1
    assert result['candidate_recall_at5_all_instances'] == pytest.approx(2/3)
    assert result['unambiguous_names'] == 1


def test_label_only_ceiling_includes_invisible_ids(tmp_path):
    label = dict(id_name={'1': 'chair', '2': 'table', '3': 'lamp', '4': 'lamp'},
                 frames={'0': {'chair': {'gt_visible': [1]}, 'table': {'gt_visible': []},
                               'lamp': {'gt_visible': [3]}}})
    atomic_write_json(tmp_path/'arkitscenes__1.labels.json.gz', label, gz=True)
    ds = SimpleNamespace(items=[(0, 'chair'), (0, 'table'), (0, 'lamp')],
                         captures=[{'canonical': 'arkitscenes/1'}], label_root=tmp_path)
    ceilings = recall_ceilings(ds, range(3))
    assert ceilings['unambiguous'] == ceilings['all_instances'] == .5
    metrics = dict(candidate_recall_at5=.36, mask_iou_pos=.5, false_presence_absent_at85=0,
                   on_target_share_at85=0)
    assert Stopper(recall_bar=.70*ceilings['unambiguous']).decide(600, metrics)[0] == 'CONTINUE'
    metrics['candidate_recall_at5'] = .34
    assert Stopper(recall_bar=.35).decide(600, metrics)[1] == 'fail_fast_at_600'


def test_permutation_and_resume_log(tmp_path):
    order = epoch_order(30, 42, 0)
    assert sorted(order) == list(range(30)) and order != list(range(30))
    assert order == epoch_order(30, 42, 0) and order != epoch_order(30, 42, 1)
    path = tmp_path/'train.jsonl'
    rows = [dict(event='train', step=i) for i in range(1, 6)]
    original = ''.join(json.dumps(r)+'\n' for r in rows)
    path.write_text(original)
    rewind_log(path, 4)
    assert [json.loads(line)['step'] for line in path.read_text().splitlines()] == [1, 2, 3, 4]
    assert next(tmp_path.glob('train.jsonl.before_resume.*')).read_text() == original


def test_validation_feature_reuse_preserves_metrics(stub_data, monkeypatch):
    from owngrd import train
    from owngrd.data import GroundingDataset
    from test_review_resume import StubViT
    dataset = GroundingDataset(*stub_data, split='inspect', size_hw=(64, 96))
    model = GroundingHead(Config.tiny())
    vit = StubViT(None, None, 'cpu')
    calls = []
    original = train.encode_presence
    def counted(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(train, 'encode_presence', counted)
    cached = train.validate(model, vit, dataset, (64, 96), indices=[0, 1, 2])
    assert len(calls) == 1
    class SeparateNames:
        def __getitem__(self, index):
            item = dataset[index]
            return dict(item, canonical=item['canonical']+'|'+item['name'])
        def get_item(self, *args, **kwargs):
            return dataset.get_item(*args, **kwargs)
    calls.clear()
    uncached = train.validate(model, vit, SeparateNames(), (64, 96), indices=[0, 1, 2])
    assert len(calls) == 3
    assert cached == uncached


def test_validation_timeout_preserves_stop_reason_and_subset(stub_data, tmp_path, monkeypatch):
    from dataclasses import asdict
    import functools
    from owngrd import train, data
    from owngrd.split_manifest import split_manifest
    from test_review_resume import StubViT
    manifest, labels, teacher = stub_data
    filtered = tmp_path/'train.json'
    split_manifest(manifest, 'train', filtered)
    config = tmp_path/'config.json'
    config.write_text(json.dumps(asdict(Config.tiny())))
    monkeypatch.setattr(train, 'FrozenViT', StubViT)
    monkeypatch.setattr(train, 'GroundingDataset', functools.partial(data.GroundingDataset, validation_fraction=.35))
    def timed_out(*args, **kwargs):
        raise TimeoutError('test validation deadline')
    monkeypatch.setattr(train, 'validate', timed_out)
    out = tmp_path/'run'
    assert train.main(['--manifest', str(filtered), '--labels', str(labels), '--teacher-root', str(teacher),
        '--out', str(out), '--config', str(config), '--hours', '1', '--steps', '1', '--validate-every', '1',
        '--checkpoint-every', '1', '--size', '64', '96', '--presence-size', '64', '96', '--val-items', '2']) == 0
    rows = [json.loads(line) for line in (out/'train.jsonl').read_text().splitlines()]
    assert rows[-1]['reason'] == 'hour_cap_during_validation'
    run = json.loads((out/'RUN.json').read_text())
    assert len(run['validation_indices']) == 2
    assert run['fail_fast_recall_bar'] == .70*run['recall_ceilings']['unambiguous']
