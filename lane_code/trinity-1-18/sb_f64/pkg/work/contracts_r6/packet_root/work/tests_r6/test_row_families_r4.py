"""Regressions for lifted points, sensor providers and structured event admission."""
import copy
import json
from pathlib import Path
import pytest
from fixtures_contracts import fixture, masks
from trace_format.contracts import contract_epoch
from student_pilot.training_contract import audit_training_contract, call_responses

L=Path(__file__).resolve().parents[2]
W=L/'work/row_families_r5'

def test_bare_ground_off_parity():
    from student_pilot import ground_lifting
    from generator.derivgen_v7.derivgen.ground_v312 import Session, render
    base=json.loads((W/'off_parity_reproduction.json').read_text())['arms']['base']['row']
    with contract_epoch(False):
        s=Session(ground_lifting,fixture('landscape')[1](),lambda n:(masks(n).masks,[1.]*32))
        item=dict(qid='bare-ground-regression',type='object_abs_distance',question='How far is the chair from the table?',options=[],roles=dict(a='chair',b='table'))
        assert render(item,s,lambda text:len(text.split())) == base

@pytest.mark.parametrize('enabled',[False,True])
def test_sensor_provider_contract(enabled):
    from student_pilot import ground_lifting
    from generator.derivgen_v7.derivgen.ground_v313 import Session
    base=json.loads((W/'provider_reproduction.json').read_text())['arms']['base']
    with contract_epoch(enabled):
        s=Session(ground_lifting,fixture('landscape')[1](),None,
            instances=lambda n:[dict(instance_id='1',masks=masks(n).masks,prob=[1.]*32)],
            multi_instance=False,keypoint_calls=True,geometry_mode='sensor')
        s.execute('<ground obj="chair">')
        assert s.box_provider_id == base['provider']
        assert s.events[0] == base['event']

def test_generator_registry_accepts_heading():
    from generator.derivgen_v7.derivgen.calculator import PrintedPointRegistry, CalculatorError
    for enabled in (False,True):
        with contract_epoch(enabled):
            registry=PrintedPointRegistry()
            extra={'heading_defined':False} if enabled else {}
            point=registry.register(camera=[1,2,3],f1=[4,5,6],spread=0,requested_frame=2,**extra)
            assert ('heading unavailable' in point['line']) == enabled
            assert ('heading_defined' in registry._points['P1']) == enabled
            with pytest.raises(CalculatorError):
                registry.execute('<dist P1 P2>')

def point_rows():
    return [r['row'] for r in json.loads((W/'base.json').read_text())['results']
            if r['family'].startswith('point_program/') and r['status']=='rendered']

def test_structured_point_program_admission():
    from generator.derivgen_v7.derivgen.trace import render_with_spans
    rows=point_rows()
    assert rows
    for row in rows:
        with contract_epoch(True):
            assert audit_training_contract([row]) == [None], row['qid']
            assert audit_training_contract([dict(routing=row,target=row['target'])]) == [None]
            pairs=list(call_responses(row))
            for call,text in pairs:
                assert call and text
                assert text in row['target'], (row['qid'],call)
            projection=render_with_spans(row['events'],row['answer'])
            assert projection['target'] == row['target']
            assert projection['tool_output_spans'] == row['tool_output_spans']

def test_point_program_pool_gate():
    from student_pilot.s1_pool import validate_source_row
    from student_pilot.carrier_c1_routing import check_row
    for row in point_rows():
        with pytest.raises(ValueError): validate_source_row(row,'packed')
        with pytest.raises(ValueError): check_row(row)

@pytest.mark.parametrize('damage',['missing','wrong_id','orphan','wrong_name','bad_values'])
def test_structured_response_integrity(damage):
    row=copy.deepcopy(next(r for r in point_rows() if r['question_type']=='absolute_distance_object'))
    events=row['events'];idx=next(i for i,e in enumerate(events) if e['kind']=='tool_response')
    if damage=='missing': events[idx:idx+1]=[]
    elif damage=='wrong_id': events[idx]['call_id']='unbound'
    elif damage=='orphan': events[idx-1:idx]=[]
    elif damage=='wrong_name': events[idx]['name']='other'
    else: events[idx]['values']={}
    assert audit_training_contract([row])[0] in ('contract_malformed_row','contract_missing_response')

def test_combined_response_envelope():
    row=dict(events=[dict(call='<move from=1 to=2>',response=dict(injected_text='distance = 1.00 m'))])
    assert audit_training_contract([row]) == [None]
    row['events'][0]['response']['injected_text']='head readout unavailable'
    assert audit_training_contract([row]) == ['contract_operator_fault']

def test_legacy_scalar_gap_audit():
    from student_pilot.live_trace313 import parse_response
    call='<gap a="chair" b="table">'
    row=dict(spec_version='3.12.2', events=[dict(call=call,response='1.88 m')])
    assert audit_training_contract([row]) == ['contract_unknown_status']
    assert audit_training_contract([dict(routing=row)]) == ['contract_unknown_status']
    with pytest.raises(ValueError): parse_response(call,'1.88 m','3.14')
    with pytest.raises(ValueError): parse_response(call,'bogus','3.12.2')

def test_real_source_candidates():
    from student_pilot.phrases import candidate_phrases, normalize_phrase
    cases=json.loads(Path(__file__).with_name('real_candidate_cases_r4.json').read_text())
    assert cases
    for case in cases:
        row=case['row']
        assert audit_training_contract([row]) == [None], (case['source'],case['line'],row['qid'])
        candidates=candidate_phrases(row['question'],row.get('options',[]))
        for key,name in row['roles'].items():
            if isinstance(name,str) and key != 'parser':
                assert normalize_phrase(name) in candidates
        # Generated calls cannot expand the fixed cache universe.
        cached=dict(row,uses_mask_cache=True,candidate_manifest=['unrelated object'])
        assert audit_training_contract([cached]) == ['contract_operand_outside_candidates']
        altered=copy.deepcopy(row)
        for event in altered['events']:
            for key in ('call','token'):
                if event.get(key,'').startswith('<ground obj='):
                    import re
                    event[key]=re.sub(r'obj="[^"]+"','obj="unrelated object"',event[key])
                    break
            else:
                continue
            break
        assert audit_training_contract([altered]) == ['contract_operand_outside_candidates']
