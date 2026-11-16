"""Small CPU exports, real export-checker validation, and overlay boundary tests."""
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tarfile
from types import SimpleNamespace as NS

import pytest
import milestone as M
import rv_read as R
import rv_d0 as D


def js(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value)+'\n')


def safetensor():
    header = json.dumps({'weight': dict(dtype='BF16', shape=[1], data_offsets=[0, 2])}).encode()
    return struct.pack('<Q', len(header)) + header + b'\0\0'


# Map only fixture mount paths; all validation comes from the unchanged checker.
CHECK_SCRIPT = '''
import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import common, export_check
root, logical, digest, step, base, mode = sys.argv[2:]
old_local = common.local
def local(p):
    p = str(p)
    for prefix, folder in ((%r, 'fsw'), (%r, 'm/ap')):
        if p == prefix or p.startswith(prefix+'/'):
            p = str(Path(root)/folder/p[len(prefix):].lstrip('/'))
            break
    return old_local(p)
common.local = export_check.local = local
result = export_check.check_export(logical, digest, base, int(step), header_only=mode=='header-only')
result['artifact']['path'] = logical
print(json.dumps(result))
''' % (str(R.T.FSW), str(R.T.AP))


def real_check(root, logical, digest, step, full, receipt, bwrap):
    models = R.T.load(R.KIT/'launcher/MODELS.json')
    argv = [sys.executable, '-B', '-c', CHECK_SCRIPT, str(R.KIT/'reader/out'), str(root), logical,
            digest, str(step), models['base']['path'], 'full' if full else 'header-only']
    result = subprocess.run(argv, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    checked = json.loads(result.stdout)
    js(receipt/'CHECK.json', checked)
    js(receipt/'COMMAND.json', dict(gpu=False, source_sha256=D.CHECKER_PINS, fixture_path_mapping=True))
    return checked


@pytest.fixture
def staged(tmp_path, monkeypatch):
    root = tmp_path/'root'; step = 100
    logical = str(R.T.FSW/'ap/8865619b/runs/359fcc3c/m100/artifact.json')
    weights = safetensor()
    digest = lambda raw: hashlib.sha256(raw).hexdigest()
    encode = lambda value: (json.dumps(value)+'\n').encode()
    index = encode(dict(weight_map={'weight': 'model.safetensors'}))
    manifest = encode(dict(schema='full-ft-export-v1', dtype='bfloat16', tensor_count=1,
        index=dict(name='model.safetensors.index.json', sha256=digest(index)),
        files=[dict(name='model.safetensors', sha256=digest(weights), bytes=len(weights), tensors=1)]))
    artifact = encode(dict(schema='carrier-c1-artifact-v1', step=step,
        full_weights=dict(path=str(Path(logical).parent/'full_weights/full_weights.json'), sha256=digest(manifest))))
    files = {'artifact.json': artifact, 'heads.pt': b'fixture', 'full_weights/full_weights.json': manifest,
             'full_weights/model.safetensors.index.json': index, 'full_weights/model.safetensors': weights}
    archive = tmp_path/'export.tar'
    with tarfile.open(str(archive), 'w') as tf:
        for name, raw in files.items():
            info = tarfile.TarInfo('m100/'+name); info.size = len(raw)
            tf.addfile(info, io.BytesIO(raw))
    done = tmp_path/'DONE.json'
    js(done, dict(object='q8/8865619b/359fcc3c_m100.tar', bytes=archive.stat().st_size, sha256=R.T.sha(archive)))
    base = R.T.physical(root, R.T.load(R.KIT/'launcher/MODELS.json')['base']['path'])
    base.mkdir(parents=True); (base/'model.safetensors').write_bytes(weights)
    monkeypatch.setattr(R.T, 'kit_stage', lambda: NS(room=lambda *a: None))
    monkeypatch.setattr(M, 'run_export_checker', real_check)
    receipt = M.stage_export(NS(root=str(root), tar=str(archive), done=str(done), step=step,
                               run='359fcc3c', full=False, bwrap='/usr/bin/bwrap'))
    pin = dict(kind='c1_export', path=logical, sha256=receipt['artifact_sha256'])
    return NS(root=root, path=R.T.physical(root, logical), pin=pin,
              receipt=root/'exports/359fcc3c_m100/RECEIPT.json', base=base)


def test_staged_d0_and_full_checker(staged):
    s = staged
    assert R.select_artifact(s.root, s.path, s.pin['sha256']) == s.pin
    identity = D.admit(s.root, s.pin)
    assert identity['step'] == 100
    assert identity['stage_receipt']['checker']['status'] == 'HEADER_ONLY_NOT_VERIFIED'
    checked = real_check(s.root, s.pin['path'], s.pin['sha256'], 100, True, s.root/'full_check', '')
    assert checked['status'] == 'VERIFIED' and checked['tensor_count'] == 1
    (s.path.parent/'full_weights/model.safetensors').write_bytes(safetensor()[:-1]+b'1')
    with pytest.raises(subprocess.CalledProcessError):
        real_check(s.root, s.pin['path'], s.pin['sha256'], 100, True, s.root/'bad_check', '')


@pytest.mark.parametrize('field,value', [('status', 'failed'), ('run', '469ddece'), ('step', 101),
    ('step', True), ('artifact_sha256', '0'*64), ('artifact', '/wrong'), ('checker_mode', 'unknown')])
def test_receipt_refusals(staged, field, value):
    receipt = R.T.load(staged.receipt); receipt[field] = value; js(staged.receipt, receipt)
    with pytest.raises(ValueError): R.select_artifact(staged.root, staged.path, staged.pin['sha256'])


@pytest.mark.parametrize('field,value', [('status', 'VERIFIED'), ('step', 101), ('scope', 'routed'),
    ('artifact', dict(path='/wrong', sha256='0'*64))])
def test_checker_receipt_refusals(staged, field, value):
    receipt = R.T.load(staged.receipt); receipt['checker'][field] = value
    js(staged.receipt, receipt); js(staged.receipt.parent/'CHECK.json', receipt['checker'])
    with pytest.raises(ValueError): R.select_artifact(staged.root, staged.path, staged.pin['sha256'])


@pytest.mark.parametrize('kind', ['lineage', 'run', 'step', 'zero', 'bool', 'hash', 'missing_receipt',
                                  'artifact_link', 'ancestor_link', 'weights_link', 'receipt_link', 'checker_pin'])
def test_export_refusals(staged, kind):
    s = staged; path = s.path; digest = s.pin['sha256']
    if kind in ('lineage', 'run'):
        path = Path(str(path).replace('8865619b' if kind == 'lineage' else '359fcc3c', 'deadbeef'))
        path.parent.mkdir(parents=True); path.write_bytes(s.path.read_bytes())
    elif kind in ('step', 'zero', 'bool'):
        value = R.T.load(path); value['step'] = {'step': 101, 'zero': 0, 'bool': True}[kind]
        js(path, value); digest = R.T.sha(path)
    elif kind == 'hash': digest = '0'*64
    elif kind == 'missing_receipt': s.receipt.rename(s.receipt.with_suffix('.saved'))
    elif kind in ('artifact_link', 'receipt_link', 'weights_link'):
        target = {'artifact_link': path, 'receipt_link': s.receipt,
                  'weights_link': path.parent/'full_weights/model.safetensors'}[kind]
        saved = target.with_suffix('.saved'); target.rename(saved); target.symlink_to(saved)
    elif kind == 'ancestor_link':
        parent = path.parent; saved = parent.with_name('saved_m100'); parent.rename(saved); parent.symlink_to(saved)
    elif kind == 'checker_pin':
        command = R.T.load(s.receipt.parent/'COMMAND.json'); command['source_sha256']['export_check.py'] = '0'*64
        js(s.receipt.parent/'COMMAND.json', command)
    with pytest.raises(ValueError): R.select_artifact(s.root, path, digest)


def test_overlay_exact_values_and_bind(staged, monkeypatch):
    s = staged; out = s.root/'packet'; out.mkdir()
    original = (R.KIT/'reader/official_adapter.py').read_bytes()
    evidence = D.write_overlay(out, R.KIT, D.admit(s.root, s.pin))
    raw = (out/D.OVERLAY).read_bytes()
    assert evidence['sha256'] == hashlib.sha256(raw).hexdigest()
    assert len(evidence['replacements']) == 4
    for row in reversed(evidence['replacements']): raw = raw.replace(row['new'].encode(), row['old'].encode(), 1)
    assert raw == original
    monkeypatch.setattr(R.T, 'namespace', lambda *a, **k: ['bwrap', '--ro-bind', str(s.root/'trinity_runner_t6'), '/trinity-build'])
    command = R.namespace(s.root, adapter=evidence, packet=out)
    assert command[-3:] == ['--ro-bind', str(out/D.OVERLAY), D.TARGET]
    assert command.index(str(R.KIT)) < command.index(str(out/D.OVERLAY))
    assert (R.KIT/'reader/official_adapter.py').read_bytes() == original
    cfg = R.make_config(s.root, out, 'proof', s.pin, evidence)
    assert cfg['spec']['step'] == 100 and cfg['spec']['models']['cp1m200'] == s.pin
    assert cfg['spec']['models']['base'] == R.T.load(R.KIT/'launcher/MODELS.json')['base']
    (out/D.OVERLAY).write_bytes((out/D.OVERLAY).read_bytes()+b'\n')
    with pytest.raises(ValueError, match='SHA256'): R.namespace(s.root, adapter=evidence, packet=out)


@pytest.mark.parametrize('field,value', [('sha256', '0'*64), ('step', 101), ('target', '/wrong'),
                                        ('replacements', [])])
def test_overlay_receipt_tampering(staged, field, value):
    out = staged.root/'packet'; out.mkdir()
    evidence = D.write_overlay(out, R.KIT, D.admit(staged.root, staged.pin))
    evidence[field] = value
    with pytest.raises(ValueError): D.verify_overlay(out, R.KIT, evidence)


def test_step544_baseline_identical(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('rv_baseline', R.BUILD.parent/'build_rv/rv_read.py')
    baseline = importlib.util.module_from_spec(spec); spec.loader.exec_module(baseline)
    baseline.BUILD = R.BUILD; baseline.KIT = R.KIT
    artifact = R.T.load(R.KIT/'launcher/MODELS.json')['cp1m200']
    path = R.T.physical(tmp_path, artifact['path']); js(path, dict(step=544))
    old_sha = R.T.sha
    monkeypatch.setattr(R.T, 'sha', lambda p: artifact['sha256'] if Path(p) == path else old_sha(p))
    assert R.select_artifact(tmp_path, path, artifact['sha256']) == baseline.select_artifact(tmp_path, path, artifact['sha256'])
    for mode in ('proof', 'production'):
        a = R.make_config(tmp_path, tmp_path/'packet', mode, artifact)
        b = baseline.make_config(tmp_path, tmp_path/'packet', mode, artifact)
        assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    monkeypatch.setattr(R.T, 'namespace', lambda *a, **k: ['bwrap', '--ro-bind', str(tmp_path/'trinity_runner_t6'), '/trinity-build'])
    assert R.namespace(tmp_path) == baseline.namespace(tmp_path)
    assert R.pins_check() == baseline.pins_check()


def test_real_adapter_bind_and_launch_checker(staged):
    s = staged; out = s.root/'adapter_test'; out.mkdir()
    evidence = D.write_overlay(out, R.KIT, D.admit(s.root, s.pin))
    script = CHECK_SCRIPT.split('result = export_check.check_export')[0] + '''
import hashlib, os, types
kit, overlay, dest = map(Path, sys.argv[8:])
sys.path.insert(0, str(kit/'reader'))
namespace = dict(__file__=str(kit/'reader/official_adapter.py'), __name__='official_adapter_fixture')
exec(compile(overlay.read_bytes(), namespace['__file__'], 'exec'), namespace)
A = types.SimpleNamespace(**namespace)
calls = []
def checked(path, digest, base, step):
    calls.append(step)
    result = export_check.check_export(path, digest, base, step)
    result['artifact']['path'] = path
    return result
namespace['check_export'] = checked
original_pins = A.code_pins
def pins():
    value = original_pins()
    value['official_adapter.py'] = hashlib.sha256(overlay.read_bytes()).hexdigest()
    return value
namespace['code_pins'] = pins
models = json.loads((kit/'launcher/MODELS.json').read_text())
original_models = json.loads(json.dumps(models))
models['cp1m200'] = dict(kind='c1_export', path=logical, sha256=digest)
A.model_specs(models)
try: A.model_specs(original_models)
except ValueError: pass
else: raise AssertionError('Overlay accepted step-544 artifact hash')
cfg = A.bind(dest, models, kit/'inputs/i1.json', dest/'videos', mode='proof')
assert cfg['reader']['step'] == int(step)
assert cfg['reader']['export_verification']['status'] == 'VERIFIED'
assert len(A.tasks(cfg)) == 10
# Stop immediately after the real launch checker, before model copies or execution.
cfg['mode'] = 'production'
namespace['verify_bound'] = lambda dest: (cfg, {})
os.environ['CUDA_VISIBLE_DEVICES'] = 'fixture'
sys.modules['vllm'] = types.SimpleNamespace(__version__='0.32.0')
class Boundary(Exception): pass
def prepare(*a): raise Boundary()
for name in ('stage', 'worker', 'merge', 'budget_merge'):
    sys.modules[name] = types.SimpleNamespace(prepare=prepare)
try: A.launch(dest)
except Boundary: pass
else: raise AssertionError('Did not reach the model staging boundary')
assert calls == [int(step), int(step)]
'''
    # The fixture script accepts extra adapter arguments after the checker arguments.
    script = script.replace('root, logical, digest, step, base, mode = sys.argv[2:]',
                            'root, logical, digest, step, base, mode = sys.argv[2:8]')
    result = subprocess.run([sys.executable, '-B', '-c', script, str(R.KIT/'reader/out'), str(s.root),
        s.pin['path'], s.pin['sha256'], '100', R.T.load(R.KIT/'launcher/MODELS.json')['base']['path'],
        'full', str(R.KIT), str(out/D.OVERLAY), str(out/'a0')], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert result.returncode == 0, result.stderr
    D.audit_bound(out, evidence)


@pytest.mark.parametrize('mode,tamper', [('proof', None), ('production', None),
                                       ('proof', 'bound'), ('proof', 'overlay')])
def test_d0_launch_receipts(staged, monkeypatch, mode, tamper):
    s = staged; out = s.root/'packet'
    js(s.root/'rv_media/RECEIPT.json', {})
    monkeypatch.setattr(R, 'runtime_check', lambda *a: {})
    monkeypatch.setattr(R, 'media_check', lambda *a: {})
    proof_calls = []
    monkeypatch.setattr(R, 'proof_check', lambda *a: proof_calls.append(a) or {'fixture': True})
    monkeypatch.setattr(R.shutil, 'disk_usage', lambda *a: NS(free=1000*1024**3))
    monkeypatch.setattr(R.T, 'environment', lambda *a, **k: {})
    monkeypatch.setattr(R.T, 'bwrap_evidence', lambda *a: {'path': '/usr/bin/bwrap'})
    monkeypatch.setattr(R.T, 'llguidance_evidence', lambda *a: {'enabled': True})
    monkeypatch.setattr(R.T, 'namespace', lambda *a, **k: ['bwrap', '--ro-bind', str(s.root/'trinity_runner_t6'), '/trinity-build'])
    def probe(*args, **kw):
        command = kw['namespace_factory'](s.root)
        assert command[-3:] == ['--ro-bind', str(out/D.OVERLAY), D.TARGET]
        return dict(versions=dict(vllm='0.32.0'), passed=True)
    monkeypatch.setattr(R.T, 'probe', probe)
    monkeypatch.setattr(R.T, 'sandbox_receipt', lambda command, *a: dict(namespace_argv=command))
    monkeypatch.setattr(R, 'card_admission', lambda gpu, path: js(path, {'fixture': True}))
    class Sampler:
        def __init__(self, *a):
            self.errors = []; self.stop = NS(set=lambda: None)
            self.thread = NS(start=lambda: None, join=lambda **k: None)
    monkeypatch.setattr(R.T, 'Sampler', Sampler)
    def run(argv, **kw):
        assert D.TARGET in argv[1]
        adapter = R.T.load(out/D.RECEIPT)
        config = R.T.load(out/'CONFIG.json')
        assert config['spec']['step'] == 100 and config['spec']['adapter_overlay'] == adapter
        (out/'llg_stub_calls.jsonl').write_text(json.dumps(dict(event='import', pid=1, module='llguidance'))+'\n')
        items = 10 if mode == 'proof' else 679
        js(out/'COMPLETE.json', dict(items=items, mode=mode))
        for arm, name in R.ARMS.items():
            js(out/'report'/(arm+'.json'), dict(items=items, groups={g: {} for g in R.GROUPS}))
            js(out/'a0/results/0'/name, {})
        if mode == 'proof': js(out/'PARITY.json', dict(items=20, processor_checked=True,
                                                      all_prompt_bytes_equal=True, prompt_pins_equal=True))
        pins = {'official_adapter.py': adapter['sha256']}
        verification = dict(status='VERIFIED', step=100, artifact={k: s.pin[k] for k in ('path', 'sha256')})
        js(out/'a0/request.json', dict(models=dict(cp1m200=s.pin),
            reader=dict(step=544 if tamper == 'bound' else 100, export_verification=verification, code_pins=pins)))
        js(out/'a0/CODE_PINS.json', pins)
        if tamper == 'overlay': (out/D.OVERLAY).write_bytes(b'changed')
        return 0
    monkeypatch.setattr(R.subprocess, 'call', run)
    args = NS(root=str(s.root), out=str(out), artifact=str(s.path), sha256=s.pin['sha256'], frames=32,
              command='rv-proof' if mode == 'proof' else 'rv-read', proof='fixture', gpu=0,
              token='d12345678', bwrap='/usr/bin/bwrap')
    if tamper:
        with pytest.raises(ValueError): R.launch(args)
        assert R.T.load(out/'EXIT.json')['status'] == 'FAILED'
        return
    assert R.launch(args)['status'] == 'COMPLETE'
    done = R.T.load(out/'EXIT.json'); R.verify_outputs(out, done)
    for name in (D.OVERLAY, D.RECEIPT, 'PROOF_SCOPE.json', 'a0/request.json'):
        assert done['output_pins'][name] == R.T.sha(out/name)
    assert R.T.load(out/'SANDBOX.json')['adapter_overlay'] == R.T.load(out/D.RECEIPT)
    scope = R.T.load(out/'PROOF_SCOPE.json')
    assert scope['model_independent'] and scope['model_dependent'] and scope['not_established']
    assert len(proof_calls) == (1 if mode == 'production' else 0)
    if mode == 'proof':
        # Exercise real proof admission and authenticated overlay checks.
        monkeypatch.undo()
        assert R.proof_check(out, s.root, s.pin, R.pins_check())['exit_sha256'] == R.T.sha(out/'EXIT.json')
        receipt = R.T.load(out/D.RECEIPT); receipt['sha256'] = '0'*64; js(out/D.RECEIPT, receipt)
        with pytest.raises(ValueError, match='pins'): R.proof_check(out, s.root, s.pin, R.pins_check())
