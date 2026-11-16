"""Fixture runs of the report layer in every reader mode, denominators and labels.

Cohorts are the real official item lists with every answer field removed (id, type, dataset,
scene, question text only); scores are synthetic."""
import json
import os
import random
from pathlib import Path

import pytest

from offkit import bind as B
from offkit import frames as F
from offkit import report as R

IN = Path(os.environ.get('OFFKIT_IN', '/scratch/jjyeung/orch_n30/b07_offread/in'))
KEEP = ('id', 'question_type', 'dataset', 'scene_name', 'question')
need = pytest.mark.skipif(not (IN / 'kit_revsi/cohort/meta_5130.jsonl').exists(), reason='cohorts not staged')


def _strip(rows):
    return [{k: str(r[k]) if k == 'id' else r[k] for k in KEEP} for r in rows]


def vsi_cohort():
    return _strip(json.loads(l) for l in open(IN / 'kit_revsi/cohort/meta_5130.jsonl'))


def revsi_cohort():
    return _strip(json.load(open(IN / 'kit_revsi/inputs/i1.json')))


def synth(cohort, seed=1, *, refuse_every=0, call_types=()):
    rnd = random.Random(seed)
    out = []
    for i, r in enumerate(cohort):
        calls = 1 if r['question_type'] in call_types else 0
        out.append(dict(id=r['id'], question_type=r['question_type'], score=rnd.random(), status='complete',
                        refusal=bool(refuse_every and i % refuse_every == 0), forced_close=(i % 97 == 0),
                        calls=calls, calls_served=calls))
    return out


READER = dict(direct=dict(kind='direct', id='direct kit f42aa1a4', eat1=dict(passed=None)),
              harness=dict(kind='harness', id='P8 fixture', eat1=dict(passed=False)),
              e2e=dict(kind='e2e', id='e2e fixture', eat1=dict(passed=True)),
              e2e_fail=dict(kind='e2e', id='e2e fixture', eat1=dict(passed=False)))
EXPORT = dict(kind='step544', sha256=B.STEP544_SHA)
ARMS = dict(direct=['primary'], harness=['primary', 'secondary_fallback', 'secondary_room_unserved'],
            e2e=['primary'], e2e_fail=['primary'])


def binding(bench, reader, mode='production', **frames):
    body = dict(schema='offkit-binding-v1', benchmark=bench, mode=mode, reader=READER[reader], export=EXPORT,
                arms=ARMS[reader], frames=F.bind_frames(**frames))
    body['binding_sha256'] = B.binding_sha256(body)
    return body


@need
@pytest.mark.parametrize('bench,cohort_fn,items,scenes,groups', [
    ('vsibench5130', vsi_cohort, 5130, 288, 8), ('revsi999t32', revsi_cohort, 999, 302, 7)])
@pytest.mark.parametrize('reader', ['harness', 'e2e'])
def test_full_read_denominators_and_labels(bench, cohort_fn, items, scenes, groups, reader, tmp_path):
    cohort = cohort_fn()
    mode = R.ReadMode(bench, reader)
    rows = synth(cohort, refuse_every=50, call_types=('object_abs_distance', 'room_size_estimation',
                                                      'room_size_estimation_single', 'room_size_estimation_multiple'))
    rep = R.aggregate(mode, cohort, rows, repetitions=200)
    assert rep['items'] == items and rep['scenes'] == scenes and len(rep['groups']) == groups
    assert sum(g['items'] for g in rep['groups'].values()) == items
    assert rep['not_read'] == []
    assert rep['groups']['object_abs_distance']['call_rate'] == 1.0
    assert rep['groups']['object_counting']['call_rate'] == 0.0
    assert sum(g['refusals'] for g in rep['groups'].values()) == len(range(0, items, 50))
    assert set(rep['by_asked_unit']) == {'object_abs_distance', 'room_size_estimation'}
    lab = R.label_report(rep, binding=binding(bench, reader), arm='primary', role='primary')
    text = R.render(lab)
    first = text.splitlines()[0]
    assert first.startswith(f'READER {reader} ') and 'EAT-1 ' in first
    if reader == 'harness':
        assert 'EAT-1 FAILED' in first
        score_lines = [l for l in text.splitlines()[1:] if '%' in l or 'CI' in l]
        assert score_lines and all(R.HARNESS_WORDS in l for l in score_lines if l[:1] != ' ')
        assert R.ROOM_PRIMARY_LABEL in text and R.DISTANCE_DISCLOSURE in text
    else:
        assert 'EAT-1 PASSED' in first and R.HARNESS_WORDS not in text
    R.write(lab, tmp_path, 'primary')
    assert json.loads((tmp_path / 'primary.json').read_text())['first_line'] == first


