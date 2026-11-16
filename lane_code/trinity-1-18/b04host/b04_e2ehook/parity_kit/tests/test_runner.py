from pathlib import Path

import pytest

from parity_kit.common import OLD, rows, write
from parity_kit.compare import agreement, compare
from parity_kit.build_manifest import build


def test_paired_bootstrap_reuses_script(tmp_path):
    old = [r for r in rows(OLD) if r['arm'] == 'unflagged'][:20]
    path = tmp_path/'new.jsonl'
    import json
    path.write_text(''.join(json.dumps(r)+'\n' for r in old))
    result = compare([path], OLD, tmp_path/'comparison')
    assert all(r['diff'] == 0.0 and r['ci'] == [0.0, 0.0] for r in result.values())


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
