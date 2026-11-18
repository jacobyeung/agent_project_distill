"""Malformed status records and retained scene exclusions use the real gates."""
import json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';T=L/'work/tree_r1';O=B/'proofs/gate_edges'
O.mkdir(exist_ok=True);sys.path[:0]=[str(T),str(B)]
from monitor9 import Monitor
monitor=Monitor(T)
from student_pilot.row_text_audit import reasons,recorded_responses
from student_pilot.scene_division_gate import check_rows
from student_pilot.s1_exclusions import Exclusions,dev_names
from student_pilot.p3_provenance import file_pin,load
for text in ('prefix<tool_response>not seen', '<tool_response><tool_response>not seen</tool_response>', '<tool_response>not seen</tool_response>'):
    assert not recorded_responses({},text)
text='<tool_response>not seen</tool_response>'
assert not recorded_responses(dict(tool_output_spans=[dict(start=0,end=len(text))]),text)
assert 'tower_scale_provenance_not_from_head' in reasons(dict(ground_record=dict(geometry_mode='tower')))
assert reasons(dict(target='heading\u00a0unavailable'))==[], 'Unrelated heading pattern broadened'
dev=file_pin(T/'student_pilot/r2_dev_merged.json')
benchmark=file_pin(L/'fixtures/work/records/revsi_dev/BENCH_SCENE_EXCLUSIONS_v2.json')
rule=Exclusions(dev,benchmark)
name=dev_names(dev)[0];dataset,scene=name.split('/',1)
row=dict(qid='excluded_fixture',dataset=dataset,scene=scene)
path=O/'division.json';path.write_text(json.dumps(dict(train_scenes=[],heldout_scenes=[])))
result=check_rows([row],file_pin(path),scene_filter=rule)
assert result['filtered']==1 and result['outside']==0
(O/'RESULT.json').write_text(json.dumps(dict(status='PASS',scene_filter=result,dev=dev,benchmark=benchmark,
    scope='Real retained exclusion and status predicates; malformed synthetic text records; no RGB/head execution.'),indent=2)+'\n')
monitor.save(O);print(json.dumps(result))
