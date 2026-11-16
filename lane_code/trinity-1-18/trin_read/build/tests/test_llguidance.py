import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace as NS

import pytest
import trinity_read as T


@pytest.mark.parametrize('gpu', [False, True])
def test_overlay_is_pinned_and_bound_after_root(tmp_path, gpu):
    T.physical(tmp_path, T.LLG_TARGET).mkdir(parents=True)
    evidence = T.llguidance_evidence()
    assert evidence['verified'] and evidence['sha256'] == T.LLG_PINS
    argv = T.namespace(tmp_path, gpu=gpu)
    at = argv.index(str(T.LLG_STUB))
    assert argv[at-1:at+2] == ['--ro-bind', str(T.LLG_STUB), str(T.LLG_TARGET)]
    assert at > argv.index(str(tmp_path/'m/ap'))
    assert at > argv.index(str(tmp_path), argv.index(str(tmp_path/'m/ap')))
    disabled = T.namespace(tmp_path, gpu=gpu, llguidance_stub=False)
    assert str(T.LLG_STUB) not in disabled and str(T.LLG_TARGET) not in disabled
    if not gpu:
        assert '--dev-bind' not in argv and '--dev' in argv


def test_missing_overlay_target_refuses_without_creating_it(tmp_path):
    target = T.physical(tmp_path, T.LLG_TARGET)
    with pytest.raises(ValueError, match='requires an existing staged directory'):
        T.namespace(tmp_path)
    assert not target.exists()


@pytest.mark.parametrize('name', sorted(T.LLG_PINS))
def test_pin_mismatch_refuses_before_binding(tmp_path, monkeypatch, name):
    stub = tmp_path/'llguidance'; stub.mkdir()
    for filename in T.LLG_PINS:
        (stub/filename).write_bytes((T.LLG_STUB/filename).read_bytes())
    (stub/name).write_text('# mismatched stub\n')
    monkeypatch.setattr(T, 'LLG_STUB', stub)
    monkeypatch.setattr(T, 'bwrap_path', lambda *a: pytest.fail('Reached bwrap with bad stub'))
    with pytest.raises(ValueError, match='llguidance stub pin mismatch'):
        T.namespace(tmp_path)
    assert T.llguidance_evidence(False)['verified'] is False


def test_extra_stub_file_refuses(tmp_path, monkeypatch):
    stub = tmp_path/'llguidance'; stub.mkdir()
    for name in T.LLG_PINS:
        (stub/name).write_bytes((T.LLG_STUB/name).read_bytes())
    (stub/'extra.py').write_text('')
    monkeypatch.setattr(T, 'LLG_STUB', stub)
    with pytest.raises(ValueError, match='inventory differs'): T.namespace(tmp_path)


def test_config_audit_authenticates_host_overlay(tmp_path, monkeypatch):
    overlay = T.llguidance_evidence()
    T.dump(tmp_path/'runs/fixture/CONFIG.json', dict(spec=dict(llguidance_stub=overlay)))
    audit = T.config_audit(tmp_path)
    assert audit['passed']
    assert any(r['kind'] == 'pinned_overlay' for r in audit['findings'])
    monkeypatch.setattr(T, 'LLG_PINS', dict(T.LLG_PINS, **{'hf.py': '0'*64}))
    assert not T.config_audit(tmp_path)['passed']
    overlay['enabled'] = False
    T.dump(tmp_path/'runs/fixture/CONFIG.json', dict(spec=dict(llguidance_stub=overlay)))
    assert T.config_audit(tmp_path)['passed']


@pytest.mark.parametrize('command', ['proof', 'read', 'need', 'probe'])
@pytest.mark.parametrize('enabled', [True, False])
def test_cli_overlay_selection(tmp_path, monkeypatch, command, enabled):
    argv = ['trinity_read.py', command, '--root', str(tmp_path)]
    if not enabled: argv.append('--no-llguidance-stub')
    if command in ('proof', 'read'): argv += ['--gpu', '0', '--token', 'p12345678']
    if command in ('need', 'read'): argv += ['--family', 'main', '--first', '1', '--out', str(tmp_path/'packet')]
    if command == 'read': argv += ['--artifact', 'fixture', '--sha256', 'a'*64, '--step', '544']
    seen = []
    monkeypatch.setattr(sys, 'argv', argv)
    monkeypatch.setattr(T, 'launch', lambda args: seen.append(args.llguidance_stub))
    monkeypatch.setattr(T, 'need_command', lambda args: seen.append(args.llguidance_stub))
    monkeypatch.setattr(T, 'probe', lambda *args: seen.append(args[-1]))
    T.main()
    assert seen == [enabled]


@pytest.mark.parametrize('enabled', [True, False])
@pytest.mark.parametrize('code', [0, 7])
def test_need_evidence_on_success_or_failure(tmp_path, monkeypatch, enabled, code):
    monkeypatch.setattr(T, 'require_stage', lambda root: {})
    monkeypatch.setattr(T, 'install_runner', lambda root: None)
    monkeypatch.setattr(T, 'bwrap_evidence', lambda *a: dict(path='/usr/bin/bwrap'))
    def command(root, config, script, args, **kwargs):
        assert kwargs['llguidance_stub'] == enabled
        work = Path(args[1]).parent
        T.dump(work/'NEED.json', dict(need=[], ids=[]))
        return ['fixture']
    monkeypatch.setattr(T, 'ns_command', command)
    monkeypatch.setattr(T.subprocess, 'run', lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, code))
    if code:
        with pytest.raises(subprocess.CalledProcessError): T.cpu_need(tmp_path, 'main', llguidance_stub=enabled)
    else:
        assert T.cpu_need(tmp_path, 'main', llguidance_stub=enabled)['llguidance_stub'] == T.llguidance_evidence(enabled)
    work = next((tmp_path/'needs').iterdir())
    for name in ('COMMAND.json', 'EXIT.json'):
        assert T.load(work/name)['llguidance_stub'] == T.llguidance_evidence(enabled)


