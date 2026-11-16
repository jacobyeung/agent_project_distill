"""Reviewer: train.main end-to-end exact resume (crash mid-run, resume, compare to an uninterrupted run)."""
import functools, json
import numpy as np
import pytest
import torch
from safetensors.torch import load_file

from test_teacher import small_manifest, run
from owngrd import labels, train, data
from owngrd.common import read_json, atomic_write_json, sha256_json
from owngrd.head import Config
from owngrd.vit import frame_size, rgb_tensor


class StubViT:
    def __init__(self, weights, bundle, device):
        self.device, self.sha256 = torch.device(device), 'stubvit'
        g = torch.Generator().manual_seed(0)
        self.proj = torch.randn(3, 16, generator=g)

    def taps(self, frames, size):
        x = torch.nn.functional.avg_pool2d(rgb_tensor(frames, size), 16).permute(0, 2, 3, 1) @ self.proj
        maps = [x * (k + 1) for k in range(4)]
        return maps, torch.nn.functional.avg_pool2d(maps[-1].permute(0, 3, 1, 2), 2, 2).permute(0, 2, 3, 1)

    def name_query(self, names):
        class Q: pass
        q = Q()
        vec = [torch.tensor([float(ord(ch) % 7) for ch in (n * 24)[:24]]) / 7 for n in names]
        q.tokens, q.mask = torch.stack(vec)[:, None], torch.ones(len(names), 1, dtype=torch.bool)
        q.rows_sha256 = q.tokenizer_sha256 = 'stub'
        return q


@pytest.fixture(scope='module')
def setup(tmp_path_factory):
    root = tmp_path_factory.mktemp('resume')
    manifest = small_manifest(root, n_caps=12, n_names=2)
    man = read_json(manifest)
    man['captures'] = [c for c in man['captures'] if c['k1_split'] == 'train']
    atomic_write_json(manifest, man)
    teacher, label = root/'teacher', root/'labels'
    assert run(manifest, teacher) == 0
    assert labels.main(['--manifest', str(manifest), '--teacher-root', str(teacher), '--out', str(label)]) == 0
    cfg = root/'cfg.json'
    tiny = Config.tiny()
    cfg.write_text(json.dumps(dict(vit_dim=16, name_dim=24, dim=32, heads=4, blocks=2, ffn=64, query_hidden=48,
        pixel_dim=16, presence_dim=16, selector_dim=16, selector_query_dim=16, pretrained_stem=False, tiny_stem=True, points=64)))
    return root, manifest, label, teacher, cfg


def test_main_exact_resume(setup, monkeypatch):
    root, manifest, label, teacher, cfg = setup
    monkeypatch.setattr(train, 'FrozenViT', StubViT)
    monkeypatch.setattr(train, 'GroundingDataset', functools.partial(data.GroundingDataset, validation_fraction=.35))
    args = lambda out: ['--manifest', str(manifest), '--labels', str(label), '--teacher-root', str(teacher), '--out', str(out),
        '--config', str(cfg), '--hours', '1', '--steps', '8', '--validate-every', '2', '--checkpoint-every', '2',
        '--warmup', '2', '--size', '64', '96', '--presence-size', '64', '96']
    assert train.main(args(root/'A')) == 0
    real = train.optimization_step
    calls = {'n': 0}
    def crash(*a, **k):
        calls['n'] += 1
        if calls['n'] == 6:
            raise KeyboardInterrupt('simulated kill after step 5 (checkpoint at 4)')
        return real(*a, **k)
    monkeypatch.setattr(train, 'optimization_step', crash)
    with pytest.raises(KeyboardInterrupt):
        train.main(args(root/'B'))
    monkeypatch.setattr(train, 'optimization_step', real)
    assert train.main(args(root/'B') + ['--resume', str(root/'B'/'resume.pt')]) == 0
    a, b = load_file(str(root/'A/export/head.safetensors')), load_file(str(root/'B/export/head.safetensors'))
    assert a.keys() == b.keys() and all(torch.equal(a[k], b[k]) for k in a)
    va = [json.loads(l) for l in open(root/'A/train.jsonl') if '"validation"' in l]
    vb = [json.loads(l) for l in open(root/'B/train.jsonl') if '"validation"' in l]
    assert va[-1]['metrics'] == vb[-1]['metrics']
