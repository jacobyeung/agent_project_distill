from pathlib import Path
import json
import pytest
from offnative.paths import ROOT
from offnative.rehearse import run
from offnative.worker import PhaseFailure
from offnative.io import load, rows

@pytest.mark.parametrize('kind',['harness','e2e'])
def test_rehearsed_result(kind):
    d=ROOT/'work'/('n2_rehearsal_'+kind+'_release')
    result=load(d/'RESULT.json')
    assert result['passed'] and result['items']==26 and result['videos']==2
    assert len(list((d/'return/receipts').glob('*.json')))==7
    primary=rows(d/'return/primary.jsonl')
    assert len(primary)==26
    if kind=='harness':
        fallback=rows(d/'return/secondary_fallback.jsonl')
        assert any(a['refusal'] and a['score']>=0 and b['score']==1 for a,b in zip(primary,fallback))
    for p in (d/'reports').glob('*.txt'):
        first=p.read_text().splitlines()[0]
        assert 'READER '+kind in first and 'EAT-1' in first
        if kind=='harness':assert 'harness-served, not an end-to-end result' in first

def test_changed_response_stops_before_official_decode(tmp_path):
    d=tmp_path/'mutated'
    with pytest.raises(PhaseFailure):run(d,'harness',mutate_proof=True)
    receipt=load(d/'return/receipts/03.json')
    assert receipt['status']=='FAIL' and receipt['official_decodes']==0
    assert not (d/'return/decode.jsonl').exists()
    assert not (d/'return/receipts/04.json').exists()

def test_fixture_cannot_claim_production(tmp_path):
    from offnative.worker import Worker
    from types import SimpleNamespace
    source=ROOT/'work/n2_rehearsal_e2e_release'
    b=load(source/'BINDING.json');c=load(source/'CONFIG.json')
    with pytest.raises(ValueError,match='synthetic status'):
        Worker(c,b,[],SimpleNamespace(synthetic=True),None,tmp_path/'out',fixture=False)
