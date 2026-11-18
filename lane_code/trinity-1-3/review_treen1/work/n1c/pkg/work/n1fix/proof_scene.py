"""Check the supplied exclusion keys against the exact production division."""
from pathlib import Path
from collections import Counter
import json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix';P=B/'proofs/division';P.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
from monitor9 import Monitor
monitor=Monitor(L/'work/tree_r1')
from student_pilot.p3_provenance import pinned,load,file_pin
from student_pilot.scene_division_gate import check_rows
from student_pilot.row_removals import Removals
binding=load(B/'F6_BINDING.json');source=pinned(binding['remove']);records=[json.loads(line) for line in source.read_text().splitlines()]
division=load(pinned(binding['division']));train=set(division['train_scenes']);heldout=set(division['heldout_scenes'])
counts=Counter();types=Counter();keys=set();metadata=[]
for record in records:
    scene=record['scene'];assert scene not in train and scene not in heldout
    assert record['row_key'] not in keys;keys.add(record['row_key']);counts[record['pool']]+=1;types[record['question_type']]+=1
    dataset,scene=scene.split('/',1);metadata.append(dict(qid=record['row_key'],dataset=dataset,scene=scene))
assert len(keys)==601
try:check_rows(metadata,binding['division'])
except ValueError as error:without=str(error)
else:raise AssertionError('Division accepted absent scenes')
with_list=check_rows(metadata,binding['division'],removals=Removals([binding['remove']]))
assert with_list['removed']==601 and with_list['outside']==0
result=dict(binding=binding,keys=len(keys),families=counts,types=types,without_list=without,with_list=with_list,
    full_v7_store_census='NOT RUN: a full scan reads the complete local database; heavy-IO approval is unavailable in this unattended run.',
    expected_store_outside=601,expected_source=str(L.parent/'work/design/20261117T2044Z_RESULT_r1_ops_remove_list.md'),
    scope='All removal-list keys and scenes independently checked against production division. This does not census the full store or prove full build_stream.')
(P/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
with (B/'DECISIONS.md').open('a') as f:
    f.write('\n- Full-store division census: the VQA database has no metadata index; a census reads the full database. Options are an approved full scan or a bounded list/division check. Default: check every supplied removal key against the production division and keep the full-store proof blocked, because heavy-IO approval cannot be obtained during this run.\n')
monitor.save(P);print(json.dumps(result))
