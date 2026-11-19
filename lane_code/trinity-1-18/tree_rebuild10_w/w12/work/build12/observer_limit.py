from pathlib import Path
import json,sys,tempfile
L=Path(__file__).resolve().parents[2];B=L/'work/build12';O=B/'proofs/observer_limit'
O.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(L/'work/build10'))
index=0
def retained(*a,**k):
    global index
    index+=1;p=L/'work/tmp/observer_limit'/str(index);p.mkdir(parents=True,exist_ok=True);return str(p)
tempfile.mkdtemp=retained
src=Path('/scratch/jjyeung/orch_n30/review_tree11/work/l1/probe.py')
s=src.read_text().replace("sys.path.insert(0,'/scratch/jjyeung/orch_n30/review_tree11/work/eat/b')",'')
space={'__name__':'observer_limit'};exec(compile(s,str(src),'exec'),space)
result=space['out']
assert result['mutate_restore_within_item']['a1']=='PASS'
assert result['mutate_in_generate']['a1']=='FAIL'
assert result['mutate_then_raise']['a1']=='FAIL'
(O/'RESULT.json').write_text(json.dumps(dict(results=result,
    named_limit='EAT1_TRANSIENT_RESTORED_BUFFER_UNOBSERVED',
    scope='The observer checks boundary snapshots. A buffer changed and restored within generate escapes A1; this is not continuous integrity.'),indent=2))
