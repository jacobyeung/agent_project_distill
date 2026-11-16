"""Relocation fixtures retain every artifact and never use a GPU or real namespace."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import pytest
if __name__ == '__main__':
    sys.path.insert(0, sys.argv[1])
import trinity_read as T


def test_area_validation(tmp_path):
    directory = tmp_path/'area'; directory.mkdir()
    link = tmp_path/'link'; link.symlink_to(directory, target_is_directory=True)
    child = directory/'child'; child.mkdir()
    file = tmp_path/'file'; file.write_text('x')
    for value in ('', 'relative', str(tmp_path/'missing'), str(file), str(link),
                  str(link/'child'), str(directory/'..'/'area')):
        env = dict(os.environ, TRIN_AREA=value)
        result = subprocess.run([sys.executable, '-B', str(T.BUILD/'trinity_read.py'), '--help'],
                                env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert result.returncode != 0 and b'TRIN_AREA' in result.stderr
    env = dict(os.environ); env.pop('TRIN_AREA', None)
    result = subprocess.check_output([sys.executable, '-B', '-c',
        'import trinity_read as T; print(T.AREA)'], cwd=str(T.BUILD), env=env)
    assert result.decode().strip() == '/scratch/jjyeung/orch_n30/trin_read'


def test_relocated_stage_need_selfcheck(tmp_path):
    # /tmp also exercises milestone admission outside /scratch. Keep evidence.
    area = Path(tempfile.mkdtemp(prefix='trin-relocation-'))
    build = area/T.BUILD.name; build.mkdir()
    for source in T.BUILD.glob('*.py'):
        shutil.copy2(str(source), str(build/source.name))
    for name in ('e193_items.json', 'e193_contract.json'):
        if (T.BUILD/name).exists(): shutil.copy2(str(T.BUILD/name), str(build/name))
    shutil.copy2(str(T.BUILD/'tests/test_runner.py'), str(build/'fixture_stage.py'))
    for source in (T.BUILD/'llg_stub/llguidance').glob('*.py'):
        target = build/'llg_stub/llguidance'/source.name
        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(source.read_bytes())
    launcher = area/'kit_src/launcher'; launcher.mkdir(parents=True)
    for name in ('orchard_stage.py', 'chain_save.py'):
        (launcher/name).write_bytes((T.KIT/'launcher'/name).read_bytes())
    (area/'work').mkdir()
    env = dict(os.environ, TRIN_AREA=str(area), PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()), str(build)],
                            cwd=str(build), env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, universal_newlines=True)
    (tmp_path/'relocation.json').write_text(json.dumps(dict(area=str(area), stdout=result.stdout,
        stderr=result.stderr, returncode=result.returncode), indent=2))
    assert result.returncode == 0, result.stdout+'\n'+result.stderr
    report = json.loads((area/'work/SELF_CHECK.json').read_text())
    assert report['passed'] and report['portability']['passed']


def miniature():
    import fixture_stage
    assert T.BUILD == Path(sys.argv[1])
    assert T.AREA == T.BUILD.parent and T.DEFAULT_ROOT == T.AREA/'root'
    assert T.KIT == T.AREA/'kit_src'
    assert T.LLG_STUB == T.BUILD/'llg_stub/llguidance'
    with pytest.MonkeyPatch.context() as patch:
        fixture_stage.test_stage_piecewise_and_complete(T.AREA/'work', patch)
    (T.AREA/'work/root').rename(T.DEFAULT_ROOT)
    root = T.DEFAULT_ROOT
    cfg = T.load(root/'bootstrap/CONFIG.json')
    state = T.load(root/'STAGING.json')
    # Complete the stage fixture's tiny export and bootstrap verification records.
    review = root/'bootstrap/REVIEW.json'; review.write_text('{}')
    weight = T.LINEAGE/'m544/full_weights/full_weights.json'
    artifact = T.LINEAGE/'m544/artifact.json'
    index = T.physical(root, weight).parent/'index.json'
    T.dump(index, {})
    T.dump(T.physical(root, weight), dict(index=dict(name=index.name, bytes=index.stat().st_size,
        sha256=T.sha(index)), files=[]))
    T.dump(T.physical(root, artifact), dict(full_weights=dict(path=str(weight),
        sha256=T.sha(T.physical(root, weight)))))
    cfg.update(launcher_pins={}, launcher_review_pin=dict(sha256=T.sha(review)),
        spec=dict(artifact=dict(path=str(artifact)), interpreters=dict(p1cpu=sys.executable)))
    T.dump(root/'bootstrap/CONFIG.json', cfg)
    state['pieces']['export']['evidence'] = dict(artifact_sha256=T.sha(T.physical(root, artifact)),
        full_weights_sha256=T.sha(T.physical(root, weight)))
    T.dump(root/'STAGING.json', state)
    # This executable simulates bwrap only; stage, need receipts, and selfcheck run normally.
    bwrap = T.AREA/'work/fixture-bwrap'
    bwrap.write_text('#!'+sys.executable+'\n'+r"""
