"""The real materializer refuses contradictory certificates for the same row."""
import copy,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build10';T=L/'work/tree_r1';O=L/'work/merge11/proofs/extent_conflict'
O.mkdir(exist_ok=True);sys.path[:0]=[str(T),str(B)]
from monitor9 import Monitor
monitor=Monitor(T)
from student_pilot.p3_provenance import load,pinned,file_pin
from student_pilot.r2_materialize import materialize
manifest=load(L/'work/merge11/proofs/extent_admission/recovery/MANIFEST.json')
receipt=load(pinned(manifest['extent_receipt']))
qid=next(iter(receipt['rows']));receipt['rows'][qid]['box_statuses'][0]='unknown'
path=O/'contradictory.json';path.write_text(json.dumps(receipt))
second=copy.deepcopy(manifest);second['extent_receipt']=file_pin(path)
paths=[]
for name,value in [('a',manifest),('b',second)]:
    path=O/(name+'.json');path.write_text(json.dumps(value));paths.append(path)
try:materialize(paths,O/'store',metadata_only=True)
except ValueError as error:assert str(error)=='EXTENT_RECEIPTS_CONFLICT',str(error)
else:raise AssertionError('Conflicting certificates merged')
(O/'RESULT.json').write_text(json.dumps(dict(status='PASS',conflicting_qid=qid,
    real_functions=['r2_materialize.materialize','r2_intake.intake'],
    scope='Contradictory pinned row-audit records refuse before any frame work; no RGB/head stand-ins.'),indent=2)+'\n')
monitor.save(O);print('PASS')
