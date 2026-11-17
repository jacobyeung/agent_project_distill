from pathlib import Path
from types import SimpleNamespace as NS

from parity_kit.common import pin, write
from e2e_reader.parity import load_native


def test_native_loading_order_and_receipt_overrides(tmp_path, monkeypatch):
    from student_pilot import carrier_c1_run as trainer
    cfg = dict(base_identity='base', align=None, init_artifact={'artifact': {'path': '/absent'}},
               frame_markers=True, pointing_weights={'decision': 5}, camera_overrides={'weight_focal': 2})
    config = tmp_path/'config.json'; write(config, cfg)
    write(tmp_path/'model.json', dict(schema='p3-model-input-v1', root=str(tmp_path/'base'), files={}))
    receipt = dict(model=pin(tmp_path/'model.json'), camera={'weight_focal': .5, 'unchanged': 1},
                   frame_markers=False, config_sha256='identity')
    write(tmp_path/'receipt.json', receipt)
    write(tmp_path/'artifact.json', dict(base_identity='base', config_sha256='identity'))
    restore = dict(original=dict(config=pin(config)), local={n:pin(tmp_path/n) for n in
                    ('model.json','receipt.json','artifact.json')})
    write(tmp_path/'RESTORE.json', restore)
    seen = []
    proc = object()
    class Model:
        trace_program_version = '3.14'
        def to(self, d):
            seen.append(('to', d)); return self
        def eval(self):
            seen.append(('eval',)); return self
        def requires_grad_(self, value):
            seen.append(('grad', value)); return self
    model = Model()
    def processor(manifest, r):
        assert r['frame_markers'] and r['camera'] == dict(weight_focal=2, unchanged=1)
        assert r['init_artifact'] == cfg['init_artifact']
        seen.append(('processor',)); return proc
    def load(manifest, r, p, evaluation):
        assert 'init_artifact' not in r and 'depth_init' not in r
        assert r['align'] is None and r['pointing_weights'] == {'decision': 5}
        assert evaluation is True and p is proc
        seen.append(('model',)); return model
    def artifact(m, p):
        assert m is model and p == pin(tmp_path/'artifact.json')
        seen.append(('artifact',)); return dict(base_identity='base', config_sha256='identity')
    monkeypatch.setattr(trainer, 'processor_for_receipt', processor)
    monkeypatch.setattr(trainer, 'load_model', load)
    monkeypatch.setattr(trainer, 'load_artifact', artifact)
    monkeypatch.setattr(trainer, 'identity', lambda c: 'identity')
    result = load_native(tmp_path, settings=dict(config=str(config)))
    assert result[:2] == (model, proc)
    assert seen == [('processor',), ('model',), ('artifact',), ('to', 'cpu'), ('eval',), ('grad', False)]
