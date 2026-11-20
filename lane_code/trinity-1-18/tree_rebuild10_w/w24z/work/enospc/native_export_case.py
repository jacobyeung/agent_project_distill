from pathlib import Path
import os,sys,json,types,subprocess,shutil
W=Path(__file__).resolve().parent;X=W/'mnt6';N=W/'node6';N.mkdir();T=N/'r';T.mkdir()
sys.path.insert(0,str(W/'native'))
guard=dict(reserve_bytes=0,retained_archive_copies=1,planned_full_states=14,extra_full_states=2,planned_weight_exports=7)
m=types.ModuleType('student_pilot.checkpoint_space');m.plan=lambda *a,**k:guard;sys.modules[m.__name__]=m
from launch_r2.persistence import upload
with (W/'native_export_fill.log').open('wb') as f:
 subprocess.run(['dd','if=/dev/zero','of='+str(X/'fill'),'bs=1M','count=64'],stdout=f,stderr=f)
 subprocess.run(['df','-B1',str(X)],stdout=f,stderr=f)
assert shutil.disk_usage(X).free==0
p=T/'m300';p.mkdir();(p/'artifact.json').write_text('{"kind":"export","step":300}\n');(p/'q.bin').write_bytes(b'q'*4096)
r=upload(dict(r1_training={},output=str(T),recipe={},checkpoint_disk_guard=guard),p,'export')
assert r['kind']=='export' and r['durable'] is False and r['parts']==[] and Path(r['archive']['path']).is_file()
(W/'native_export_result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
