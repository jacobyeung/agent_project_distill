from copy import deepcopy
from pathlib import Path
import json
import pytest
from offnative.io import dump, sha, owned, digest
from offnative.paths import ROOT
from offnative.cohort import cohort, media302, name_inventory, canary, operands
from offnative.scoring import Scorer
from offnative.worker import merge, arms
from offnative.proof import compare
from offkit.report import ReadMode, check_cohort
from offkit.bind import bind, BindError

@pytest.fixture
def full():return cohort('revsi999t32')

def test_cohort_membership_and_unread_type(full):
    mode=ReadMode('revsi999t32','harness');check_cohort(mode,full)
    with pytest.raises(ValueError):check_cohort(mode,full[:-1])
    changed=deepcopy(full)
    for row in changed:
        if row['question_type']=='object_abs_distance':row['question_type']='object_size_estimation'
    with pytest.raises(ValueError):check_cohort(mode,changed)
    ids=[str(r['example_id']) for r in full]
    records=[dict(id=k) for k in ids]
    assert len(merge(ids,[records[::2],records[1::2]]))==999
    for bad in (records[:-1],records+[records[0]]):
        with pytest.raises(ValueError):merge(ids,[bad])

def test_media_and_canary(full):
    need=media302(full)
    assert len(need)==302
    added=[r for r in need if r['upload_required']]
    assert len(added)==41 and sum(r['source'] is None for r in added)==17
    assert len(canary(full,ReadMode('revsi999t32','harness')))==10
    assert name_inventory(full)['unresolved']==[]
    assert operands('What is the distance between the wall picture and the microwave (in meters)?')==['wall picture','microwave']
    assert operands('Unrecognized wording') is None

def test_refused_distance_fallback():
    items=[dict(id='1',question_type='object_abs_distance'),dict(id='2',question_type='room_size_estimation_single')]
    primary=[dict(id='1',score=0,refusal=True),dict(id='2',score=.5,refusal=False)]
    unserved=[dict(id='1',score=1,refusal=False),dict(id='2',score=.2,refusal=False)]
    out=arms(primary,unserved,items,'harness')
    assert out['primary'][0]['score']==0
    assert out['secondary_fallback'][0]['score']==1
    assert out['secondary_room_unserved'][0]['score']==0
    assert out['secondary_room_unserved'][1]['score']==.2
    with pytest.raises(ValueError):arms(primary,unserved[1:],items,'harness')

def test_answer_bytes_reach_official_scorer(tmp_path,monkeypatch):
    import offnative.scoring as scoring
    p=tmp_path/'labels.json';dump(p,[dict(id='1',example_id='1',question_type='object_abs_distance',ground_truth='2')])
    native=scoring.evaluator();seen=[];original=native.score_item
    def spy(task,raw,*args,**kw):seen.append(raw.encode());return original(task,raw,*args,**kw)
    monkeypatch.setattr(native,'score_item',spy)
    raw='<think>value is in metres</think>\n 2.000 ft \n'
    record=Scorer(p).score(dict(id='1',question_type='object_abs_distance'),dict(text=raw,tokens=[],calls=[]),'primary')
    assert seen==[raw.encode()]
    assert record['model_text'].encode()==raw.encode()
    assert record['score']==1

def test_bind_rejects_unfrozen_and_wrong_selector(tmp_path):
    with pytest.raises(BindError):bind('revsi999t32','step544','harness:'+'0'*64)
    p=tmp_path/'ROUTED_PATH_FROZEN_20261116.md'
    p.write_text('```json\n'+json.dumps({'freeze_values':{'selector':{'source':'VSTI'}}})+'\n```\n')
    with pytest.raises(BindError):bind('revsi999t32','step544','harness:'+sha(p),freeze_file=p)

def test_bind_eat1_production(tmp_path):
    p=tmp_path/'e2e.json';dump(p,{'fixture':True})
    with pytest.raises(BindError):bind('revsi999t32','step544','e2e:'+sha(p),e2e_manifest=p)
    assert bind('revsi999t32','step544','e2e:'+sha(p),e2e_manifest=p,mode='fixture')['reader']['kind']=='e2e'

def test_e2e_proof_requires_camera_only():
    d=dict(tokens=[1],text='a',calls=[dict(call='c',response='r')])
    ref=[dict(key='1',question_type='camera_displacement',decode=deepcopy(d)),dict(key='2',question_type='object_abs_distance',decode=deepcopy(d))]
    actual=deepcopy(ref);actual[1]['decode']['calls'][0]['response']='changed'
    assert compare(ref,actual,'e2e')['passed']
    assert not compare(ref,actual,'harness')['passed']
    actual[0]['decode']['tokens']=[2]
    assert not compare(ref,actual,'e2e')['passed']

def test_writes_cannot_escape():
    with pytest.raises(ValueError):owned(ROOT.parent/'outside')

def test_unserved_call_is_not_counted_as_served(tmp_path):
    p=tmp_path/'labels.json';dump(p,[dict(id='1',example_id='1',question_type='object_abs_distance',ground_truth='2')])
    rec=Scorer(p).score(dict(id='1',question_type='object_abs_distance'),
        dict(text='<think>look</think>\n2',tokens=[],calls=[dict(call='<ground mode="room">',served=False)]),'primary')
    assert rec['calls']==1 and rec['calls_served']==0
