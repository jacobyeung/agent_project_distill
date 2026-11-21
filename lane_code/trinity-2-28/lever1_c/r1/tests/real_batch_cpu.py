"""Stage the delivery through production job.stage with real archives, then run
the first production capture on CPU in the pinned Orchard environment.

Substitutions: the host bwrap binary (the pinned one is absent), part sources
mapped to the authenticated local copies in DL (single-part sources are
hard-linked after the same SHA256/MD5 check copy_parts performs), the policy
terminator helper (inert sleep, as in test_vpy), /project paths mapped to the
fixture, and device 'cpu' for 'cuda:0'. Everything else is production code.
Writes out/REAL_BATCH_CPU.json.
"""
import os
THREADS = '48'
os.environ.update(CUDA_VISIBLE_DEVICES='', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
import base64
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import import_audit as A
DL = Path('/scratch/jjyeung/orch_n30/reads228/dl')
BULK = {'e/0': 's4e0b', 'e/1': 's4e1', 'e/2': 's4e2', 'e/3': 's4e3', 'g/0': 'g0'}
started = time.monotonic()
raw = (HERE/'out/delivery.tgz').read_bytes(); outer = A.unpack(raw); inner = A.unpack(outer['0.tgz'])
base = Path(tempfile.mkdtemp(prefix='real_', dir=HERE.parent/'r1_fixtures_old')); p = base/'p'; p.mkdir()
evidence = dict(passed=False, delivery_sha256=A.sha(raw), token=A.decode(outer['0.json'])['token'], fixture=str(base),
                threads=int(THREADS), substitutions=__doc__.split('\n\n')[1].replace('\n', ' '))
out_path = HERE/'out/REAL_BATCH_CPU.json'
def save():
    evidence['wall_seconds'] = time.monotonic()-started
    out_path.write_text(json.dumps(evidence, indent=2, default=str)+'\n')
try:
    for name, data in inner.items():
        dest = p/name; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(data)
    pkg = base/'package'; pkg.mkdir()
    for name, data in outer.items():
        dest = pkg/name; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(data)
    sys.path.insert(0, str(p))
    import l
    l.install(p)
    from orchard_h10 import job, boot
    from orchard_h10.common import template, canonical, sha, write
    from orchard_h10.export_pins import load
    S, J, R, *_ = template()
    cfg = A.decode(inner['9.json']); pub = A.decode(outer['0.json'])
    cfg.update({k: pub[k] for k in ('payload_bytes', 'payload_sha256', 'plan_sha256')})
    inputs = A.decode(outer['a/1.json']); assets = A.decode(inner['orchard_h10/vendor/ORCHARD_ASSETS.json'])
    root = base/'j'; root.mkdir(); os.environ.update(USER='jjyeung', SLURM_JOB_ID='174777')
    mapping = {}
    for i, group in enumerate(assets['groups']):
        for n, (path, size, digest) in enumerate(group):mapping[path] = DL/('r%d_%d' % (i, n))
    for spec in inputs['archives']:
        for part in spec['parts']:
            rel = '/'.join(Path(part['path']).parts[-2:])
            path = DL/BULK[rel] if rel in BULK else DL/Path(part['path']).name
            if not path.exists():raise FileNotFoundError('input not on this node: '+part['path'])
            mapping[part['path']] = path
    mapping[str(Path('/project/community/jjyeung')/cfg['token']/'0.tgz')] = base/'0.tgz'
    (base/'0.tgz').write_bytes(outer['0.tgz'])
    local_bwrap = Path('/usr/bin/bwrap')
    original_copy = S.copy_parts; original_path = boot.Path
    copies = []
    def copied(parts, dest, opener, **kwargs):
        t0 = time.monotonic()
        if dest.name == 'bwrap':
            data = local_bwrap.read_bytes(); dest.write_bytes(data)
            return dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        cache = HERE/'tests/vpy_inguub3c/j/a/1'
        if len(parts) == 1 or (dest.name == '1' and cache.exists()):
            source = mapping[parts[0]['path']] if len(parts) == 1 else cache
            whole = hashlib.sha256()
            with source.open('rb') as stream:
                for part in parts:
                    h, m, left = hashlib.sha256(), hashlib.md5(), part['bytes']
                    while left:
                        block = stream.read(min(left, 8*1024**2))
                        if not block:raise ValueError('Part size differs')
                        left -= len(block); h.update(block); m.update(block); whole.update(block)
                    if h.hexdigest() != part['sha256']:raise ValueError('Part SHA256 differs')
                    if part.get('md5') and base64.b64encode(m.digest()).decode() != part['md5']:raise ValueError('Part MD5 differs')
                if stream.read(1):raise ValueError('Part size differs')
            if kwargs.get('expected_sha') and whole.hexdigest() != kwargs['expected_sha']:raise ValueError('Archive SHA256 differs')
            os.link(source, dest)
            value = dict(bytes=source.stat().st_size, sha256=whole.hexdigest())
            copies.append(dict(dest=dest.name, linked=True, seconds=time.monotonic()-t0, **value))
            return value
        value = original_copy(parts, dest, lambda part: mapping[part['path']].open('rb'), **kwargs)
        copies.append(dict(dest=dest.name, linked=False, seconds=time.monotonic()-t0, bytes=sum(x['bytes'] for x in parts)))
        return value
    def mapped_path(value):return Path(mapping.get(str(value), value))
    inert = base/'0.sh'; inert.write_text('#!/bin/sh\nexec sleep 30\n'); inert.chmod(0o700)
    original_namespace = J.namespace
    def namespace():
        for name in ('sj', 'fsw', 'm/ap'):(root/name).mkdir(parents=True, exist_ok=True)
        return original_namespace(root)+['--bind', str(root), str(root), '--ro-bind', str(inert), inputs['policy']['terminator']]
    production_launch = boot.launch
    def launch(r, c, i, j, pre_bytes, seconds):
        dispatch = root/'a'
        (dispatch/'5.py').write_bytes(inner['orchard_h10/entry.py'])
        config = dict(package=cfg['logical']+'/p', output=cfg['logical']+'/r', python=inputs['python'],
                      cache_root=cfg['logical']+'/r/cache/0', prefix=['bash', inputs['policy']['vnice']])
        (dispatch/'4.json').write_text(json.dumps(dict(action=4, config=config, package=config['package'], plan=cfg['plan_sha256'], job='174777')))
        shared = base/'shared'; shared.mkdir()
        def launch_path(value):
            path = Path(value)
            return shared if str(path) == '/project/community/jjyeung' else original_path(mapping.get(str(value), value))
        with patch.object(J, 'namespace', side_effect=lambda r: namespace()), patch.object(boot, 'Path', side_effect=launch_path):
            production_launch(r, c, i, j, pre_bytes, seconds)
        receipt = A.decode(J.physical(root, cfg['logical']+'/r/metadata/25.json').read_bytes())
        evidence['boot'] = {k: receipt.get(k) for k in ('passed', 'modules', 'child_returncode', 'worker_returncode', 'failed_module', 'bulk_bytes', 'pre_bulk_bytes')}
        if not receipt.get('passed'):raise RuntimeError('boot failed')
    t0 = time.monotonic()
    with patch.object(S, 'copy_parts', side_effect=copied), patch.object(boot, 'Path', side_effect=mapped_path), \
         patch.object(boot, 'launch', side_effect=launch):
        job.stage(root, cfg, inputs, S, J)
    evidence['stage'] = dict(seconds=time.monotonic()-t0, copies=copies, production_job_stage=True)
    save()
    # Production preparation (job.main action 0), then the operator's read-0 capture on CPU.
    for name in ('sj', 'fsw', 'm/ap'):(root/name).mkdir(parents=True, exist_ok=True)
    env = J.environment(root)
    env = {k: v for k, v in env.items() if 'sam' not in k.lower()}
    env.update(OMP_NUM_THREADS=THREADS, MKL_NUM_THREADS=THREADS, OPENBLAS_NUM_THREADS=THREADS, CUDA_VISIBLE_DEVICES='')
    dispatch = root/'a'
    pins = load(inputs, pkg)
    write(dispatch/'0.json', dict(action=0, package=cfg['logical']+'/p', config=cfg, inputs={**inputs, '_export': pins}))
    t0 = time.monotonic()
    prep = subprocess.run(namespace()+[inputs['python'], '-B', '-I', str(dispatch/'5.py'), str(dispatch/'0.json')],
                          env=env, cwd=root, capture_output=True, text=True)
    evidence['prepare'] = dict(returncode=prep.returncode, seconds=time.monotonic()-t0, tail=(prep.stdout+prep.stderr)[-4000:])
    if prep.returncode:raise RuntimeError('action 0 failed')
    p_logical = cfg['logical']+'/p'
    operator = root/'7.py'; operator.write_bytes(outer['a/6.py'])
    run_cfg = dict(export_pin=cfg['logical']+'/d/6.json', export_cache=cfg['logical']+'/d/7.json', allocation='174777', package=p_logical,
                   output=cfg['logical']+'/r', python=inputs['python'], export=cfg['logical']+'/d/e',
                   binding=cfg['logical']+'/d/binding.json', settings=cfg['logical']+'/d/settings.json',
                   plan_sha256=cfg['plan_sha256'], inputs_sha256=canonical({k: v for k, v in inputs.items() if k != 'resume'}),
                   operator_sha256=hashlib.sha256(outer['a/6.py']).hexdigest(),
                   types=inputs.get('types'), stop_margin=cfg['stop_margin'], return_margin=cfg['return_margin'],
                   prefix=['bash', inputs['policy']['vnice']])
    write(dispatch/'1.json', dict(action=1, package=p_logical, config=run_cfg, end=time.time()+3600))
    (dispatch/'real.py').write_bytes((HERE/'tests/real_batch_inner.py').read_bytes())
    result_file = root/'real.json'
    t0 = time.monotonic()
    proc = subprocess.Popen(['nice', '-n', '10']+namespace()+[inputs['python'], '-B', '-I', str(dispatch/'real.py'),
                            str(dispatch/'1.json'), str(result_file), str(operator)],
                            env=env, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        output, _ = proc.communicate(timeout=3600)
    except subprocess.TimeoutExpired:
        proc.terminate(); output, _ = proc.communicate(timeout=60)
        evidence['timeout'] = True
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    evidence['forward'] = dict(returncode=proc.returncode, seconds=time.monotonic()-t0,
                               children_peak_rss_bytes=usage.ru_maxrss*1024, output_tail=output.decode(errors='replace')[-6000:])
    if result_file.exists():evidence['result'] = json.loads(result_file.read_text())
    evidence['passed'] = proc.returncode == 0 and evidence.get('result', {}).get('passed') is True
except BaseException as error:
    import traceback
    evidence.update(error=type(error).__name__+': '+str(error)[:4000], traceback=traceback.format_exc()[-8000:])
finally:
    save()
print(json.dumps(dict(passed=evidence['passed'], error=evidence.get('error'), wall=evidence['wall_seconds'])))
raise SystemExit(0 if evidence['passed'] else 1)
