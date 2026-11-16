import copy
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace as NS

import pytest
import trinity_read as T


@pytest.mark.parametrize('command', ['proof', 'read', 'need', 'selfcheck'])
def test_bwrap_option_help(command):
    result = subprocess.run([sys.executable, '-B', str(T.BUILD/'trinity_read.py'), command, '--help'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    assert result.returncode == 0 and '--bwrap' in result.stdout and '/usr/bin/bwrap' in result.stdout


def host_fixture(tmp_path):
    path = tmp_path/'host-bwrap'
    path.write_text('#!/bin/sh\nprintf "fixture bwrap 0.4.0\\n"\n')
    path.chmod(0o700)
    return path


def test_custom_executable_identity_and_namespace(tmp_path):
    T.physical(tmp_path, T.LLG_TARGET).mkdir(parents=True)
    path = host_fixture(tmp_path)
    evidence = T.bwrap_evidence(tmp_path, str(path))
    assert evidence == dict(path=str(path), sha256=T.sha(path), version='fixture bwrap 0.4.0\n', version_stderr='')
    assert T.namespace(tmp_path, bwrap=str(path))[0] == str(path)
    assert T.namespace(tmp_path)[0] == '/usr/bin/bwrap'


@pytest.mark.parametrize('alias', ['direct', 'symlink', 'hardlink', 'copy'])
def test_never_execute_pinned_bwrap(tmp_path, monkeypatch, alias):
    staged = tmp_path/'bwrap'; staged.write_bytes(b'pinned bytes')
    monkeypatch.setattr(T, 'PINNED_BWRAP_SHA256', T.sha(staged))
    path = staged
    if alias != 'direct':
        path = tmp_path/alias
        if alias == 'symlink': path.symlink_to(staged)
        elif alias == 'hardlink': T.os.link(str(staged), str(path))
        else: path.write_bytes(staged.read_bytes())
    monkeypatch.setattr(T.subprocess, 'run', lambda *a, **k: pytest.fail('Pinned binary executed'))
    with pytest.raises(ValueError, match='bwrap'): T.bwrap_evidence(tmp_path, path)


@pytest.mark.parametrize('code', [0, 7])
def test_need_records_selected_bwrap_even_on_failure(tmp_path, monkeypatch, code):
    path = host_fixture(tmp_path); real_run = subprocess.run
    monkeypatch.setattr(T, 'require_stage', lambda root: {})
    monkeypatch.setattr(T, 'install_runner', lambda root: None)
    def command(root, config, script, args, **kwargs):
        assert kwargs['bwrap'] == str(path)
        work = Path(args[1]).parent
        T.dump(work/'NEED.json', dict(need=[], ids=[]))
        return [str(path), '--fixture']
    monkeypatch.setattr(T, 'ns_command', command)
    def run(cmd, **kwargs):
        if cmd[-1] == '--version': return real_run(cmd, **kwargs)
        return subprocess.CompletedProcess(cmd, code)
    monkeypatch.setattr(T.subprocess, 'run', run)
    if code:
        with pytest.raises(subprocess.CalledProcessError): T.cpu_need(tmp_path, 'main', bwrap=str(path))
    else:
        assert T.cpu_need(tmp_path, 'main', bwrap=str(path))['bwrap']['path'] == str(path)
    work = next((tmp_path/'needs').iterdir())
    command = T.load(work/'COMMAND.json'); exit_info = T.load(work/'EXIT.json')
    assert exit_info['returncode'] == code
    assert command['bwrap'] == exit_info['bwrap']
    assert command['bwrap']['sha256'] == T.sha(path)


def accepted_fixture(tmp_path):
    raw = (T.DEFAULT_ROOT/'bootstrap/CONFIG.json').read_bytes()
    assert T.sha(T.DEFAULT_ROOT/'bootstrap/CONFIG.json') == T.ACCEPTED_CONFIG_SHA256
    (tmp_path/'bootstrap').mkdir()
    (tmp_path/'bootstrap/CONFIG.json').write_bytes(raw)
    return T.load(tmp_path/'bootstrap/CONFIG.json')


def test_accepted_config_evidence_is_informational(tmp_path):
    accepted_fixture(tmp_path)
    result = T.config_audit(tmp_path)
    assert result['passed'] and result['pinned_template_authenticated']
    evidence = [r for r in result['findings'] if r['kind'] == 'pinned_evidence']
    assert any(r['value'] == 'orchard-login-001' for r in evidence)
    assert any(r['value'].startswith('/project/') for r in evidence)
    assert any(len(r['value']) == 64 for r in evidence)
    assert all(not r['fails'] for r in evidence)
    active = next(r for r in result['findings'] if r['field'] == '$.spec.artifact.path')
    assert active['kind'] == 'namespace_alias' and active['mapped_path'].startswith(str(tmp_path))


@pytest.mark.parametrize('field,value', [('package', '/data3/escape/package'),
                                        ('run', '/home/escape/job'),
                                        ('package', str(T.SJ/'../../data3/escape'))])
def test_active_paths_in_run_config_fail(tmp_path, field, value):
    config = accepted_fixture(tmp_path)
    config['spec'][field] = value
    T.dump(tmp_path/'runs/token/CONFIG.json', config)
    result = T.config_audit(tmp_path)
    assert not result['passed']
    assert any(r.get('field') == '$.spec.'+field and r['fails'] for r in result['findings'])


def test_namespace_alias_cannot_hide_symlink_escape(tmp_path):
    accepted_fixture(tmp_path)
    (tmp_path/'sj').symlink_to('/data3/escape')
    result = T.config_audit(tmp_path)
    assert not result['passed']
    assert any(r.get('field') == '$.spec.package' and r['fails'] for r in result['findings'])


def test_modified_bootstrap_is_not_accepted_evidence(tmp_path):
    config = accepted_fixture(tmp_path)
    config['assets']['observed_host'] = 'orchard-login-999'
    T.dump(tmp_path/'bootstrap/CONFIG.json', config)
    result = T.config_audit(tmp_path)
    assert not result['pinned_template_authenticated']
    assert not any(r['kind'] == 'pinned_evidence' for r in result['findings'])


def test_need_cli_passes_bwrap_to_every_family(tmp_path, monkeypatch):
    calls = []
    def need(*args):
        calls.append(args)
        return dict(need=[], items=0, estimated_frame_bytes={})
    monkeypatch.setattr(T, 'cpu_need', need)
    T.need_command(NS(root=str(tmp_path), all=True, family=None, ids=None, first=None,
                      out=str(tmp_path/'need.txt'), bwrap='/usr/bin/custom-bwrap'))
    assert len(calls) == 3 and all(c[-2:] == ('/usr/bin/custom-bwrap', True) for c in calls)
