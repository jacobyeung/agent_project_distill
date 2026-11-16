"""Scorer check: the kit's aggregation reproduces the accepted direct reads of step 544
(VSI-Bench six tasks 68.77 [66.5, 71.0]; ReVSI five categories 64.94 [61.3, 68.4]) from the raw
budget_2048 rows of the accepted returns, to every printed digit and every interval endpoint."""
import json
import os
from pathlib import Path

import pytest

from offkit import report as R
from offkit.adapt_direct import from_return

IN = Path(os.environ.get('OFFKIT_IN', '/scratch/jjyeung/orch_n30/b07_offread/in'))
need = pytest.mark.skipif(not (IN / 'ret_vsi/a0').exists(), reason='accepted returns not staged')


def _cohort(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def _accepted(path):
    return json.load(open(path))


@need
def test_vsi_six_task_reproduces_68_77():
    cohort = _cohort(IN / 'kit_revsi/cohort/COHORT_OFFICIAL6.jsonl')
    meta = {r['id']: r for r in _cohort(IN / 'kit_revsi/cohort/meta_5130.jsonl')}
    cohort = [dict(r, question=meta[r['id']]['question']) for r in cohort]
    items = from_return(IN / 'ret_vsi/a0', 2048)
    rep = R.aggregate(R.ReadMode('vsibench5130', 'direct'), cohort, items)
    acc = _accepted(IN / 'ret_vsi/report/B2048.json')
    assert rep['items'] == 4008 and rep['scenes'] == 288
    assert round(100 * rep['headline']['score'], 2) == 68.77
    assert rep['headline']['score'] == pytest.approx(acc['six_task_mean']['score'], abs=1e-12)
    assert rep['headline']['percentile_95'] == pytest.approx(acc['six_task_mean']['percentile_95'], abs=1e-12)
    for g, r in acc['groups'].items():
        assert rep['groups'][g]['score'] == pytest.approx(r['score'], abs=1e-12), g
        assert rep['groups'][g]['percentile_95'] == pytest.approx(r['percentile_95'], abs=1e-12), g
    assert rep['not_read'] == ['object_abs_distance', 'room_size_estimation']
    assert sum(r['forced_closes'] for r in rep['groups'].values()) == 12


@need
def test_revsi_five_category_reproduces_64_94():
    cohort = _cohort(IN / 'kit_revsi/cohort/c5.jsonl')
    items = from_return(IN / 'ret_revsi/a0', 2048)
    rep = R.aggregate(R.ReadMode('revsi999t32', 'direct'), cohort, items)
    acc = _accepted(IN / 'ret_revsi/report/B2048.json')
    assert rep['items'] == 679 and rep['scenes'] == 261
    assert round(100 * rep['headline']['score'], 2) == 64.94
    assert rep['headline']['score'] == pytest.approx(acc['five_category_mean']['score'], abs=1e-12)
    assert rep['headline']['percentile_95'] == pytest.approx(acc['five_category_mean']['percentile_95'], abs=1e-12)
    for g, r in acc['groups'].items():
        assert rep['groups'][g]['score'] == pytest.approx(r['score'], abs=1e-12), g
        assert rep['groups'][g]['percentile_95'] == pytest.approx(r['percentile_95'], abs=1e-12), g
    for label, r in acc['direction_by_question_text'].items():
        assert rep['direction_by_question_text'][label]['score'] == pytest.approx(r['score'], abs=1e-12)
        assert rep['direction_by_question_text'][label]['percentile_95'] == pytest.approx(r['percentile_95'], abs=1e-12)
