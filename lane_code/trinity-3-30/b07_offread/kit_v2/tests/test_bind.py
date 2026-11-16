"""Binding refusals: export, init selection, one-export ledger, P8 freeze, K1 refit, EAT-1."""
import hashlib
import json

import pytest

from offkit import bind as B

D0_SHA = 'a' * 64
_LED = {}


@pytest.fixture(autouse=True)
def _ledger(tmp_path):
    _LED['path'] = tmp_path / 'DEFAULT_LEDGER.jsonl'


def bind(*a, **k):
    k.setdefault('ledger', _LED['path'])
    return B.bind(*a, **k)


def _done(tmp_path, sha=D0_SHA, step=200):
    p = tmp_path / f'gcs_359fcc3c_m{step}.done'
    p.write_text(f'q8/8865619b/359fcc3c_m{step}.tar 123456789 {sha}\n')
    return p


def _sel(tmp_path, sha=D0_SHA, step=200, **over):
    p = tmp_path / 'INIT_SELECTION.json'
    body = dict(selected_sha256=sha, selected_step=step, init_rule_sha256=B.INIT_RULE_SHA,
                d0_ended=dict(reason='completed_step_1000', event='EV/cont_ops/fixture_D0_ENDED.md'),
                label='D0 m%d selected by NEXT_LEG_INIT_RULE item 7' % step)
    body.update(over)
    p.write_text(json.dumps(body))
    return p


def _freeze(tmp_path, values, name='ROUTED_PATH_FROZEN_20261117.md'):
    p = tmp_path / name
    p.write_text('# P8 freeze\n\n```json\n' + json.dumps(dict(freeze_values=values)) + '\n```\n')
    return p, hashlib.sha256(p.read_bytes()).hexdigest()


def test_step544_direct_binds():
    b = bind('vsibench5130', 'step544', 'direct')
    assert b['export']['sha256'] == B.STEP544_SHA and b['groups'] == [
        'object_counting', 'object_size_estimation', 'object_rel_distance', 'object_rel_direction',
        'route_planning', 'obj_appearance_order'] and b['items'] == 4008 and b['arms'] == ['primary']
    r = bind('revsi999t32', 'step544', 'direct')
    assert r['items'] == 679 and len(r['groups']) == 5
    assert len(b['binding_sha256']) == 64


def test_done_needs_matching_init_selection(tmp_path):
    with pytest.raises(B.BindError, match='init-selection'):
        bind('vsibench5130', 'done:' + str(_done(tmp_path)), 'direct')
    with pytest.raises(B.BindError, match='did not select'):
        bind('vsibench5130', 'done:' + str(_done(tmp_path)), 'direct', init_selection=_sel(tmp_path, 'b' * 64))
    b = bind('vsibench5130', 'done:' + str(_done(tmp_path)), 'direct', init_selection=_sel(tmp_path))
    assert b['export']['kind'] == 'done' and b['export']['sha256'] == D0_SHA


@pytest.mark.parametrize('text', ['x 1', 'gs://b/x 1 ' + 'a' * 64, 'x -1 ' + 'a' * 64, 'x 1 ' + 'A' * 64, 'x 1 ab'])
def test_malformed_done_refused(tmp_path, text):
    p = tmp_path / 'm.done'; p.write_text(text)
    with pytest.raises(B.BindError):
        bind('vsibench5130', 'done:' + str(p), 'direct', init_selection=_sel(tmp_path))


def test_ledger_admits_one_d0_export_only(tmp_path):
    led = tmp_path / 'OFFICIAL_READ_LEDGER.jsonl'
    b = bind('vsibench5130', 'done:' + str(_done(tmp_path)), 'direct', init_selection=_sel(tmp_path), ledger=led)
    B.ledger_append(led, b)
    # same export, other benchmark: fine
    b2 = bind('revsi999t32', 'done:' + str(_done(tmp_path)), 'direct', init_selection=_sel(tmp_path), ledger=led)
    B.ledger_append(led, b2)
    # same export, same benchmark and reader, production again: refused
    with pytest.raises(B.BindError, match='already'):
        B.ledger_append(led, b)
    # a second D0 milestone: refused even with its own selection file
    other = tmp_path / 'o'; other.mkdir()
    with pytest.raises(B.BindError, match='another D0 export'):
        bind('vsibench5130', 'done:' + str(_done(other, 'c' * 64, 600)), 'direct',
               init_selection=_sel(other, 'c' * 64, 600), ledger=led)
    # step 544 is not a D0 milestone and stays admissible
    bind('vsibench5130', 'step544', 'direct', ledger=led)


def test_harness_refused_before_p8(tmp_path):
    with pytest.raises(B.BindError, match='freeze-file'):
        bind('vsibench5130', 'step544', 'harness:' + 'f' * 64)
    with pytest.raises(B.BindError, match='does not exist'):
        bind('vsibench5130', 'step544', 'harness:' + 'f' * 64, freeze_file=tmp_path / 'ROUTED_PATH_FROZEN_20261117.md')


