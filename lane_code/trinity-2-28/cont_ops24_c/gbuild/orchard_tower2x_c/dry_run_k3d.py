"""Exercise one real capture, decode drift, input rejection, placement and errors."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent/'orchard_tower2x_b'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def put(path, obj):
    path.write_text(json.dumps(obj, indent=2)+'\n')


def main():
    start = time.monotonic()
    work = Path(tempfile.mkdtemp(prefix='check_', dir=ROOT))
    build = json.loads((ROOT/'BUILD.json').read_text())
    script = (ROOT/'o_place.sh').read_text()
    dest = work/'a'
    def install(target, text=script, source=OLD/'8.tgz'):
        local = text.replace(build['path'], str(target)).replace(build['source'], str(source))
        local = local.replace('/usr/bin/python3', sys.executable)
        return subprocess.run(['bash','-s'], input=local, text=True, capture_output=True)
    before = {n:hashlib.sha256((OLD/n).read_bytes()).hexdigest()
              for n in ('0.py','1.json','2.py','3.json','BATCH.sh')}
    done = install(dest)
    assert done.returncode == 0, done.stderr
    assert int(done.stdout) == build['added_bytes']
    assert os.path.samefile(dest/'8.tgz', OLD/'8.tgz')
    for name in build['small_files']:
        assert (dest/name).read_bytes() == (ROOT/name).read_bytes()
    assert install(dest).returncode
    missing = install(work/'b', source=work/'missing')
    assert missing.returncode and not (work/'b').exists()
    # A same-sized sparse file exercises archive SHA256 rejection without copying frames.
    wrong = work/'wrong.tgz'
    with wrong.open('xb') as f:
        f.seek(build['reused_bytes']-1)
        f.write(b'\0')
    corrupt = install(work/'c', source=wrong)
    assert corrupt.returncode and 'E46' in corrupt.stderr and not (work/'c').exists()
    # Change the transport pin, not its embedded assets, to exercise fail-before-write.
    text = script.replace("!=", "==", 1)
    corrupt_transport = install(work/'d', text=text)
    assert corrupt_transport.returncode and 'E40' in corrupt_transport.stderr and not (work/'d').exists()
    worker = module('worker_k3d', dest/'2.py')
    entry = module('entry_k3d', dest/'0.py')
    diag = module('diag_k3d', dest/'9.py')
    cfg, verified = entry.verify(dest)
    assert len(verified.tasks(cfg)) == 20
    assert verified.forecast(cfg) <= 1500
    assert cfg['xk'] == [1, 2, 'cv2']
    assert all(r['x6'] == (3 if r['x5'][0] > r['x5'][1] else 0) for r in cfg['x3'])
    frames = work/'8'
    frames.mkdir()
    names = set(cfg['x3'][0]['x4'][1]['x3'])
    with tarfile.open(dest/'8.tgz') as archive:
        for item in archive:
            if item.name in names:
                (frames/item.name).write_bytes(archive.extractfile(item).read())
    assert len(list(frames.iterdir())) == 63
    pay = ROOT.parent/'work/payload'
    cfg.update(x8=[str(pay/'tree'), '/scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3.12/site-packages'],
               xl=str(frames), xu=str(work/'9.err'))
    for pin in cfg['x9']:
        pin[0] = str(pay/pin[0].split('/p/',1)[1])
    result = worker.run(cfg, stub=True, only=1)
    assert result['complete'] and result['ran'] == [[0,0],[0,1]], result.get('error_detail')
    assert result['raw_match_count'] == result['raw_frame_count'] == 95
    assert [len(a['c2w']) for a in result['rows'][0]['arms']] == [32,63]
    # Keep the production recipe unchanged; replace cv2.resize only in this test.
    import cv2
    import numpy as np
    from PIL import Image
    def alternate(arr, size, interpolation):
        assert interpolation == cv2.INTER_CUBIC
        return np.asarray(Image.fromarray(arr).resize(size, Image.Resampling.BICUBIC))
    with patch.object(cv2, 'resize', alternate):
        drift = worker.run(cfg, stub=True, only=1)
    assert drift['complete'] and drift['raw_frame_count'] == 95
    assert drift['raw_match_count'] == 0
    for data in (result, drift):
        for arm in data['rows'][0]['arms']:
            assert len(arm['decode_versions']) == len(arm['ids'])
            assert all(set(v) == {'cv2','PIL','numpy'} for v in arm['decode_versions'])
            assert arm['raw_match_count'] == sum(arm['raw_matches'])
        a,b = data['rows'][0]['arms']
        assert [b['raw_sha256'][s] for s in b['slots']] == a['raw_sha256']
    score = module('score_k3d', ROOT/'score.py')
    ref = json.loads((ROOT/'REFERENCE.json').read_text())
    for name, data in [('DRY',result),('DRIFT',drift)]:
        assert score.score(data, ref)['verdict'] == 'synthetic'
        raw = worker.write(work/(name+'.json'), data)
        receipt = worker.write(work/(name+'.1.json'), dict(schema=2,token=cfg['x0'],input_sha256=worker.digest(dest/'1.json'),
            sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), complete=True, stub=True, job='0'))
        (ROOT/(name+'.json')).write_bytes(raw)
        (ROOT/(name+'.1.json')).write_bytes(receipt)
    bad = copy.deepcopy(cfg)
    bad['x3'][0]['x4'][0]['x1'][0] = '0'*64
    failed = worker.run(bad, stub=True, only=1)
    assert not failed['complete'] and failed['error_detail']['code'] == 'E07'
    # Both entry modes retain a short error record without staging any parent payload.
    for mode in (0,1):
        out = work/('e'+str(mode))
        out.mkdir()
        def fail(*args, **kwargs):
            raise ValueError('E24')
        with patch.object(entry,'verify',return_value=(cfg,worker)), patch.object(entry,'admit'), \
                patch.object(entry,'execute',side_effect=fail), patch.object(sys,'argv',['0.py',str(mode),str(out)]):
            if mode == 0:
                try:
                    entry.main()
                except ValueError as exc:
                    diag.record(entry.error_path(out,mode),diag.detail(exc))
            else:
                # The receipt needs this small local configuration.
                (out/'1.json').write_bytes((ROOT/'1.json').read_bytes())
                assert entry.main() == 1
        log = entry.error_path(out,mode).read_text()
        assert json.loads(log)['code'] == 'E24'
        assert '/scratch/' not in log and '/tmp/' not in log
    # A real subprocess exercises the supervisor and outer exception handler.
    broken = work/'f'
    broken.mkdir()
    for name in ('0.py','9.py'):
        (broken/name).write_bytes((ROOT/name).read_bytes())
    run = subprocess.run([sys.executable,'-I','-s','-B',str(broken/'9.py'),'0',str(broken)],capture_output=True)
    assert run.returncode == 1
    logs = (broken/'4.err').read_text()
    assert 'FileNotFoundError' in logs and 'E92' in logs
    assert logs.encode() in run.stderr
    (broken/'4.out').write_bytes(run.stdout)
    (broken/'4.stderr').write_bytes(run.stderr)
    assert '/scratch/' not in logs and '/tmp/' not in logs
    # Exercise byte streams containing opaque-word violations and payload paths.
    with patch.object(sys,'argv',[]):
        import contextlib, io
        stdout,stderr = io.StringIO(),io.StringIO()
        with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
            diag.capture([sys.executable,'-c',"import sys; print('/payload/tower/camera.py'); print('arkit model',file=sys.stderr)"])
        summaries = [json.loads(stdout.getvalue()),json.loads(stderr.getvalue())]
        assert all(set(x) == {'bytes','sha256'} and x['bytes'] > 0 for x in summaries)
    after = {n:hashlib.sha256((OLD/n).read_bytes()).hexdigest() for n in before}
    assert before == after and worker.digest(OLD/'8.tgz') == build['reused_sha256']
    evidence = dict(passed=True,capture='41069054',frames=[32,63],normal_matches=95,
        mismatch_matches=0,frames_per_run=95,alternate_backend='Pillow bicubic replacing cv2.resize in test only',
        versions=result['rows'][0]['arms'][0]['decode_versions'][0],
        corrupt_png_error='E07',hard_link_same_inode=True,small_files_identical=True,
        rejected=['existing destination','missing source','wrong archive hash','wrong transport hash'],
        cpu_gpu_error_logs=True,supervisor_subprocess=True,opaque_stream_summaries=summaries,
        old_kit_pins_unchanged=True,seconds=time.monotonic()-start,
        rss_kib=max(a['rss_kib'] for data in (result,drift) for a in data['rows'][0]['arms']),
        work=str(work),scope='Real capture and actual preprocessing/pose conversion with stub backbone/heads; no GPU or remote execution.')
    put(ROOT/'CPU_K3D.json',evidence)
    print(json.dumps(evidence))


if __name__ == '__main__':
    main()
