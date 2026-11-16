import copy
import json
from pathlib import Path

import pytest

from parity_kit.common import OLD, read, rows, sha, write
from parity_kit.provenance import digest, row_binding, runtime_identity
from parity_kit.compare import agreement, compare
from parity_kit.build_manifest import build


def test_paired_bootstrap_reuses_script(tmp_path):
    old = [r for r in rows(OLD) if r['arm'] == 'unflagged'][:20]
    path = tmp_path/'new.jsonl'
    write_partition(path, old)
    result = compare([path], OLD, tmp_path/'comparison')
    assert all(r['diff'] == 0.0 and r['ci'] == [0.0, 0.0] for r in result.values())
    report = read(tmp_path/'comparison/PROVENANCE.json')
    assert len(report['partitions']) == 1
    assert report['runtime']['native_fla'] is True
    assert report['runtime']['camera_agreement_label'] == 'within noise'
    assert read(tmp_path/'comparison/CALL_AGREEMENT.json')['label'] == 'within noise'
    assert 'Job 170056 used fla kernels: True' in (tmp_path/'comparison/TABLE.txt').read_text()


def test_call_divergence():
    a = dict(calls={'records': [dict(call='<move from=1 to=2>')]})
    b = dict(decode=dict(calls=[dict(call='<move from=1 to=3>')]))
    report = agreement(a, b)
    assert report['first_divergence_call'] == 0
    assert report['first_divergence_character'] == 16


def test_resume_skips_completed_items_and_refuses_arm_change(tmp_path, monkeypatch):
    from parity_kit import run_parity as R
    from parity_kit.common import META, PREP, REQUEST, tasks, pin
    from e2e_reader import parity
    export = tmp_path/'export'; export.mkdir()
    write(export/'RESTORE.json', {'fixture': True})
    config = META/PREP/'config.json'
    settings = dict(export_dir=str(export), artifact_manifest={'sha256': 'fixture'},
                    config=str(config), arm='own_depth')
    selected = tasks({})[:2]
    calls = []
    def make(*args, **kwargs):
        calls.append('load')
        def gen(t):
            calls.append(t['id'])
            return dict(key='devrows:'+t['id'], scores={}, seconds=0.)
        return gen
    monkeypatch.setattr(parity, 'make_real', make)
    R.run(settings, selected, tmp_path/'run', device='cpu')
    R.run(settings, selected, tmp_path/'run', device='cpu')
    assert calls == ['load'] + [t['id'] for t in selected]
    with pytest.raises(ValueError, match='resume load receipt differs'):
        R.run(dict(settings, arm='scale_head'), selected, tmp_path/'run', device='cpu')


def test_g3t_uses_manifest_basenames(tmp_path, monkeypatch):
    import numpy as np
    from PIL import Image
    from e2e_reader.real import TowerG3T
    from student_pilot import tower_read
    root = tmp_path/'nested'; root.mkdir()
    names = [root/'model.safetensors', root/'config.json']
    class Artifact:
        def files(self, name):
            assert name == 'g3t'
            return names
    class Tower:
        def __init__(self, settings):
            assert settings['weights_path'] == str(names[0])
            assert settings['config_path'] == str(names[1])
            self.dense_frames = settings['dense_frames']
        def run(self, batch):
            from types import SimpleNamespace
            return SimpleNamespace(**{k: np.zeros(1) for k in
                ('raw_pose9', 'anchor_slots', 'frame_indices', 'depth_grid', 'depth_conf_grid', 'grid_uv')})
    monkeypatch.setattr(tower_read, 'FrozenG3TTower', Tower)
    frames = dict(native_frames=[Image.new('RGB',(4,4))], dense_indices=[0], anchor_slots=[0], anchor_indices=[0])
    TowerG3T(Artifact(), 'cpu')(frames)
    names.append(tmp_path/'config.json')
    with pytest.raises(ValueError, match='g3t_file_not_unique'):
        TowerG3T(Artifact(), 'cpu')(frames)


