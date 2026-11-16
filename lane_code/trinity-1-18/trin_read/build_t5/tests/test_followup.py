import copy
import os
from pathlib import Path
import signal
import subprocess
import sys
from types import SimpleNamespace as NS

import pytest
import trinity_read as T
import compare_tokens as C


def test_private_shm_and_all_caches(tmp_path):
    T.physical(tmp_path, T.LLG_TARGET).mkdir(parents=True)
    custom = tmp_path/'private/shm'
    command = T.namespace(tmp_path, gpu=True, shm=custom)
    device = command.index('--dev-bind')
    assert command[device:device+6] == ['--dev-bind', '/dev', '/dev', '--bind', str(custom), '/dev/shm']
    assert custom.is_dir()
    assert str(T.KIT) not in command and str(T.BUILD) not in command
    assert str(tmp_path/'trinity_runner_t5') in command
    env = T.environment(tmp_path, '0', 'p12345678', custom)
    for key in ('TMPDIR', 'HOME', 'XDG_CACHE_HOME', 'HF_HOME', 'TRITON_CACHE_DIR', 'TORCHINDUCTOR_CACHE_DIR', 'VLLM_CACHE_ROOT'):
        assert T.inside(Path(env[key]), tmp_path) and Path(env[key]).is_dir()
    assert env['CUDA_VISIBLE_DEVICES'] == '0'


def test_host_shm_is_shallow_and_does_not_follow_links(tmp_path):
    (tmp_path/'sub').mkdir(); (tmp_path/'sub/hidden').write_bytes(b'abc')
    (tmp_path/'link').symlink_to(tmp_path/'sub/hidden')
    rows = T.host_shm_ours(tmp_path)
    assert {Path(r['path']).name for r in rows} == {'sub', 'link'}
    assert all(r['bytes'] >= 0 for r in rows)


def test_host_shm_filters_uid(tmp_path, monkeypatch):
    (tmp_path/'file').write_bytes(b'a')
    monkeypatch.setattr(T.os, 'getuid', lambda: -1)
    assert T.host_shm_ours(tmp_path) == []


@pytest.mark.parametrize('pattern', ['/data3/x/*.stop', '/home/user/stop', '/tmp/*/*.stop', '**/*.stop'])
def test_yield_glob_rejects_shared_or_recursive_search(pattern):
    with pytest.raises(ValueError): T.yield_pattern(pattern)


def test_yield_glob_local(tmp_path):
    assert T.yield_pattern(str(tmp_path/'*.stop')) == str(tmp_path/'*.stop')
    assert T.yield_pattern(None) is None


def test_process_group_escalation_only_targets_child(monkeypatch):
    signals = []; waited = []
    child = NS(pid=os.getpgrp()+100000, wait=lambda: waited.append(True) or -9)
    monkeypatch.setattr(T.os, 'killpg', lambda group, sig: signals.append((group, sig)))
    assert T.stop_group(child, grace=0) == -9
    assert signals == [(child.pid, signal.SIGTERM), (child.pid, signal.SIGKILL)]
    assert waited == [True]
    with pytest.raises(RuntimeError): T.stop_group(NS(pid=os.getpgrp()), grace=0)


def test_process_group_grace_waits_even_if_leader_exits(monkeypatch):
    events = []
    child = NS(pid=os.getpgrp()+100000, wait=lambda: events.append('reap') or 0)
    monkeypatch.setattr(T.time, 'sleep', lambda seconds: events.append(('wait', seconds)))
    monkeypatch.setattr(T.os, 'killpg', lambda group, sig: events.append(sig))
    T.stop_group(child)
    assert events == [signal.SIGTERM, ('wait', 60), signal.SIGKILL, 'reap']


def test_reader_polls_30_seconds_and_yields(tmp_path, monkeypatch):
    flag = tmp_path/'please.stop'; waits = []; launches = []; stopped = []
    class Child:
        pid = 1234567
        def wait(self, timeout=None):
            waits.append(timeout); flag.write_text('yield')
            raise subprocess.TimeoutExpired('fixture', timeout)
    def popen(*args, **kwargs):
        launches.append(kwargs); return Child()
    monkeypatch.setattr(T.subprocess, 'Popen', popen)
    monkeypatch.setattr(T, 'stop_group', lambda child: stopped.append(child.pid))
    code, event = T.run_reader(['fixture'], {}, tmp_path, None, str(tmp_path/'*.stop'))
    assert code != 0 and event['matched_file'] == str(flag)
    assert event['utc'].endswith('Z') and event['time'] > 0
    assert waits == [30] and stopped == [Child.pid]
    assert launches[0]['start_new_session'] is True


def test_reader_normal_cpu_child(tmp_path):
    with (tmp_path/'log').open('wb') as log:
        code, event = T.run_reader([sys.executable, '-B', '-c', 'print("ok")'], {}, tmp_path, log)
    assert code == 0 and event is None and (tmp_path/'log').read_text() == 'ok\n'


