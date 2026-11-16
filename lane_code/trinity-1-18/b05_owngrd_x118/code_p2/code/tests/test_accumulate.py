"""Gradient accumulation: exact resume with several names per update, and a one-item update equals the plain step."""
import copy, functools, json
import pytest
import torch
from safetensors.torch import load_file

from test_review_resume import StubViT, setup
from owngrd import train, data
from owngrd.head import Config, GroundingHead
from owngrd.common import read_json


def test_accumulated_main_exact_resume(setup, monkeypatch):
    root, manifest, label, teacher, cfg = setup
    monkeypatch.setattr(train, 'FrozenViT', StubViT)
    monkeypatch.setattr(train, 'GroundingDataset', functools.partial(data.GroundingDataset, validation_fraction=.35))
    args = lambda out: ['--manifest', str(manifest), '--labels', str(label), '--teacher-root', str(teacher), '--out', str(out),
        '--config', str(cfg), '--hours', '1', '--steps', '6', '--validate-every', '2', '--checkpoint-every', '2',
        '--warmup', '2', '--size', '64', '96', '--presence-size', '64', '96', '--accumulate', '3']
    assert train.main(args(root/'C')) == 0
    real = train.accumulated_step
    calls = {'n': 0}
    def crash(*a, **k):
        calls['n'] += 1
        if calls['n'] == 4:
            raise KeyboardInterrupt('simulated kill in update 4 (checkpoint at 2)')
        return real(*a, **k)
    monkeypatch.setattr(train, 'accumulated_step', crash)
    with pytest.raises(KeyboardInterrupt):
        train.main(args(root/'D'))
    monkeypatch.setattr(train, 'accumulated_step', real)
    assert train.main(args(root/'D') + ['--resume', str(root/'D'/'resume.pt')]) == 0
    a, b = load_file(str(root/'C/export/head.safetensors')), load_file(str(root/'D/export/head.safetensors'))
    assert a.keys() == b.keys() and all(torch.equal(a[k], b[k]) for k in a)
    rows = [json.loads(l) for l in open(root/'C/train.jsonl')]
    tr = [r for r in rows if r['event'] == 'train']
    assert [r['step'] for r in tr] == list(range(1, 7)) and all(len(r['name']) == 3 for r in tr)
    n_train = len(data.GroundingDataset(manifest, label, teacher, 'train', (64, 96), seed=42, validation_fraction=.35))
    assert tr[-1]['epoch']*n_train + tr[-1]['item'] == 18
    va = [json.loads(l) for l in open(root/'C/train.jsonl') if '"validation"' in l]
    vb = [json.loads(l) for l in open(root/'D/train.jsonl') if '"validation"' in l]
    assert va[-1]['metrics'] == vb[-1]['metrics']


def test_single_item_accumulation_equals_plain_step(setup, monkeypatch):
    root, manifest, label, teacher, cfg = setup
    vit = StubViT(None, None, 'cpu')
    ds = data.GroundingDataset(manifest, label, teacher, 'train', (64, 96), seed=42, validation_fraction=.35)
    item = ds[0]
    batch = train.encode_item(vit, item, (64, 96))
    train.seed_all(3)
    m1 = GroundingHead(Config(**read_json(cfg)))
    m2 = copy.deepcopy(m1)
    o1, s1 = train.make_optimizer(m1, warmup=2, steps=10)
    o2, s2 = train.make_optimizer(m2, warmup=2, steps=10)
    state = torch.get_rng_state()
    l1, _, n1 = train.optimization_step(m1, batch, [item['target']], o1, s1)
    torch.set_rng_state(state)
    l2, _, n2 = train.accumulated_step(m2, [(batch, [item['target']])], o2, s2)
    assert abs(n1-n2) < 1e-5 and all(abs(l1[k]-l2[k]) < 1e-5 for k in l1)
    assert all(torch.allclose(a, b, atol=1e-6) for a, b in zip(m1.parameters(), m2.parameters()))
