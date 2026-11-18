# Reviewer refute test (copy only): faithful gate threshold, exit codes, and r.py final refusal.
import json,subprocess,sys,shutil
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parents[2];P=H/'payload';out=H/'evidence/review/gate';out.mkdir(exist_ok=False)
(P/'t').exists() or None
t=out/'b/t';t.mkdir(parents=True)
subprocess.run(['tar','-xf',str(P/json.loads((H/'ids.json').read_text())['trainer']['file']),'-C',str(t)],check=True)
shutil.copy(P/'f.py',out/'b/f.py')
sys.path.insert(0,str(t))
import student_pilot.h1_faithful as hf
res={}
def rows(n_ok,n_bad,extra=0):
    r=[dict(question_type='camera_rotation',ok=True,target='x',events=[]) for _ in range(n_ok)]
    r+=[dict(question_type='camera_displacement',ok=False,target='x',events=[]) for _ in range(n_bad)]
    r+=[dict(question_type='object_count',target='x',events=[]) for _ in range(extra)]
    return r
fake=lambda row,printed:{'target':'x' if row['ok'] else 'y'}
with patch.object(hf,'canonical_row',lambda s:s),patch.object(hf,'materialize',fake):
    for name,(a,b,e) in dict(r95=(19,1,5),r94=(47,3,0),none=(0,0,10)).items():
        v=hf.identity_check(rows(a,b,e));res[name]=dict(rate=v['identity_rate'],passes=v['passes'])
assert res['r95']['passes'] and not res['r94']['passes'] and not res['none']['passes']
# f.py exit codes on real files: a non-camera JSONL (rate None) -> 1; unreadable -> 2.
j=out/'rows.jsonl';j.write_text(json.dumps(dict(question_type='object_count'))+'\n')
py='/scratch/jjyeung/envs/p1cpu/bin/python'
res['fpy_no_camera_rc']=subprocess.run([py,'-B',str(out/'b/f.py'),str(j),'--out',str(out/'g1.json')],capture_output=True).returncode
res['fpy_missing_rc']=subprocess.run([py,'-B',str(out/'b/f.py'),str(out/'absent.sqlite')],capture_output=True).returncode
res['fpy_no_camera_passes']=json.loads((out/'g1.json').read_text())['passes']
# r.py final must refuse a failing gate before any derivation.
rp=(P/'r.py').read_text();assert "gate['passes'] is True" in rp
res['rpy_final_asserts_gate']=True
res['s_sh_requires_final_manifest']="manifest_sha256" in (P/'s.sh').read_text()
(H/'evidence/review/rv_gate.json').write_text(json.dumps(res,indent=1));print(json.dumps(res,indent=1))

assert res['fpy_no_camera_rc']==1 and res['fpy_missing_rc']==2
assert res['fpy_no_camera_passes'] is False
assert res['s_sh_requires_final_manifest']
print('PASS faithful gate')