def test_disk_inventory_never_follows_symlinks(tmp_path):
    out = tmp_path/'run'; (out/'direct/main/models/base').mkdir(parents=True)
    model = out/'direct/main/models/base/weights'; model.write_bytes(b'12345')
    (out/'link').symlink_to(tmp_path, target_is_directory=True)
    rows = T.disk_listing(out)
    assert next(r for r in rows if r['path'] == str(model))['bytes'] == 5
    assert next(r for r in rows if r['path'] == str(out/'link'))['kind'] == 'symlink'
    assert len(rows) == 6


def test_cheap_hash_checks_small_files_and_large_sizes(tmp_path):
    small = tmp_path/'small'; small.write_bytes(b'abc')
    big = tmp_path/'large'; big.write_bytes(b'x'*(T.SMALL_FILE_BYTES+1))
    rows = {p.name: dict(bytes=p.stat().st_size, sha256=T.sha(p)) for p in (small,big)}
    good = T.cheap_verify(tmp_path, rows)
    assert good == dict(files=2, hashed=1, size_only=1, errors=[])
    small.write_bytes(b'xyz'); big.write_bytes(b'x')
    bad = T.cheap_verify(tmp_path, rows)
    assert len(bad['errors']) == 2


def test_cheap_verify_refuses_escape(tmp_path):
    assert T.cheap_verify(tmp_path, {'../escape': dict(bytes=0, sha256='0'*64)})['errors']


def test_config_audit_exposes_pinned_host_and_external_paths(tmp_path):
    T.dump(tmp_path/'bootstrap/CONFIG.json', dict(assets=dict(observed_host='orchard-login-001', archive='/project/legacy.tar'),
                                                local=str(tmp_path/'cache'), logical=str(T.AP/'model'), system='/usr/bin/python3'))
    audit = T.config_audit(tmp_path)
    assert not audit['passed']
    assert {r['kind'] for r in audit['findings']} == {'metadata','external_path','namespace_alias','allowed_path'}