@pytest.mark.parametrize('state', [{}, {'status': 'partial'}, {'status': 'complete'}])
def test_probe_refuses_missing_uv_python_and_retains_report(tmp_path, monkeypatch, state):
    T.dump(tmp_path/'STAGING.json', dict(pieces={'runtime_0': state}))
    monkeypatch.setattr(T, 'capture_command', lambda argv: dict(argv=argv, stdout='', returncode=None))
    monkeypatch.setattr(T.subprocess, 'run', lambda *a, **k: pytest.fail('Ran without runtime_0'))
    with pytest.raises(ValueError, match='requires runtime_0 staged'):
        T.probe(tmp_path)
    report = T.load(next((tmp_path/'runs').glob('probe_*/PROBE.json')))
    assert not report['passed'] and report['returncode'] is None
    assert report['cryptography_imported'] is None


@pytest.mark.parametrize('enabled', [True, False])
@pytest.mark.parametrize('outcome', ['success', 'imports_failed', 'namespace_failed', 'timeout'])
def test_probe_namespace_and_evidence(tmp_path, monkeypatch, enabled, outcome):
    T.physical(tmp_path, T.LLG_TARGET).mkdir(parents=True)
    T.dump(tmp_path/'STAGING.json', dict(complete=False, pieces={'runtime_0': dict(status='complete')}))
    uv = tmp_path/'sj/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12'
    uv.parent.mkdir(parents=True); uv.write_bytes(b'fixture')
    python = T.physical(tmp_path, T.VLLM_ENV/'bin/python')
    python.parent.mkdir(parents=True); python.symlink_to(T.UV+'/bin/python3.12')
    monkeypatch.setattr(T, 'bwrap_evidence', lambda *a: dict(path='/usr/bin/bwrap'))
    custom_shm = tmp_path/'private-shm'
    imports = dict(versions=dict(vllm='0.32.0', torch='fixture', transformers='fixture'),
                   glibc='glibc 2.28', imports_passed=outcome == 'success', cryptography_imported=False,
                   structured_output=dict(stub_runtime_error=True))
    monkeypatch.setattr(T, 'capture_command', lambda argv: dict(argv=argv, stdout='', returncode=None))
    def run(command, **kwargs):
        assert '--dev-bind' not in command and '--dev' in command
        assert command == T.namespace(tmp_path, shm=custom_shm, llguidance_stub=enabled) + [str(T.VLLM_ENV/'bin/python'), '-I', '-B', '-c', T.PROBE_CODE]
        env = T.environment(tmp_path, shm=custom_shm)
        env['LLG_STUB_LOG'] = kwargs['env']['LLG_STUB_LOG']
        assert kwargs['env'] == env
        Path(env['LLG_STUB_LOG']).write_text(json.dumps(dict(event='import', module='llguidance', pid=1))+'\n'+json.dumps(dict(event='call', name='llguidance.grammar_from'))+'\n')
        assert kwargs['env']['CUDA_VISIBLE_DEVICES'] == ''
        if outcome == 'timeout': raise subprocess.TimeoutExpired(command, 120)
        stdout = '' if outcome == 'namespace_failed' else T.PROBE_MARKER+json.dumps(imports)+'\n'
        return subprocess.CompletedProcess(command, 0 if outcome == 'success' else 1, stdout, 'fixture stderr')
    monkeypatch.setattr(T.subprocess, 'run', run)
    if outcome == 'success':
        result = T.probe(tmp_path, shm=custom_shm, llguidance_stub=enabled)
        assert result['passed'] and result['glibc'] == 'glibc 2.28'
    else:
        with pytest.raises((RuntimeError, subprocess.TimeoutExpired)):
            T.probe(tmp_path, shm=custom_shm, llguidance_stub=enabled)
    result = T.load(next((tmp_path/'runs').glob('probe_*/PROBE.json')))
    assert result['llguidance_stub'] == T.llguidance_evidence(enabled)
    assert result['passed'] == (outcome == 'success')
    assert result['cryptography_imported'] is (None if outcome in ('namespace_failed', 'timeout') else False)


def test_probe_code_reports_actual_loaded_modules(tmp_path):
    # Exercise the import script without importing any real GPU libraries.
    code = '''
import sys, types
for name in ('vllm', 'torch', 'transformers', 'vllm.model_executor', 'vllm.model_executor.models',
             'vllm.v1', 'vllm.v1.engine', 'vllm.v1.engine.core', 'vllm.v1.worker', 'vllm.v1.worker.gpu_model_runner'):
    module = types.ModuleType(name); module.__version__ = 'fixture'; module.__path__ = []
    sys.modules[name] = module
sys.modules['vllm'].LLM = object
sys.modules['vllm.model_executor.models'].qwen3_5 = object
sys.modules['cryptography'] = types.ModuleType('cryptography')
'''
    result = subprocess.run([sys.executable, '-I', '-B', '-c', code+T.PROBE_CODE],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    assert result.returncode == 0, result.stderr
    record = json.loads(result.stdout.split(T.PROBE_MARKER)[1])
    assert record['imports_passed'] and record['cryptography_imported']
    assert record['versions']['vllm'] == 'fixture' and record['glibc'].startswith('glibc ')
