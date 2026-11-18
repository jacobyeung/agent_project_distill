import json,os,sys,sqlite3,collections,time
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/review_treen1/work');TREE=Path(sys.argv[1]);tag=sys.argv[2];lim=int(sys.argv[3])
os.environ.update(R2_FIXTURES=str(W/'n1c/pkg/fixtures'),R2_PROOFS=str(W/'n1c/tmp'))
sys.path[:0]=[str(TREE)]
from student_pilot.carrier_c1_run import Rows
from student_pilot.p3_provenance import file_pin
from tests.test_r2_build9_recovery import TinyProcessor
PIN=file_pin(W/'n1c/pkg/work/n1fix/inputs/extents.json')
DB='/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite'
r=Rows({'streams':{},'extent_receipt':PIN,'r1_training':{'schema':'r1-training-v1'}},TinyProcessor())
r.connections['vqa']=sqlite3.connect('file:'+DB+'?mode=ro',uri=True)
n=r.connections['vqa'].execute('SELECT count(*) FROM rows').fetchone()[0]
ids=[i for i, in r.connections['vqa'].execute('SELECT i FROM rows ORDER BY i LIMIT ?',(lim,))]
c=collections.Counter();t=time.time()
for i in ids:
    try:r.row('vqa',i);c['ADMIT']+=1
    except Exception as e:c[type(e).__name__+':'+str(e)[:50]]+=1
out=dict(tree=str(TREE),rows_in_db=n,checked=len(ids),seconds=round(time.time()-t,1),outcomes=dict(c.most_common()),b7=bool(r.b7_inputs),r1=getattr(r,'r1_training',None))
print(json.dumps(out,indent=1));(W/'n1c'/f'R1READER_{tag}.json').write_text(json.dumps(out,indent=1,default=str))