def test_root_carries_wrapper_without_kit(tmp_path):
    T.install_runner(tmp_path)
    manifest = T.load(tmp_path/'trinity_runner_t5/MANIFEST.json')
    assert set(manifest) == {'trinity_read.py','namespace_worker.py','compare_tokens.py','paired_read.py','e193_contract.json','milestone.py','e193_items.json'}
    assert T.cheap_verify(tmp_path/'trinity_runner_t5', manifest)['errors'] == []
    T.install_runner(tmp_path)
    result = subprocess.run(['/usr/bin/python3','-B',str(tmp_path/'trinity_runner_t5/trinity_read.py'),'selfcheck','--help'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 0
    T.dump(tmp_path/'trinity_runner_t5/MANIFEST.json', {})
    with pytest.raises(ValueError, match='manifest differs'): T.install_runner(tmp_path)


def test_partial_selfcheck_reports_unverifiable_and_does_not_write(tmp_path, monkeypatch):
    T.dump(tmp_path/'STAGING.json', dict(complete=False,pieces={'a0':dict(status='complete',evidence=dict(sha256='x'))}))
    T.dump(tmp_path/'bootstrap/CONFIG.json', {})
    before = T.disk_listing(tmp_path)
    commands = []
    def run(cmd, **kwargs):
        commands.append(cmd); return NS(returncode=0, stderr='', stdout='bubblewrap 0.4.0\n')
    monkeypatch.setattr(T.subprocess, 'run', run)
    result = T.selfcheck(tmp_path)
    assert not result['passed'] and 'a0:' in result['unverifiable'][0]
    assert result['checks']['cpu_namespace']['returncode'] == 0
    assert commands[0] == ['/usr/bin/bwrap', '--version']
    assert commands[1][-1] == '/bin/true'
    at = commands[1].index('--dev-bind')
    assert commands[1][at+1:at+3] == ['/dev/null', '/dev/null']
    assert T.disk_listing(tmp_path) == before


@pytest.mark.parametrize('command', ['read','proof'])
@pytest.mark.parametrize('custom_bwrap', [False, True])
@pytest.mark.parametrize('enabled', [True, False])
def test_launch_yield_writes_exit_proof_and_model_inventory(tmp_path, monkeypatch, command, custom_bwrap, enabled):
    import milestone as M
    monkeypatch.setattr(M, 'inventory', lambda: {'main': {'items': {'one': 'fixture'}}})
    bwrap = '/usr/bin/bwrap'
    if custom_bwrap:
        selected = tmp_path/'selected-bwrap'
        selected.write_text('#!/bin/sh\nprintf "fixture bwrap 0.4.0\\n"\n')
        selected.chmod(0o700)
        bwrap = str(selected)
    monkeypatch.setattr(T, 'probe', lambda *a: dict(passed=True, versions={'python':'fixture'}))
    monkeypatch.setattr(T, 'capture_command', lambda argv: dict(argv=argv, stdout='', returncode=None))
    cfg = dict(spec=dict(package=str(T.SJ/'pkg'),models={}), output='old')
    monkeypatch.setattr(T, 'require_stage', lambda root: copy.deepcopy(cfg))
    def need(*args):
        assert args[-2:] == (bwrap, enabled)
        return dict(ids=['one'],need=[])
    monkeypatch.setattr(T, 'cpu_need', need)
    monkeypatch.setattr(T, 'read_space', lambda *a: 0)
    monkeypatch.setattr(T, 'check_card', lambda *a: {})
    def namespace(*args, **kwargs):
        assert kwargs['bwrap'] == bwrap
        assert kwargs['llguidance_stub'] == enabled
        return [bwrap, 'fake-reader']
    monkeypatch.setattr(T, 'ns_command', namespace)
    record = dict(example_id='one', token_ids=[1], raw_generation='A', extracted_answer='A', score=1.0)
    T.dump(tmp_path/'sj/pkg/parity/DEV20.json', dict(ids=['one'],need=[],arms={arm:[record] for arm in C.ARMS}))
    out = tmp_path/'runs/p12345678' if command == 'proof' else tmp_path/'packet'
    models = out/'b0/d0/models' if command == 'proof' else out/'direct/main/models'
    def reader(*args):
        (models/'base').mkdir(parents=True); (models/'base/weights').write_bytes(b'123')
        return 75, dict(matched_file=str(tmp_path/'yield'),time=1,utc='fixture')
    monkeypatch.setattr(T, 'run_reader', reader)
    monkeypatch.setattr(T, 'host_shm_ours', lambda: [])
    class Sampler:
        def __init__(self, *args):
            self.thread = NS(start=lambda: None, join=lambda **kw: None)
            self.stop = NS(set=lambda: None); self.errors = []
    monkeypatch.setattr(T, 'Sampler', Sampler)
    args = NS(root=str(tmp_path),command=command,token='p12345678',gpu='0',shm=None,yield_glob=None,
              family='main',first=1,ids=None,out=str(out),artifact=str(T.LINEAGE/'m544/artifact.json'),sha256='a'*64,step=544,bwrap=bwrap,
              llguidance_stub=enabled)
    with pytest.raises(RuntimeError, match='Run or memory sampler failed'): T.launch(args)
    exit_info = T.load(out/'EXIT.json'); yielded = T.load(out/'YIELD.json')
    assert exit_info['yielded'] and exit_info['returncode'] == 75
    assert exit_info['host_dev_shm_ours'] == exit_info['host_dev_shm_ours_before'] == []
    assert exit_info['bwrap'] == T.load(out/'COMMAND.json')['bwrap']
    overlay = T.llguidance_evidence(enabled)
    assert exit_info['llguidance_stub'] == T.load(out/'COMMAND.json')['llguidance_stub'] == overlay
    assert T.load(out/'SPEC.json')['llguidance_stub'] == overlay
    assert T.load(out/'CONFIG.json')['spec']['llguidance_stub'] == overlay
    assert exit_info['bwrap']['path'] == bwrap
    assert exit_info['bwrap']['sha256'] == T.sha(bwrap)
    assert exit_info['bwrap']['version'] == ('fixture bwrap 0.4.0\n' if custom_bwrap else 'bubblewrap 0.4.0\n')
    assert any(row['bytes'] == 3 for row in yielded['model_copies'])
    assert (out/'HOST_SHM_BEFORE.json').exists()
    if command == 'proof':
        proof = T.load(out/'PROOF.json')
        assert not proof['passed'] and proof['host_dev_shm_ours'] == []
        assert proof['bwrap'] == exit_info['bwrap']
        assert proof['llguidance_stub'] == overlay


def test_real_child_group_handles_term(tmp_path):
    script = 'import signal,sys; signal.signal(signal.SIGTERM, lambda *a: sys.exit(0)); print("ready",flush=True); signal.pause()'
    child = subprocess.Popen([sys.executable, '-B', '-c', script], stdout=subprocess.PIPE,
                             universal_newlines=True, start_new_session=True)
    assert child.stdout.readline().strip() == 'ready'
    assert os.getpgid(child.pid) == child.pid != os.getpgrp()
    assert T.stop_group(child, grace=0.1) == 0


def test_real_child_group_escalates_ignored_term(tmp_path):
    script = 'import signal; signal.signal(signal.SIGTERM, signal.SIG_IGN); print("ready",flush=True); signal.pause()'
    child = subprocess.Popen([sys.executable, '-B', '-c', script], stdout=subprocess.PIPE,
                             universal_newlines=True, start_new_session=True)
    assert child.stdout.readline().strip() == 'ready'
    assert T.stop_group(child, grace=0.1) == -signal.SIGKILL


def test_camera_receipt_inventory_from_authenticated_tar(tmp_path):
    import hashlib
    import io
    import tarfile
    source = tmp_path/'camera.tar'
    with tarfile.open(str(source), 'w') as archive:
        info = tarfile.TarInfo('sj/camera.json'); info.size = 2
        archive.addfile(info, io.BytesIO(b'{}'))
    pin = dict(bytes=source.stat().st_size, sha256=T.sha(source))
    rows = T.small_archive_inventory(source, pin)
    assert rows == {'sj/camera.json': dict(bytes=2, sha256=hashlib.sha256(b'{}').hexdigest())}
    pin['sha256'] = '0'*64
    with pytest.raises(ValueError): T.small_archive_inventory(source, pin)