@need
def test_e2e_without_pass_is_marked_unclaimable():
    cohort = vsi_cohort()
    rep = R.aggregate(R.ReadMode('vsibench5130', 'e2e'), cohort, synth(cohort), repetitions=50)
    text = R.render(R.label_report(rep, binding=binding('vsibench5130', 'e2e_fail'), arm='primary', role='primary'))
    assert 'EAT-1 FAILED' in text.splitlines()[0] and 'not a claimable result' in text.splitlines()[0]


@need
def test_missing_items_score_zero_inside_denominator():
    cohort = vsi_cohort()
    rows = synth(cohort)
    full = R.aggregate(R.ReadMode('vsibench5130', 'harness'), cohort, rows, repetitions=50)
    dropped = [r for r in rows if r['question_type'] != 'route_planning']
    part = R.aggregate(R.ReadMode('vsibench5130', 'harness'), cohort, dropped, repetitions=50)
    assert part['items'] == 5130
    assert part['groups']['route_planning']['score'] == 0.0
    assert part['groups']['route_planning']['errors'] == 194
    assert part['headline']['score'] < full['headline']['score']


@need
@pytest.mark.parametrize('bench,cohort_fn', [('vsibench5130', vsi_cohort), ('revsi999t32', revsi_cohort)])
def test_unread_type_impossible(bench, cohort_fn):
    cohort = cohort_fn()
    t = 'room_size_estimation' if bench == 'vsibench5130' else 'room_size_estimation_multiple'
    with pytest.raises(ValueError, match='requires|unread'):
        R.aggregate(R.ReadMode(bench, 'harness'), [r for r in cohort if r['question_type'] != t], [], repetitions=10)
    short = cohort[:-1]
    with pytest.raises(ValueError, match='requires'):
        R.aggregate(R.ReadMode(bench, 'harness'), short, [], repetitions=10)


@need
def test_direct_mode_refuses_routed_items_and_reports_not_read():
    cohort = vsi_cohort()
    with pytest.raises(ValueError):
        R.aggregate(R.ReadMode('vsibench5130', 'direct'), cohort, [], repetitions=10)
    six = [r for r in cohort if r['question_type'] not in ('object_abs_distance', 'room_size_estimation')]
    assert len(six) == 4008
    rep = R.aggregate(R.ReadMode('vsibench5130', 'direct'), six, synth(six), repetitions=10)
    lab = R.label_report(rep, binding=binding('vsibench5130', 'direct'), arm='primary', role='primary')
    text = R.render(lab)
    assert 'object_abs_distance: not read by this reader' in text
    assert 'not the eight-task mean' in text and 'direct-only' in text.splitlines()[0]


@need
def test_foreign_and_duplicate_items_refused():
    cohort = revsi_cohort()
    rows = synth(cohort)
    with pytest.raises(ValueError, match='duplicate'):
        R.aggregate(R.ReadMode('revsi999t32', 'harness'), cohort, rows + rows[:1], repetitions=10)
    with pytest.raises(ValueError, match='outside the cohort'):
        R.aggregate(R.ReadMode('revsi999t32', 'harness'), cohort, rows + [dict(rows[0], id='zz')], repetitions=10)
    bad = [dict(r) for r in rows]; bad[0]['score'] = 1.5
    with pytest.raises(ValueError, match='invalid'):
        R.aggregate(R.ReadMode('revsi999t32', 'harness'), cohort, bad, repetitions=10)