def fixture_receipt(items):
    settings = dict(arm='own_depth', config='fixture', env_roots=[], keys=[r['key'] for r in items])
    runtime = dict(python='fixture', fla=dict(present=False, version=None, origin=None))
    return dict(schema='parity-load-v2', arm='own_depth', device='cpu',
                inputs=dict(settings=settings, runtime_code=[dict(path='code', sha256='code-pin')]),
                artifact_manifest=dict(sha256='artifact-pin'), restore_pin=dict(sha256='restore-pin'),
                runtime_identity=runtime, runtime_identity_sha256=digest(runtime),
                settings_sha256=digest(settings), keys=settings['keys'],
                dense_frame_counts={r['key']: 64 for r in items})


def write_partition(path, items, mutate=None):
    receipt = fixture_receipt(items)
    if mutate:
        mutate(receipt)
    receipt['settings_sha256'] = digest(receipt['inputs']['settings'])
    receipt['runtime_identity_sha256'] = digest(receipt['runtime_identity'])
    receipt_path = path.parent/'LOAD_RECEIPT.json'
    write(receipt_path, receipt)
    binding = row_binding(receipt, sha(receipt_path))
    path.write_text(''.join(json.dumps(dict(r, **binding))+'\n' for r in items))


@pytest.mark.parametrize('field', ['arm', 'settings', 'code', 'artifact', 'runtime', 'restore'])
def test_compare_refuses_mixed_receipts(tmp_path, field):
    old = [r for r in rows(OLD) if r['arm'] == 'unflagged'][:2]
    left, right = tmp_path/'left/items.jsonl', tmp_path/'right/items.jsonl'
    write_partition(left, old[:1])
    def mutate(receipt):
        if field == 'arm':
            receipt['arm'] = receipt['inputs']['settings']['arm'] = 'scale_head'
        elif field == 'settings':
            receipt['inputs']['settings']['config'] = 'other'
        elif field == 'code':
            receipt['inputs']['runtime_code'][0]['sha256'] = 'other'
        elif field == 'artifact':
            receipt['artifact_manifest']['sha256'] = 'other'
        elif field == 'runtime':
            receipt['runtime_identity']['python'] = 'other'
        else:
            receipt['restore_pin']['sha256'] = 'other'
    write_partition(right, old[1:], mutate)
    with pytest.raises(ValueError, match='partition load receipts differ'):
        compare([left, right], OLD, tmp_path/'comparison')


def test_compare_accepts_disjoint_compatible_partitions(tmp_path):
    old = [r for r in rows(OLD) if r['arm'] == 'unflagged'][:20]
    left, right = tmp_path/'left/items.jsonl', tmp_path/'right/items.jsonl'
    write_partition(left, old[:10])
    write_partition(right, old[10:])
    result = compare([left, right], OLD, tmp_path/'comparison')
    assert all(r['diff'] == 0.0 for r in result.values())
    report = read(tmp_path/'comparison/PROVENANCE.json')
    assert [p['keys'] for p in report['partitions']] == [[r['key'] for r in chunk] for chunk in (old[:10], old[10:])]


@pytest.mark.parametrize('field', ['arm', 'settings_sha256', 'load_receipt_sha256', 'runtime_identity_sha256'])
def test_compare_refuses_row_provenance(tmp_path, field):
    old = [r for r in rows(OLD) if r['arm'] == 'unflagged'][:1]
    path = tmp_path/'items.jsonl'
    write_partition(path, old)
    item = rows(path)[0]
    item[field] = 'other'
    path.write_text(json.dumps(item)+'\n')
    with pytest.raises(ValueError, match='journal provenance differs: ' + field):
        compare([path], OLD, tmp_path/'comparison')


