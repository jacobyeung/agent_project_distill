"""Admission and reduced-proof regressions use synthetic values only."""
from copy import deepcopy
import json
import pytest
from offnative.paths import ROOT
from offnative.io import load, sha
from offnative.proof import (compare, loss_record, LOSS_RECORD_SHA256, verify_served)
from offnative.scoring import Scorer


def pin():
    return {'path':str(ROOT/'out/PROOF_MASKS_LOST.json'),'sha256':LOSS_RECORD_SHA256}


def reference():
    keys=load(ROOT/'out/PROOF_KEYS.json')['keys']
    decoded={'text':'<think>x</think>2','tokens':[1,2],
             'calls':[{'call':'<ground obj="chair">','response':'2 m'}],
             'heads':{'ground_queries':[{'name':'chair','points':[1,2]}]}}
    return [dict(key=r['key'],question_type=r['question_type'],decode=deepcopy(decoded),
                 independent_responses=r['question_type']!='object_abs_distance') for r in keys]


@pytest.mark.parametrize('decoded,arm',[
    ({'script_mode':False},'primary'), ({'script_answer':''},'primary'),
    ("{'script_mode': 'native'}",'primary'), ('{"script_answer": null}', 'primary'),
    ({},' SCRIPTED '), ({},'ScRiPtEd')])
def test_scorer_rejects_scripted_before_labels(tmp_path,decoded,arm):
    # An absent labels file proves refusal happens before scorer or label access.
    with pytest.raises(ValueError,match='script'):
        Scorer(tmp_path/'never_open_labels.json').score(
            {'id':'1','question_type':'object_abs_distance'},decoded,arm)


def test_reduced_proof_requires_pinned_loss(tmp_path):
    rows=reference()
    with pytest.raises(ValueError,match='pinned lost-mask'):
        compare(rows,rows,'harness',mode='reduced')
    bad=tmp_path/'loss.json';bad.write_text((ROOT/'out/PROOF_MASKS_LOST.json').read_text()+' ')
    with pytest.raises(ValueError,match='content differs'):
        loss_record({'path':str(bad),'sha256':LOSS_RECORD_SHA256})
    with pytest.raises(ValueError,match='pinned lost-mask'):
        loss_record({'path':str(bad),'sha256':sha(bad)})


@pytest.mark.parametrize('kind',['harness','e2e'])
def test_reduced_proof_requires_only_camera(kind):
    rows=reference()
    result=compare(rows,rows,kind,mode='reduced',loss_pin=pin())
    assert result['passed'] and result['mode']=='reduced'
    assert sum(c['required'] for c in result['checks'])==5
    changed=deepcopy(rows);changed[5]['decode']['tokens']=[99]
    assert compare(rows,changed,kind,mode='reduced',loss_pin=pin())['passed']


@pytest.mark.parametrize('field',['response','query','answer','call','independent_camera','missing_digest'])
def test_reduced_proof_catches_mutation(field):
    rows=reference();changed=deepcopy(rows)
    d=changed[5]['decode']
    if field=='response':d['calls'][0]['response']='3 m'
    if field=='query':d['heads']['ground_queries'][0]['points']=[9]
    if field=='answer':d['text']='<think>x</think>3'
    if field=='call':d['calls'][0]['call']='<ground obj="table">'
    if field=='independent_camera':changed[0]['independent_responses']=False
    if field=='missing_digest':
        rows[5]['decode']['heads']={};d['heads']={}
    result=compare(rows,changed,'harness',mode='reduced',loss_pin=pin())
    assert result['passed'] == (field!='independent_camera')


def test_reduced_proof_rejects_other_distance_selection():
    rows=reference();rows[5]['key']='different'
    with pytest.raises(ValueError,match='selected distance'):
        compare(rows,rows,'harness',mode='reduced',loss_pin=pin())


def test_distance_replay_has_no_silent_reduced_mode():
    from offnative.replay import replay_row
    row=reference()[5]
    with pytest.raises(ValueError,match='explicit reduced'):
        replay_row(row,None,{})
    with pytest.raises(ValueError,match='pinned lost-mask'):
        replay_row(row,None,{},mode='reduced')


def test_reduced_loss_is_shipped_and_pinned():
    from offnative.portable import sources
    files,pins=sources()
    assert files['out/PROOF_MASKS_LOST.json']==(ROOT/'out/PROOF_MASKS_LOST.json').read_bytes()
    assert sha(ROOT/'out/PROOF_MASKS_LOST.json')==LOSS_RECORD_SHA256