@need
def test_official_aggregation_equal_subtype_then_group_means():
    cohort = revsi_cohort()
    rows = []
    for r in cohort:
        # every item of subtype backward_* scores 1, forward_* 0: direction = 0.5 regardless of counts
        s = 1.0 if 'backward' in r['question_type'] else 0.0
        rows.append(dict(id=r['id'], question_type=r['question_type'], score=s, status='complete'))
    rep = R.aggregate(R.ReadMode('revsi999t32', 'harness'), cohort, rows, repetitions=10)
    assert rep['groups']['object_rel_direction']['score'] == 0.5
    assert rep['headline']['score'] == pytest.approx(0.5 / 7)
    cohort = vsi_cohort()
    rows = [dict(id=r['id'], question_type=r['question_type'], status='complete',
                 score=1.0 if r['question_type'] == 'object_rel_direction_easy' else 0.0) for r in cohort]
    rep = R.aggregate(R.ReadMode('vsibench5130', 'harness'), cohort, rows, repetitions=10)
    assert rep['groups']['object_rel_direction']['score'] == pytest.approx(1 / 3)
    assert rep['headline']['score'] == pytest.approx(1 / 24)


def test_asked_unit_parser():
    q = 'what is the distance between the table and the bathtub (in meters)?'
    assert R.asked_unit(q) == 'meters'
    assert R.asked_unit('What is the size of this room (in square meters)?') == 'square_meters'
    assert R.asked_unit('What is the size of this room (in square feet)?') == 'square_feet'
    assert R.asked_unit('how far apart are they (in centimeters)?') == 'centimeters'
    assert R.asked_unit('how far apart are they (in feet)?') == 'feet'
    assert R.asked_unit('how far apart are they (in inches)?') == 'inches'
    assert R.asked_unit('how far apart are they?') == 'unstated'


@need
def test_official_unit_census():
    from collections import Counter
    v = Counter(R.asked_unit(r['question']) for r in vsi_cohort() if r['question_type'] in ('object_abs_distance', 'room_size_estimation'))
    assert v == Counter(meters=834, square_meters=288)
    rv = Counter(R.asked_unit(r['question']) for r in revsi_cohort() if r['question_type'].startswith(('object_abs', 'room_size')))
    assert sum(rv.values()) == 320 and rv['unstated'] == 0


@need
def test_label_comes_from_a_verified_matching_binding():
    cohort = vsi_cohort()
    rep = R.aggregate(R.ReadMode('vsibench5130', 'harness'), cohort, synth(cohort), repetitions=20)
    with pytest.raises(ValueError, match='differs from the aggregate reader'):
        R.label_report(rep, binding=binding('vsibench5130', 'e2e'), arm='primary', role='primary')
    with pytest.raises(ValueError, match='benchmark'):
        R.label_report(rep, binding=binding('revsi999t32', 'harness'), arm='primary', role='primary')
    tampered = binding('vsibench5130', 'harness')
    tampered['reader'] = dict(tampered['reader'], kind='e2e')
    with pytest.raises(ValueError, match='binding_sha256'):
        R.label_report(rep, binding=tampered, arm='primary', role='primary')
    unknown = binding('vsibench5130', 'harness')
    unknown['reader'] = dict(unknown['reader'], kind='Harness')
    unknown['binding_sha256'] = B.binding_sha256(unknown)
    with pytest.raises(ValueError, match='unknown reader kind'):
        R.label_report(rep, binding=unknown, arm='primary', role='primary')
    with pytest.raises(ValueError, match='not an arm'):
        R.label_report(rep, binding=binding('vsibench5130', 'harness'), arm='scripted', role='primary')


@need
def test_mode_and_frame_override_are_printed():
    cohort = vsi_cohort()
    rep = R.aggregate(R.ReadMode('vsibench5130', 'e2e'), cohort, synth(cohort), repetitions=20)
    first = R.label_report(rep, binding=binding('vsibench5130', 'e2e', mode='fixture', count=64, layout='spread',
                                                override_reason='layout probe'), arm='primary', role='primary')['first_line']
    assert 'MODE fixture' in first and 'fixture binding: not a benchmark result' in first
    assert 'FRAMES 64 spread' in first and 'frame layout differs from training: layout probe' in first
