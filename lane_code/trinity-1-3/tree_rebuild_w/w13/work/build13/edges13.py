from pathlib import Path
import sys,os,json
L=Path(__file__).resolve().parents[2];B=L/'work/build13';T=L/'work/tree_r1';O=B/'proofs/edges'
O.mkdir(parents=True,exist_ok=True);sys.path[:0]=[str(T),str(L/'work/n1fix2')]
from monitor9 import Monitor
m=Monitor(T)
import launch_r1.entry
from student_pilot.r1_routing import check_local_size,Filters
from student_pilot.s1_exclusions import verify
from student_pilot.p3_provenance import load,file_pin
from student_pilot.row_removals import Removals
check_local_size(1)
try:check_local_size(200_000_001)
except ValueError as e:assert str(e)=='R1_LOCAL_COMPOSITION_STORAGE_LIMIT'
else:raise AssertionError('Storage limit missing')
prepared=load(B/'proofs/tests/population13/test_native_mixture_and_bound_producer/produced/receipt.json')
verify(prepared,{})
cfg=load(B/'inputs/config.json');f=Filters(cfg,cfg['scene_division'])
p=O/'removed.jsonl';p.write_text(json.dumps(dict(row_key='fixture_removed'))+'\n')
f.removals=Removals([file_pin(p)])
assert f.reason(dict(qid='fixture_removed'),'vqa')=='remove_files'
(O/'RESULT.json').write_text(json.dumps(dict(status='PASS',storage_boundary=200_000_000,
    source='User build rules; pure size predicate only, no oversized allocation or write',scene_selection='native verify consumes the reader subset and original scene receipt')))
m.save(O)
