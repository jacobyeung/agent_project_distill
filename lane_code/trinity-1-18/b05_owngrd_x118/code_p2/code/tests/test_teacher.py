import copy
import gzip
import json

import pytest

from conftest import FRAMES, TEACHER_K1
from owngrd import teacher
from owngrd.common import rle_decode, sha256_file


def small_manifest(tmp_path, n_caps=2, n_names=3, tag='man'):
    man = json.loads(TEACHER_K1.read_text())
    have = set(json.loads((FRAMES.parent / 'inv/frames12_caps.json').read_text()))
    caps = [copy.deepcopy(c) for c in man['captures'] if c['canonical'] in have][:n_caps]
    for c in caps:
        c['names'] = c['names'][:n_names]
        for f in c['frames']:
            f['path'] = str(FRAMES / f['sha256'][:2] / f"{f['sha256']}.png")
    man['captures'] = caps
    p = tmp_path / f'{tag}.json'
    p.write_text(json.dumps(man))
    return p


def run(p, out, *extra):
    return teacher.main(['--manifest', str(p), '--manifest-sha256', sha256_file(p), '--out', str(out), '--stub', *extra])


def test_stub_pass_format_and_resume(tmp_path):
    p = small_manifest(tmp_path)
    out = tmp_path / 'out'
    assert run(p, out) == 0
    man = json.loads(p.read_text())
    for c in man['captures']:
        d = out / teacher.capture_key(c['canonical'])
        done = json.loads((d / 'DONE.json').read_text())
        assert done['teacher_sha256'] == sha256_file(d / 'teacher.json.gz')
        t = json.loads(gzip.decompress((d / 'teacher.json.gz').read_bytes()))
        assert t['stub'] is True and t['contract']['joint_floor'] == 0.2 and t['contract']['cap'] == 10
        assert t['frame_sha256'] == [f['sha256'] for f in c['frames']]
        assert len(t['frames']) == 32 and set(t['roles']) == {n['name'] for n in c['names']}
        for fr in t['frames'].values():
            assert fr['size'] in ([640, 480], [480, 640])
            for pred in fr['phrases'].values():
                assert len(pred['instances']) <= 10
                for inst in pred['instances']:
                    assert inst['joint_score'] >= 0.2
                    assert rle_decode(inst['mask']).shape == tuple(fr['size'])
    before = {c['canonical']: (out / teacher.capture_key(c['canonical']) / 'DONE.json').stat().st_mtime_ns
              for c in man['captures']}
    assert run(p, out) == 0
    after = {k: (out / teacher.capture_key(k) / 'DONE.json').stat().st_mtime_ns for k in before}
    assert before == after


def test_partial_capture_redone(tmp_path):
    p = small_manifest(tmp_path, n_caps=1)
    out = tmp_path / 'out'
    assert run(p, out) == 0
    c = json.loads(p.read_text())['captures'][0]
    d = out / teacher.capture_key(c['canonical'])
    ref = (d / 'teacher.json.gz').read_bytes()
    (d / 'DONE.json').rename(d / 'DONE.moved')
    (d / 'teacher.json.gz').write_bytes(b'junk')
    assert run(p, out) == 0
    assert gzip.decompress((d / 'teacher.json.gz').read_bytes()) == gzip.decompress(ref)


def test_shards_partition(tmp_path):
    p = small_manifest(tmp_path, n_caps=3, n_names=1)
    out = tmp_path / 'out'
    assert run(p, out, '--shard', '0/2') == 0
    assert run(p, out, '--shard', '1/2') == 0
    assert len(list(out.glob('*/DONE.json'))) == 3


def test_time_cap_exit3(tmp_path):
    p = small_manifest(tmp_path, n_caps=2, n_names=1)
    assert run(p, tmp_path / 'out', '--hours', '0') == 3


def test_refusals(tmp_path):
    p = small_manifest(tmp_path, n_caps=1, tag='a')
    with pytest.raises(SystemExit, match='hash'):
        teacher.main(['--manifest', str(p), '--manifest-sha256', '0' * 64, '--out', str(tmp_path / 'o'), '--stub'])
    man = json.loads(p.read_text())
    man['captures'][0]['frames'][0]['sha256'] = 'f' * 64
    p.write_text(json.dumps(man))
    with pytest.raises(ValueError, match='Frame hash'):
        run(p, tmp_path / 'o2')
    p = small_manifest(tmp_path, n_caps=1, tag='b')
    man = json.loads(p.read_text())
    man['gate_receipt']['gate_digest'] = 'x'
    p.write_text(json.dumps(man))
    with pytest.raises(SystemExit, match='Gate digest'):
        run(p, tmp_path / 'o3')