@pytest.fixture
def resumable(tmp_path, monkeypatch):
    from parity_kit import run_parity as runner
    from parity_kit.common import META, PREP, tasks, key
    from e2e_reader import parity
    export = tmp_path/'export'
    write(export/'RESTORE.json', {'fixture': True})
    settings = dict(export_dir=str(export), artifact_manifest={'sha256': 'fixture'},
                    config=str(META/PREP/'config.json'), arm='own_depth', env_roots=[])
    selected = tasks({})[:2]
    monkeypatch.setattr(parity, 'make_real', lambda *a, **kw:
                        lambda t: dict(key=key(t), arm=settings['arm'], scores={}, seconds=0.))
    out = tmp_path/'run'
    runner.run(settings, selected, out, device='cpu')
    return runner, settings, selected, out


@pytest.mark.parametrize('field', ['arm', 'settings_sha256', 'load_receipt_sha256', 'runtime_identity_sha256'])
def test_resume_refuses_mixed_row_provenance(resumable, field):
    runner, settings, selected, out = resumable
    path = out/'items.jsonl'
    items = rows(path)
    items[0][field] = 'scale_head' if field == 'arm' else 'other'
    path.write_text(''.join(json.dumps(r)+'\n' for r in items))
    with pytest.raises(ValueError, match='journal provenance differs: ' + field):
        runner.run(settings, selected, out, device='cpu')


@pytest.mark.parametrize('field', ['python', 'torch', 'transformers', 'numpy', 'scipy', 'torchvision',
                                   'fla', 'causal_conv1d', 'PYTHONPATH', 'env_roots', 'cuda_device_name'])
def test_resume_refuses_runtime_identity_change(resumable, monkeypatch, field):
    runner, settings, selected, out = resumable
    changed = copy.deepcopy(read(out/'LOAD_RECEIPT.json')['runtime_identity'])
    changed[field] = 'changed'
    monkeypatch.setattr(runner, 'runtime_identity', lambda *a: changed)
    with pytest.raises(ValueError, match='resume load receipt differs'):
        runner.run(settings, selected, out, device='cpu')


def test_resume_refuses_changed_receipt_bytes(resumable):
    runner, settings, selected, out = resumable
    path = out/'LOAD_RECEIPT.json'
    path.write_text(path.read_text() + '\n')
    with pytest.raises(ValueError, match='resume load receipt bytes differ'):
        runner.run(settings, selected, out, device='cpu')


def test_resume_rows_pin_actual_receipt(resumable):
    _, settings, _, out = resumable
    receipt = read(out/'LOAD_RECEIPT.json')
    for item in rows(out/'items.jsonl'):
        assert item['arm'] == settings['arm']
        assert item['settings_sha256'] == digest(settings)
        assert item['load_receipt_sha256'] == sha(out/'LOAD_RECEIPT.json')
        assert item['runtime_identity_sha256'] == digest(receipt['runtime_identity'])


def test_runtime_identity_records_environment(monkeypatch):
    import torch
    monkeypatch.setattr('parity_kit.provenance.metadata.version', lambda name: 'fixture-' + name)
    monkeypatch.setenv('PYTHONPATH', '/scratch/runtime-fixture')
    monkeypatch.setattr(torch.cuda, 'get_device_name', lambda device: 'fixture GPU')
    identity = runtime_identity({'env_roots': ['/scratch/env']}, 'cuda:0')
    assert identity['python']['version'] and identity['python']['executable']
    assert identity['torch'] == dict(version=str(torch.__version__), cuda=torch.version.cuda)
    for name in ('transformers', 'numpy', 'scipy', 'torchvision'):
        assert identity[name] == 'fixture-' + name
    assert identity['PYTHONPATH'] == '/scratch/runtime-fixture'
    assert identity['env_roots'] == ['/scratch/env']
    assert identity['cuda_device_name'] == 'fixture GPU'
    assert all(isinstance(identity[n]['present'], bool) for n in ('fla', 'causal_conv1d'))


def test_runtime_identity_records_absent_packages(monkeypatch):
    from importlib import metadata
    def version(name):
        raise metadata.PackageNotFoundError(name)
    monkeypatch.setattr('parity_kit.provenance.metadata.version', version)
    identity = runtime_identity({}, 'cpu')
    for name in ('transformers', 'numpy', 'scipy', 'torchvision'):
        assert identity[name] is None
    assert identity['cuda_device_name'] is None
