import json, hashlib, tarfile
from pathlib import Path
R=Path('extract').resolve()
TAR='/scratch/jjyeung/orch_n30/sb_ktfix2/out/sb_ktfix2.tar'
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
m=json.load(open(R/'out/FIX2_MEMBERS.json'))
names=[t.name for t in tarfile.open(TAR) if t.isfile()]
nontar=[t.name for t in tarfile.open(TAR) if not t.isfile()]
mf=m['files']
bad=[k for k,v in mf.items() if sha(R/k)!=v]
extra=sorted(set(names)-set(mf)); missing=sorted(set(mf)-set(names))
# code pins replica
DS=('cpu.sh','gpu_environment.sh','run_A.sh','run_B.sh','run_C.sh','run_H.sh')
paths=[p for p in (R/'code').rglob('*') if p.is_file() and p.suffix in ('.py','.json','.md')]
paths+=[p for p in (R/'configs').glob('*.json') if p.name!='CODE_REVIEW.json']
paths+=[R/'scripts'/n for n in DS]+[R/'scripts'/n for n in ('finalize_v3.py','bind_camera.py')]
paths+=[R/'inputs/CAMERA_FRAME_JOINS.json',R/'inputs/TASK_RULINGS.txt']
paths+=[R/'inputs'/n for n in ('V2_SOURCES.json','KIT_SPEC_tower_frames_v2.md','pose_k1.py')]
paths+=list((R/'inputs/K1_ROWSETS').glob('*'))
paths+=[p for p in (R/'inputs/exclusions').rglob('*') if p.is_file()]
pins={str(p.relative_to(R)):sha(p) for p in sorted(paths)}
dg=hashlib.sha256(json.dumps(pins,sort_keys=True,allow_nan=False).encode()).hexdigest()
c=json.load(open(R/'out/CODE_SHA256.json'))
diffpins=[k for k in set(pins)|set(c['files']) if pins.get(k)!=c['files'].get(k)]
# compare to live sb_ktfix2 workspace code
L=Path('/scratch/jjyeung/orch_n30/sb_ktfix2')
live=[k for k in pins if not (L/k).is_file() or sha(L/k)!=pins[k]]
res=dict(tar_members=len(names),non_file_members=nontar,manifest_files=len(mf),hash_mismatch=bad,in_tar_not_manifest=extra,in_manifest_not_tar=missing,
 code_files=len(pins),code_sha256=dg,matches_claim=dg=='39b253c268e69d3ad71621336928e6446871e5483ed4283453d5e8e9f1ea401e',
 code_json_sha=c['code_sha256'],pin_diffs_vs_CODE_SHA256_json=diffpins,live_workspace_differs=live,
 configs=sorted(str(p.relative_to(R)) for p in (R/'configs').glob('*')),
 has_code_review=(R/'configs/CODE_REVIEW.json').exists())
for n in ('DRYRUN.json','GPU_NEED.json','TESTS.json','VALIDATION.json','EXCLUSIONS.json'):
    try: res[n+'_code_sha']=json.load(open(R/'out'/n)).get('code_sha256')
    except Exception as e: res[n+'_code_sha']=repr(e)
print(json.dumps(res,indent=1))
json.dump(res,open('verify_members.json','w'),indent=1)
