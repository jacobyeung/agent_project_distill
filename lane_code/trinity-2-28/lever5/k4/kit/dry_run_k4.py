"""Installer tests, a stub-tower dry run over all 7 arms on one real capture, decode drift, error surfaces."""
import contextlib
import copy
import hashlib
import importlib.util
import io
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
GB = Path('/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild')
OLD8 = GB/'orchard_tower2x_b/8.tgz'
PAY = GB/'work/payload'
SITE = '/scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3.12/site-packages'
SERVED = '/scratch/jjyeung/orch_n30/nvkey1/work/c0stage/devs1_frames'
PINNED = {n: hashlib.sha256((GB/'orchard_tower2x_b'/n).read_bytes()).hexdigest() for n in ('0.py', '1.json', '2.py', '3.json', 'BATCH.sh')}
PINNED_C = {n: hashlib.sha256((GB/'orchard_tower2x_c'/n).read_bytes()).hexdigest() for n in ('0.py', '1.json', '2.py', '3.json', '9.py', 'BATCH.sh')}


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    start = time.monotonic()
    sys.path.append(SITE)
    work = Path(tempfile.mkdtemp(prefix='check_', dir=ROOT))
    build = json.loads((ROOT/'BUILD.json').read_text())
    raw = (ROOT/'o_place.sh').read_bytes()
    n = build['transport_prelude_bytes']
    prelude, blob = raw[:n], raw[n:]
    assert len(blob) == build['place_tar_bytes'] and hashlib.sha256(blob).hexdigest() == build['place_tar_sha256']
    def install(target, source=OLD8, body=blob, edit=None):
        text = prelude.decode().replace(build['path'], str(target)).replace(build['source'], str(source))
        text = text.replace('/project/community', '/scratch').replace('/usr/bin/python3', sys.executable)
        if edit:
            text = edit(text)
        return subprocess.run(['bash', '-s'], input=text.encode()+body, capture_output=True)
    checks = {}
    dest = work/'a'
    done = install(dest)
    assert done.returncode == 0, done.stderr
    assert int(done.stdout) == build['added_bytes']
    assert os.path.samefile(dest/'8.tgz', OLD8)
    for name in build['shipped']:
        assert (dest/name).read_bytes() == (ROOT/name).read_bytes()
    checks['install'] = dict(stdout=int(done.stdout), same_inode=True, identical=True)
    again = install(dest)
    assert again.returncode and b'E44' in again.stderr
    missing = install(work/'b', source=work/'missing')
    assert missing.returncode and b'E49' in missing.stderr and not (work/'b').exists()
    wrong = work/'wrong.tgz'
    with wrong.open('xb') as f:
        f.seek(build['reused_bytes']-1)
        f.write(b'\0')
    corrupt = install(work/'c', source=wrong)
    assert corrupt.returncode and b'E46' in corrupt.stderr and not (work/'c').exists()
    flipped = bytearray(blob)
    flipped[len(blob)//2] ^= 1
    for label, body in (('flipped', bytes(flipped)), ('truncated', blob[:-1]), ('extra', blob+b'\n')):
        bad = install(work/('d'+label), body=body)
        assert bad.returncode and b'E40' in bad.stderr and not (work/('d'+label)).exists(), label
    floor = install(work/'e', edit=lambda t: t.replace('-ge 5', '-ge 999999999'))
    assert floor.returncode == 3 and b'E48' in floor.stderr and not (work/'e').exists()
    checks['rejected'] = ['existing destination E44', 'missing source E49', 'wrong archive hash E46',
                          'flipped/truncated/extra-byte transport E40', '/project floor E48']
    entry = module('entry_k4', dest/'0.py')
    worker = module('worker_k4', dest/'2.py')
    diag = module('diag_k4', dest/'9.py')
    cfg, verified = entry.verify(dest)
    assert len(verified.tasks(cfg)) == 70 and verified.forecast(cfg) <= cfg['xv'][1]
    frames = work/'8'
    frames.mkdir()
    for archive in (dest/'8.tgz', dest/'10.tgz'):
        with tarfile.open(archive) as t:
            for item in t:
                assert item.isfile() and '/' not in item.name and item.name.endswith('.png')
                with (frames/item.name).open('xb') as f:
                    f.write(t.extractfile(item).read())
    assert len(list(frames.iterdir())) == 1250
    cfg.update(x8=[str(PAY/'tree'), SITE], xl=str(frames), xc=SERVED, xu=str(work/'9.err'))
    for pin in cfg['x9']:
        pin[0] = str(PAY/pin[0].split('/p/', 1)[1])
    before = time.monotonic()
    result = worker.run(cfg, mode='stub', only=1)
    stub_seconds = time.monotonic()-before
    order = [[0, a] for a in cfg['xr']]
    assert result['complete'] and result['ran'] == order, result.get('error_detail')
    arms = result['rows'][0]['arms']
    assert [len(a['c2w']) for a in arms] == [32, 32, 32, 63, 94, 63, 94]
    assert result['raw_match_count'] == result['raw_frame_count'] == 410
    ref = json.loads((ROOT/'REFERENCE_K4.json').read_text())
    plans = ref['captures'][0]['arms']
    for a, plan in zip(arms, plans):
        assert a['raw_sha256'] == plan['raw_sha256'] and a['ids'] == plan['ids'] and a['slots'] == plan['slots']
    served = [a['raw_sha256'][0] for a in (arms[0], arms[1], arms[5], arms[6])]
    assert len(set(served)) == 1
    assert [arms[6]['raw_sha256'][s] for s in arms[6]['slots']] == arms[0]['raw_sha256']
    assert [arms[4]['raw_sha256'][s] for s in arms[4]['slots']] == arms[2]['raw_sha256']
    assert arms[0]['raw_sha256'] != arms[2]['raw_sha256']
    import cv2
    import numpy as np
    from PIL import Image
    def alternate(arr, size, interpolation):
        assert interpolation == cv2.INTER_CUBIC
        return np.asarray(Image.fromarray(arr).resize(size, Image.Resampling.BICUBIC))
    with patch.object(cv2, 'resize', alternate):
        drift = worker.run(cfg, mode='stub', only=1)
    assert drift['complete'] and drift['raw_frame_count'] == 410
    assert drift['raw_match_count'] == 128, drift['raw_match_count']
    score = module('score_k4d', ROOT/'score_k4.py')
    for name, data in (('DRY', result), ('DRIFT', drift)):
        assert score.score(data, ref)['verdict'] == 'synthetic'
        worker.write(work/(name+'.json'), data)
    # A wrong PNG at a planned name stays fatal.
    bad_name = cfg['x3'][0]['x4'][2]['x1'][0]+'.png'
    good = (frames/bad_name).read_bytes()
    (frames/bad_name).write_bytes((frames/(cfg['x3'][0]['x4'][2]['x1'][1]+'.png')).read_bytes())
    failed = worker.run(cfg, mode='stub', only=1)
    assert not failed['complete'] and failed['error_detail']['code'] == 'E07'
    (frames/bad_name).write_bytes(good)
    # Decode of every shipped frame, as the CPU check runs it, and the CPU pass rule.
    before = time.monotonic()
    decoded = worker.decode_all(cfg)
    decode_seconds = time.monotonic()-before
    frames_total = sum(a['frames'] for r in decoded for a in r['arms'])
    matches = sum(a['raw_match_count'] for r in decoded for a in r['arms'])
    assert frames_total == matches == 4100
    unit = copy.deepcopy(result)
    unit['rows'][0]['arms'] = [arms[0]]+[dict(status='budget')]*6
    unit.update(ran=[[0, 0]], decoded=decoded, mode='cpu')
    assert entry.cpu_passed(cfg, verified, unit)
    short = copy.deepcopy(unit)
    short['decoded'] = short['decoded'][:-1]
    assert not entry.cpu_passed(cfg, verified, short)
    short = copy.deepcopy(unit)
    short['decoded'][2]['arms'][6]['frames'] -= 1
    assert not entry.cpu_passed(cfg, verified, short)
    summary = score.cpu_summary(unit, ref)
    assert summary['decoded_frames'] == 4100 and summary['finite']
    # Entry modes keep short error records without staging the parent payload.
    for mode in (0, 1):
        out = work/('e'+str(mode))
        out.mkdir()
        def fail(*args, **kwargs):
            raise ValueError('E24')
        with patch.object(entry, 'verify', return_value=(cfg, worker)), patch.object(entry, 'admit'), \
                patch.object(entry, 'execute', side_effect=fail), patch.object(sys, 'argv', ['0.py', str(mode), str(out)]):
            if mode == 0:
                try:
                    entry.main()
                except ValueError as exc:
                    diag.record(entry.error_path(out, mode), diag.detail(exc))
            else:
                (out/'1.json').write_bytes((ROOT/'1.json').read_bytes())
                assert entry.main() == 1
                ret = json.loads((out/'5.json').read_text())
                assert ret['mode'] == 'gpu' and not ret['complete']
        log = entry.error_path(out, mode).read_text()
        assert json.loads(log)['code'] == 'E24'
        assert '/scratch/' not in log and '/tmp/' not in log
    broken = work/'f'
    broken.mkdir()
    for name in ('0.py', '9.py'):
        (broken/name).write_bytes((ROOT/name).read_bytes())
    run = subprocess.run([sys.executable, '-I', '-s', '-B', str(broken/'9.py'), '0', str(broken)], capture_output=True)
    assert run.returncode == 1
    logs = (broken/'4.err').read_text()
    assert 'FileNotFoundError' in logs and 'E92' in logs and logs.encode() in run.stderr
    (broken/'4.out').write_bytes(run.stdout)
    (broken/'4.stderr').write_bytes(run.stderr)
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        diag.capture([sys.executable, '-c', "import sys; print('/payload/tower/camera.py'); print('arkit model', file=sys.stderr)"])
    summaries = [json.loads(stdout.getvalue()), json.loads(stderr.getvalue())]
    assert all(set(x) == {'bytes', 'sha256'} and x['bytes'] > 0 for x in summaries)
    after = {n: hashlib.sha256((GB/'orchard_tower2x_b'/n).read_bytes()).hexdigest() for n in PINNED}
    after_c = {n: hashlib.sha256((GB/'orchard_tower2x_c'/n).read_bytes()).hexdigest() for n in PINNED_C}
    assert after == PINNED and after_c == PINNED_C
    evidence = dict(passed=True, capture=ref['captures'][0]['capture'], arms=ref['labels'],
                    frames=[len(a['c2w']) for a in arms], order=cfg['xr'], raw_matches=410, drift_matches=128,
                    alternate_backend='Pillow bicubic replacing cv2.resize in test only (served PNGs unaffected)',
                    versions=arms[0]['decode_versions'], corrupt_png_error='E07', decode_all_frames=4100,
                    decode_all_seconds=decode_seconds, stub_seconds=stub_seconds, return_bytes_one_capture=len(json.dumps(result, separators=(',', ':'))),
                    installer=checks, cpu_pass_rule=True, error_logs=True, supervisor_subprocess=True,
                    opaque_stream_summaries=summaries, prior_kits_unchanged=True, seconds=time.monotonic()-start,
                    rss_kib=max(a['rss_kib'] for a in arms), work=str(work),
                    scope='Real capture, real PNGs, actual preprocessing and pose conversion with a stub backbone/heads.')
    (ROOT/'DRY_K4.json').write_text(json.dumps(evidence, indent=2)+'\n')
    print(json.dumps(evidence))


if __name__ == '__main__':
    main()