import json, os, pathlib, sys
if '--version' in sys.argv:
    print('fixture bwrap'); sys.exit(0)
assert '--unshare-net' in sys.argv
if '--input' in sys.argv:
    request_path = pathlib.Path(sys.argv[sys.argv.index('--input')+1])
    request = json.loads(request_path.read_text())
    area = pathlib.Path(os.environ['TRIN_AREA'])
    assert area.is_dir() and str(request_path).startswith(str(area/'root')+'/')
    root = area/'root'
    assert str(root) in sys.argv and '/trinity-build/namespace_worker.py' in sys.argv
    runner = next(root.glob('trinity_runner*p'))
    sys.path.insert(0, str(runner))
    import trinity_read as T
    assert T.AREA == area and T.DEFAULT_ROOT == root
    T.dump(pathlib.Path(request['work'])/'NEED.json', dict(need=[], ids=['fixture'], items=1,
        estimated_frame_bytes={}))
""")
    bwrap.chmod(0o700)
    # Also retain a separate legacy bundle; relocation must not overwrite it.
    legacy = 'trinity_runner_t6' if 't6' in T.BUILD.name else 'trinity_runner'
    target = root/legacy; target.mkdir()
    (target/'legacy.py').write_text('# immutable staged fixture\n')
    T.dump(target/'MANIFEST.json', {'legacy.py': dict(bytes=(target/'legacy.py').stat().st_size,
        sha256=T.sha(target/'legacy.py'))})
    before = T.disk_listing(target)
    T.physical(root, T.LLG_TARGET).mkdir(parents=True)
    assert T.cpu_need(root, 'main', first=1, bwrap=str(bwrap))['ids'] == ['fixture']
    from types import SimpleNamespace as NS
    T.need_command(NS(root=str(root), all=False, family='main', ids=None, first=1,
        out=str(T.AREA/'work/NEED.txt'), bwrap=str(bwrap), llguidance_stub=True, fixture=False))
    assert T.disk_listing(target) == before
    for path in (T.BUILD/'ok', root/'ok', T.AREA/'work/ok'):
        assert T.writable(path) == path
    with pytest.raises(ValueError): T.writable(T.AREA/'escape')
    (T.AREA/'work/escape').symlink_to(T.AREA.parent, target_is_directory=True)
    with pytest.raises(ValueError): T.writable(T.AREA/'work/escape/out')
    # Run the full existing checker with only the namespace process simulated.
    before_check = T.selfcheck(root, bwrap=str(bwrap))
    assert before_check['passed'], before_check
    T.dump(T.AREA/'work/SELF_CHECK.json', before_check)
    assert set(before_check['checks']) == {'bootstrap_payload', 'bwrap_hash', 'pieces',
                                          'runner', 'relocated_runner', 'cpu_namespace'}
    for directory, key in ((target, 'runner'), (root/(legacy+'p' if legacy.endswith('t6') else legacy+'_p'), 'relocated_runner')):
        manifest = T.load(directory/'MANIFEST.json')
        file = directory/next(iter(manifest))
        raw = file.read_bytes(); file.write_bytes(raw+b'changed')
        failed = T.selfcheck(root, bwrap=str(bwrap))
        assert not failed['passed'] and failed['checks'][key]['errors']
        file.write_bytes(raw)
    if 't6' in T.BUILD.name:
        import milestone as M
        source = T.AREA/'work/export.tar'; source.write_bytes(b'fixture')
        assert M.completed_local(source, tar=True) == source
        link = source.with_name('linked.tar'); link.symlink_to(source)
        with pytest.raises(ValueError): M.completed_local(link, tar=True)


if __name__ == '__main__':
    sys.path.insert(0, sys.argv[1])
    # The script imports T before main; the subprocess cwd/PYTHONPATH selects this build.
    miniature()
