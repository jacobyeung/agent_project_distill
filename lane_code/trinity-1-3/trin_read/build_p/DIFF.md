# Relocatable lane changes

All changes are **PATH/ENV**. No BEYOND change is required.

| File or artifact | Class | Change |
|---|---|---|
| `trinity_read.py`: `lane_area`, `AREA`, `DEFAULT_ROOT`, `KIT`, `REFERENCE` | PATH/ENV | Validate `TRIN_AREA`; keep its default; use the local kit reference when the variable is set. |
| `trinity_read.py`: `writable`, stub path, environment | PATH/ENV | Allow the active build, lane root and work directory; locate the stub beside the build; carry `TRIN_AREA` into workers. |
| `trinity_read.py`: runner installation, bind source, selfcheck | PATH/ENV | Give the relocated bundle a distinct directory; preserve and verify existing staged bytes; verify both bundles when present. |
| `tests/test_followup.py` | PATH/ENV | Expect the relocated runner directory. |
| `tests/test_relocation.py` | PATH/ENV | Exercise path validation, stage/need/selfcheck in a miniature `/tmp` lane, namespace environment, write confinement and bundle integrity. |
| `REPORT_P.md`, `SPACE_P.json`, test logs, miniature test artifacts | PATH/ENV | Record relocation evidence and unchanged space accounting. |
| `audit_relocation.py`, `PATH_AUDIT_P.json` | PATH/ENV | Audit bounded source and staged receipt paths without reading large payloads. |

`namespace_worker.py` and `compare_tokens.py` are byte-identical to their source builds. Model-copy policy, reserve formula, free-space floor, selection, scoring, token comparison and payload bytes are unchanged.