def test_harness_binds_by_freeze_sha(tmp_path):
    p, sha = _freeze(tmp_path, dict(selector=dict(source='K1_refit', kill_rules_passed=True, sha256='e' * 64)))
    with pytest.raises(B.BindError, match='differs'):
        bind('vsibench5130', 'step544', 'harness:' + 'f' * 64, freeze_file=p)
    b = bind('vsibench5130', 'step544', 'harness:' + sha, freeze_file=p)
    assert b['reader']['eat1']['passed'] is False and b['items'] == 5130 and len(b['groups']) == 8
    assert b['arms'] == ['primary', 'secondary_fallback', 'secondary_room_unserved']
    bad = tmp_path / 'x'; bad.mkdir()
    q, qsha = _freeze(bad, {}, name='FROZEN.md')
    with pytest.raises(B.BindError, match='name'):
        bind('vsibench5130', 'step544', 'harness:' + qsha, freeze_file=q)
    nb = tmp_path / 'nb'; nb.mkdir()
    r = nb / 'ROUTED_PATH_FROZEN_20261117.md'; r.write_text('no machine block')
    with pytest.raises(B.BindError, match='json'):
        bind('vsibench5130', 'step544', 'harness:' + hashlib.sha256(r.read_bytes()).hexdigest(), freeze_file=r)


def test_revsi_harness_needs_k1_refit(tmp_path):
    p, sha = _freeze(tmp_path, dict(selector=dict(source='current_deployed', kill_rules_passed=False)))
    bind('vsibench5130', 'step544', 'harness:' + sha, freeze_file=p)  # VSI may use the current selector
    with pytest.raises(B.BindError, match='K1-refit'):
        bind('revsi999t32', 'step544', 'harness:' + sha, freeze_file=p)


def test_e2e_needs_eat1_pass_for_production(tmp_path):
    m = tmp_path / 'EXPORT_MANIFEST.json'; m.write_text('{"files": []}')
    sha = hashlib.sha256(m.read_bytes()).hexdigest()
    with pytest.raises(B.BindError, match='fixture mode only'):
        bind('vsibench5130', 'step544', 'e2e:' + sha, e2e_manifest=m)
    b = bind('vsibench5130', 'step544', 'e2e:' + sha, e2e_manifest=m, mode='fixture')
    assert b['reader']['eat1']['passed'] is None and b['arms'] == ['primary']
    rep = tmp_path / 'EAT1.json'
    rep.write_text(json.dumps(dict(manifest_sha256=sha, verdict='FAIL', clauses=dict(A1=dict(status='PASS'), A4=dict(status='FAIL')))))
    with pytest.raises(B.BindError, match='fixture mode only'):
        bind('vsibench5130', 'step544', 'e2e:' + sha, e2e_manifest=m, eat1_report=rep)
    rep.write_text(json.dumps(dict(manifest_sha256=sha, verdict='PASS', clauses={f'A{i}': dict(status='PASS') for i in range(1, 7)})))
    b = bind('vsibench5130', 'step544', 'e2e:' + sha, e2e_manifest=m, eat1_report=rep)
    assert b['reader']['eat1']['passed'] is True
    rep.write_text(json.dumps(dict(manifest_sha256='0' * 64, verdict='PASS', clauses={'A1': dict(status='PASS')})))
    with pytest.raises(B.BindError, match='another manifest'):
        bind('vsibench5130', 'step544', 'e2e:' + sha, e2e_manifest=m, eat1_report=rep)


def test_production_needs_a_ledger():
    with pytest.raises(B.BindError, match='ledger'):
        B.bind('vsibench5130', 'step544', 'direct', ledger=None)
    assert B.bind('vsibench5130', 'step544', 'direct', mode='proof')['mode'] == 'proof'


@pytest.mark.parametrize('over,step,match', [
    (dict(init_rule_sha256='0' * 64), 200, 'registered init rule'),
    (dict(selected_step=400), 200, 'candidate'),
    (dict(d0_ended={}), 200, 'D0 ended'),
    (dict(d0_ended=dict(reason='tired', event='x')), 200, 'D0 ended'),
    ({}, 100, 'candidate'),
    ({}, 50, 'candidate'),
])
def test_init_selection_is_validated(tmp_path, over, step, match):
    with pytest.raises(B.BindError, match=match):
        bind('vsibench5130', 'done:' + str(_done(tmp_path, step=step)), 'direct',
             init_selection=_sel(tmp_path, step=step, **over))


def test_d0_object_outside_lineage_refused(tmp_path):
    p = tmp_path / 'x.done'; p.write_text('q8/other/359fcc3c_m200.tar 1 ' + D0_SHA + '\n')
    with pytest.raises(B.BindError, match='lineage'):
        bind('vsibench5130', 'done:' + str(p), 'direct', init_selection=_sel(tmp_path))


def test_binding_carries_frames_and_hashes_them():
    a = bind('vsibench5130', 'step544', 'direct')
    assert a['frames']['count'] == 32 and a['frames']['layout'] == 'duplicate'
    with pytest.raises(B.BindError, match='differs from the trained'):
        bind('vsibench5130', 'step544', 'direct', frames=(64, 'spread'))
    o = bind('vsibench5130', 'step544', 'direct', frames=(64, 'spread'), frames_override_reason='probe')
    assert o['binding_sha256'] != a['binding_sha256'] and o['frames']['layout_override_reason'] == 'probe'
    assert B.verify_binding(a) is a
