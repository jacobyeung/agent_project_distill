import json

import pytest

from conftest import AUTH, TEACHER_K1
from owngrd.eligibility import Gate, canon


@pytest.fixture(scope='module')
def gate():
    return Gate(AUTH)


def _load(name):
    return json.loads((AUTH / name).read_text())


def test_every_devs1_capture_refused(gate):
    caps = _load('DEVS1_MANIFEST.json')['captures']
    assert len(caps) == 152
    assert all(gate.reasons(c['scene']) for c in caps)


def test_withheld_rooms_refused(gate):
    w = _load('WITHHELD_ROOMS_80.json')
    pool = _load('CAPTURES.json')['captures']
    rooms = {canon(r) for r in w['rooms']}
    hit = [c for c in pool if canon(c['room']) in rooms]
    assert hit and all('withheld_80' in gate.reasons(c['canonical']) for c in hit)


def test_benchmark_scenes_refused(gate):
    b = _load('BENCH_SCENE_EXCLUSIONS_v2.json')
    pool = {c['canonical'] for c in _load('CAPTURES.json')['captures']}
    hit = [canon(s) for s in b['scenes'] if canon(s) in pool]
    assert hit and all('benchmark_v2' in gate.reasons(s) for s in hit)


def test_admit_refuses_mixed_manifest(gate):
    man = json.loads(TEACHER_K1.read_text())
    bad = _load('DEVS1_MANIFEST.json')['captures'][0]['scene']
    with pytest.raises(ValueError):
        gate.admit(man['captures'][:3] + [{'canonical': canon(bad)}])


def test_teacher_manifest_admitted_and_bound(gate):
    man = json.loads(TEACHER_K1.read_text())
    r = gate.admit(man['captures'])
    assert r['gate_digest'] == man['gate_receipt']['gate_digest']
    assert not any(gate.reasons(c['canonical']) for c in man['captures'])


def test_changed_authority_refused(tmp_path):
    for p in AUTH.iterdir():
        (tmp_path / p.name).write_bytes(p.read_bytes())
    d = json.loads((tmp_path / 'WITHHELD_ROOMS_80.json').read_text())
    d['rooms'] = d['rooms'][:-1]
    (tmp_path / 'WITHHELD_ROOMS_80.json').write_text(json.dumps(d))
    with pytest.raises(ValueError, match='changed'):
        Gate(tmp_path)