```diff
--- build/trinity_read.py
+++ build_p/trinity_read.py
@@ -28,10 +28,21 @@
 
 sys.dont_write_bytecode = True
 BUILD = Path(__file__).resolve().parent
-AREA = Path('/scratch/jjyeung/orch_n30/trin_read')
+def lane_area():
+    """Accept an existing absolute lane directory without symlink components."""
+    value = os.environ.get('TRIN_AREA', '/scratch/jjyeung/orch_n30/trin_read')
+    path = Path(value)
+    if (not path.is_absolute() or '..' in path.parts or not path.is_dir()
+            or any(p.is_symlink() for p in (path,)+tuple(path.parents))):
+        raise ValueError('TRIN_AREA must be an absolute existing directory without symlink components')
+    return path
+
+
+AREA = lane_area()
 DEFAULT_ROOT = AREA/'root'
 KIT = Path('/trinity-kit') if Path('/trinity-kit').exists() else AREA/'kit_src'
-REFERENCE = Path('/scratch/jjyeung/orch_n30/evalx27/work/kit/build/pb59bef09f3')
+REFERENCE = (KIT/'build/pb59bef09f3' if 'TRIN_AREA' in os.environ else
+             Path('/scratch/jjyeung/orch_n30/evalx27/work/kit/build/pb59bef09f3'))
 STORE = '/project/community/jjyeung/cp4tk_fr/k6tk'
 VNICE = '/data3/shared/scripts/vnice/vnice.sh'
 DEFAULT_BWRAP = '/usr/bin/bwrap'
@@ -43,7 +54,7 @@
 FSW = Path('/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung')
 AP = Path('/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap')
 VLLM_ENV = AP/'19252904/e'
-LLG_STUB = AREA/'build/llg_stub/llguidance'
+LLG_STUB = BUILD/'llg_stub/llguidance'
 LLG_TARGET = VLLM_ENV/'lib/python3.12/site-packages/llguidance'
 LLG_PINS = {
     '__init__.py': '01fc27773baceee9eb87ff76cec70d8ce761a8ddef6c73055224e77a70023572',
@@ -64,8 +75,8 @@
 
 def writable(path):
     path = Path(path).resolve()
-    if not any(inside(path, p) for p in (AREA/'build', DEFAULT_ROOT)):
-        raise ValueError('Writes must remain under build/ or root/: '+str(path))
+    if not any(inside(path, p) for p in (BUILD, DEFAULT_ROOT, AREA/'work')):
+        raise ValueError('Writes must remain under this build, root/ or work/: '+str(path))
     return path
 
 
@@ -83,7 +94,7 @@
 
 def install_runner(root):
     """Carry the three wrapper modules with a root-only copy; never alter kit bytes."""
-    destination = root/'trinity_runner'
+    destination = root/'trinity_runner_p'
     rows = {}
     for name in ('trinity_read.py', 'namespace_worker.py', 'compare_tokens.py'):
         source = BUILD/name; target = destination/name
@@ -489,7 +500,7 @@
              '--bind', str(root/'fsw'), str(FSW), '--dir', '/lustre',
              '--bind', str(root/'m/ap'), str(AP),
              '--ro-bind', str(root/'sj/uv-python/cpython-3.12.13-linux-x86_64-gnu'), UV,
-             '--bind', str(root), str(root), '--ro-bind', str(root/'trinity_runner'), '/trinity-build',
+             '--bind', str(root), str(root), '--ro-bind', str(root/'trinity_runner_p'), '/trinity-build',
              '--ro-bind', str(root/'k6tk'), STORE,
              '--dir', '/home/jjyeung', '--die-with-parent', '--chdir', str(root)]
     if overlay['enabled']:
@@ -501,7 +512,7 @@
     shm_directory(root, shm)
     for name in ('cache', 'temp', 'home', 'k6tk', 'cache/hf', 'cache/triton', 'cache/torchinductor', 'cache/vllm'):
         (root/name).mkdir(parents=True, exist_ok=True)
-    return dict(PATH='/usr/local/bin:/usr/bin:/bin', USER=os.environ.get('USER', 'jjyeung'),
+    return dict(TRIN_AREA=str(AREA), PATH='/usr/local/bin:/usr/bin:/bin', USER=os.environ.get('USER', 'jjyeung'),
                 SLURM_JOB_ID=token, CUDA_VISIBLE_DEVICES=gpu, HOME=str(root/'home'), TMPDIR=str(root/'temp'),
                 XDG_CACHE_HOME=str(root/'cache'), HF_HOME=str(root/'cache/hf'),
                 TRITON_CACHE_DIR=str(root/'cache/triton'), TORCHINDUCTOR_CACHE_DIR=str(root/'cache/torchinductor'),
@@ -880,10 +891,12 @@
             unverifiable.append(name+': STAGING.json has no extracted-file inventory')
         rows.update(current)
     checks['pieces'] = cheap_verify(root, rows)
-    manifest = root/'trinity_runner/MANIFEST.json'
-    if manifest.exists():
-        checks['runner'] = cheap_verify(root, {'trinity_runner/'+p:pin for p,pin in load(manifest).items()})
-    else: unverifiable.append('trinity_runner: not installed; run stage from build before copying')
+    runner_dirs = [name for name in ('trinity_runner', 'trinity_runner_p') if (root/name/'MANIFEST.json').exists()]
+    for index, name in enumerate(runner_dirs):
+        manifest = root/name/'MANIFEST.json'
+        checks['runner' if index == 0 else 'relocated_runner'] = cheap_verify(
+            root, {name+'/'+p:pin for p,pin in load(manifest).items()})
+    if not runner_dirs: unverifiable.append('trinity_runner_p: not installed; run stage from the relocated build before copying')
     # This probe needs no staged interpreter, model, frame, cache, or GPU device.
     executed = bwrap_evidence(root, bwrap)
     command = [executed['path'], '--unshare-net', '--dev', '/dev', '--dev-bind', '/dev/null', '/dev/null',
@@ -901,7 +914,7 @@
         checks['cpu_namespace'] = dict(returncode=None, error=str(error), command=command, bwrap=executed)
     audit = config_audit(root)
     passed = (state.get('complete', False) and not missing and not unverifiable and not checks['pieces']['errors']
-              and not checks.get('runner', {}).get('errors') and checks['cpu_namespace']['returncode'] == 0
+              and not checks.get('runner', {}).get('errors') and not checks.get('relocated_runner', {}).get('errors') and checks['cpu_namespace']['returncode'] == 0
               and all(c.get('passed', True) for c in checks.values()) and audit['passed'])
     return dict(passed=bool(passed), stage_complete=state.get('complete', False), checks=checks,
                 unverifiable=unverifiable, missing_pieces=missing, portability=audit, small_file_bytes=SMALL_FILE_BYTES,
--- build/tests/test_followup.py
+++ build_p/tests/test_followup.py
@@ -19,7 +19,7 @@
     assert command[device:device+6] == ['--dev-bind', '/dev', '/dev', '--bind', str(custom), '/dev/shm']
     assert custom.is_dir()
     assert str(T.KIT) not in command and str(T.BUILD) not in command
-    assert str(tmp_path/'trinity_runner') in command
+    assert str(tmp_path/'trinity_runner_p') in command
     env = T.environment(tmp_path, '0', 'p12345678', custom)
     for key in ('TMPDIR', 'HOME', 'XDG_CACHE_HOME', 'HF_HOME', 'TRITON_CACHE_DIR', 'TORCHINDUCTOR_CACHE_DIR', 'VLLM_CACHE_ROOT'):
         assert T.inside(Path(env[key]), tmp_path) and Path(env[key]).is_dir()
@@ -128,14 +128,14 @@
 
 def test_root_carries_wrapper_without_kit(tmp_path):
     T.install_runner(tmp_path)
-    manifest = T.load(tmp_path/'trinity_runner/MANIFEST.json')
+    manifest = T.load(tmp_path/'trinity_runner_p/MANIFEST.json')
     assert set(manifest) == {'trinity_read.py','namespace_worker.py','compare_tokens.py'}
-    assert T.cheap_verify(tmp_path/'trinity_runner', manifest)['errors'] == []
+    assert T.cheap_verify(tmp_path/'trinity_runner_p', manifest)['errors'] == []
     T.install_runner(tmp_path)
-    result = subprocess.run(['/usr/bin/python3','-B',str(tmp_path/'trinity_runner/trinity_read.py'),'selfcheck','--help'],
+    result = subprocess.run(['/usr/bin/python3','-B',str(tmp_path/'trinity_runner_p/trinity_read.py'),'selfcheck','--help'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
     assert result.returncode == 0
-    T.dump(tmp_path/'trinity_runner/MANIFEST.json', {})
+    T.dump(tmp_path/'trinity_runner_p/MANIFEST.json', {})
     with pytest.raises(ValueError, match='manifest differs'): T.install_runner(tmp_path)
 
 
--- build/tests/test_relocation.py
+++ build_p/tests/test_relocation.py
@@ -0,0 +1,152 @@
+"""Relocation fixtures retain every artifact and never use a GPU or real namespace."""
+import json
+import os
+from pathlib import Path
+import shutil
+import subprocess
+import sys
+import tempfile
+
+import pytest
+if __name__ == '__main__':
+    sys.path.insert(0, sys.argv[1])
+import trinity_read as T
+
+
+def test_area_validation(tmp_path):
+    directory = tmp_path/'area'; directory.mkdir()
+    link = tmp_path/'link'; link.symlink_to(directory, target_is_directory=True)
+    child = directory/'child'; child.mkdir()
+    file = tmp_path/'file'; file.write_text('x')
+    for value in ('', 'relative', str(tmp_path/'missing'), str(file), str(link),
+                  str(link/'child'), str(directory/'..'/'area')):
+        env = dict(os.environ, TRIN_AREA=value)
+        result = subprocess.run([sys.executable, '-B', str(T.BUILD/'trinity_read.py'), '--help'],
+                                env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
+        assert result.returncode != 0 and b'TRIN_AREA' in result.stderr
+    env = dict(os.environ); env.pop('TRIN_AREA', None)
+    result = subprocess.check_output([sys.executable, '-B', '-c',
+        'import trinity_read as T; print(T.AREA)'], cwd=str(T.BUILD), env=env)
+    assert result.decode().strip() == '/scratch/jjyeung/orch_n30/trin_read'
+
+
+def test_relocated_stage_need_selfcheck(tmp_path):
+    # /tmp also exercises milestone admission outside /scratch. Keep evidence.
+    area = Path(tempfile.mkdtemp(prefix='trin-relocation-'))
+    build = area/T.BUILD.name; build.mkdir()
+    for source in T.BUILD.glob('*.py'):
+        shutil.copy2(str(source), str(build/source.name))
+    for name in ('e193_items.json', 'e193_contract.json'):
+        if (T.BUILD/name).exists(): shutil.copy2(str(T.BUILD/name), str(build/name))
+    shutil.copy2(str(T.BUILD/'tests/test_runner.py'), str(build/'fixture_stage.py'))
+    for source in (T.BUILD/'llg_stub/llguidance').glob('*.py'):
+        target = build/'llg_stub/llguidance'/source.name
+        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(source.read_bytes())
+    launcher = area/'kit_src/launcher'; launcher.mkdir(parents=True)
+    for name in ('orchard_stage.py', 'chain_save.py'):
+        (launcher/name).write_bytes((T.KIT/'launcher'/name).read_bytes())
+    (area/'work').mkdir()
+    env = dict(os.environ, TRIN_AREA=str(area), PYTHONDONTWRITEBYTECODE='1')
+    result = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()), str(build)],
+                            cwd=str(build), env=env, stdout=subprocess.PIPE,
+                            stderr=subprocess.PIPE, universal_newlines=True)
+    (tmp_path/'relocation.json').write_text(json.dumps(dict(area=str(area), stdout=result.stdout,
+        stderr=result.stderr, returncode=result.returncode), indent=2))
+    assert result.returncode == 0, result.stdout+'\n'+result.stderr
+    report = json.loads((area/'work/SELF_CHECK.json').read_text())
+    assert report['passed'] and report['portability']['passed']
+
+
+def miniature():
+    import fixture_stage
+    assert T.BUILD == Path(sys.argv[1])
+    assert T.AREA == T.BUILD.parent and T.DEFAULT_ROOT == T.AREA/'root'
+    assert T.KIT == T.AREA/'kit_src'
+    assert T.LLG_STUB == T.BUILD/'llg_stub/llguidance'
+    with pytest.MonkeyPatch.context() as patch:
+        fixture_stage.test_stage_piecewise_and_complete(T.AREA/'work', patch)
+    (T.AREA/'work/root').rename(T.DEFAULT_ROOT)
+    root = T.DEFAULT_ROOT
+    cfg = T.load(root/'bootstrap/CONFIG.json')
+    state = T.load(root/'STAGING.json')
+    # Complete the stage fixture's tiny export and bootstrap verification records.
+    review = root/'bootstrap/REVIEW.json'; review.write_text('{}')
+    weight = T.LINEAGE/'m544/full_weights/full_weights.json'
+    artifact = T.LINEAGE/'m544/artifact.json'
+    index = T.physical(root, weight).parent/'index.json'
+    T.dump(index, {})
+    T.dump(T.physical(root, weight), dict(index=dict(name=index.name, bytes=index.stat().st_size,
+        sha256=T.sha(index)), files=[]))
+    T.dump(T.physical(root, artifact), dict(full_weights=dict(path=str(weight),
+        sha256=T.sha(T.physical(root, weight)))))
+    cfg.update(launcher_pins={}, launcher_review_pin=dict(sha256=T.sha(review)),
+        spec=dict(artifact=dict(path=str(artifact)), interpreters=dict(p1cpu=sys.executable)))
+    T.dump(root/'bootstrap/CONFIG.json', cfg)
+    state['pieces']['export']['evidence'] = dict(artifact_sha256=T.sha(T.physical(root, artifact)),
+        full_weights_sha256=T.sha(T.physical(root, weight)))
+    T.dump(root/'STAGING.json', state)
+    # This executable simulates bwrap only; stage, need receipts, and selfcheck run normally.
+    bwrap = T.AREA/'work/fixture-bwrap'
+    bwrap.write_text('#!'+sys.executable+'\n'+r"""
+import json, os, pathlib, sys
+if '--version' in sys.argv:
+    print('fixture bwrap'); sys.exit(0)
+assert '--unshare-net' in sys.argv
+if '--input' in sys.argv:
+    request_path = pathlib.Path(sys.argv[sys.argv.index('--input')+1])
+    request = json.loads(request_path.read_text())
+    area = pathlib.Path(os.environ['TRIN_AREA'])
+    assert area.is_dir() and str(request_path).startswith(str(area/'root')+'/')
+    root = area/'root'
+    assert str(root) in sys.argv and '/trinity-build/namespace_worker.py' in sys.argv
+    runner = next(root.glob('trinity_runner*p'))
+    sys.path.insert(0, str(runner))
+    import trinity_read as T
+    assert T.AREA == area and T.DEFAULT_ROOT == root
+    T.dump(pathlib.Path(request['work'])/'NEED.json', dict(need=[], ids=['fixture'], items=1,
+        estimated_frame_bytes={}))
+""")
+    bwrap.chmod(0o700)
+    # Also retain a separate legacy bundle; relocation must not overwrite it.
+    legacy = 'trinity_runner_t6' if 't6' in T.BUILD.name else 'trinity_runner'
+    target = root/legacy; target.mkdir()
+    (target/'legacy.py').write_text('# immutable staged fixture\n')
+    T.dump(target/'MANIFEST.json', {'legacy.py': dict(bytes=(target/'legacy.py').stat().st_size,
+        sha256=T.sha(target/'legacy.py'))})
+    before = T.disk_listing(target)
+    T.physical(root, T.LLG_TARGET).mkdir(parents=True)
+    assert T.cpu_need(root, 'main', first=1, bwrap=str(bwrap))['ids'] == ['fixture']
+    from types import SimpleNamespace as NS
+    T.need_command(NS(root=str(root), all=False, family='main', ids=None, first=1,
+        out=str(T.AREA/'work/NEED.txt'), bwrap=str(bwrap), llguidance_stub=True, fixture=False))
+    assert T.disk_listing(target) == before
+    for path in (T.BUILD/'ok', root/'ok', T.AREA/'work/ok'):
+        assert T.writable(path) == path
+    with pytest.raises(ValueError): T.writable(T.AREA/'escape')
+    (T.AREA/'work/escape').symlink_to(T.AREA.parent, target_is_directory=True)
+    with pytest.raises(ValueError): T.writable(T.AREA/'work/escape/out')
+    # Run the full existing checker with only the namespace process simulated.
+    before_check = T.selfcheck(root, bwrap=str(bwrap))
+    assert before_check['passed'], before_check
+    T.dump(T.AREA/'work/SELF_CHECK.json', before_check)
+    assert set(before_check['checks']) == {'bootstrap_payload', 'bwrap_hash', 'pieces',
+                                          'runner', 'relocated_runner', 'cpu_namespace'}
+    for directory, key in ((target, 'runner'), (root/(legacy+'p' if legacy.endswith('t6') else legacy+'_p'), 'relocated_runner')):
+        manifest = T.load(directory/'MANIFEST.json')
+        file = directory/next(iter(manifest))
+        raw = file.read_bytes(); file.write_bytes(raw+b'changed')
+        failed = T.selfcheck(root, bwrap=str(bwrap))
+        assert not failed['passed'] and failed['checks'][key]['errors']
+        file.write_bytes(raw)
+    if 't6' in T.BUILD.name:
+        import milestone as M
+        source = T.AREA/'work/export.tar'; source.write_bytes(b'fixture')
+        assert M.completed_local(source, tar=True) == source
+        link = source.with_name('linked.tar'); link.symlink_to(source)
+        with pytest.raises(ValueError): M.completed_local(link, tar=True)
+
+
+if __name__ == '__main__':
+    sys.path.insert(0, sys.argv[1])
+    # The script imports T before main; the subprocess cwd/PYTHONPATH selects this build.
+    miniature()
```
