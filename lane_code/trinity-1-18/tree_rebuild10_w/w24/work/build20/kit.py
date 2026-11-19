from pathlib import Path
import base64,hashlib,json,os,re,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build20';T=L/'work/tree_r1';E=L.parent/'ext/pwrap';K=B/'kits/q';O=B/'proofs/operator'
O.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(T))
from student_pilot.p3_provenance import load,file_pin,sha256,source_files
from student_pilot.source_seal import create
from launch_r1.build import build,verify
from launch_r2.build import capsule_json,scan
def capraw(raw):return json.dumps(dict(encoding='base64',payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())).encode()
def cap(name,value):(K/name).write_bytes(capsule_json(value))
for name in ('config.json','kit_config.json'):
    c=load(B/'inputs'/name)
    c['r1_training']['mix']=file_pin(B/'inputs/mix.json')
    c['r1_training']['component_rows']=file_pin(B/'inputs/component_rows.json')
    (B/'inputs'/name).write_text(json.dumps(c,sort_keys=True,indent=2)+'\n')
if K.exists() and not (B/'KIT_Q_INITIAL.json').exists():
    K.rename(K.parent/'q_incomplete')
if not K.exists():build(B/'inputs/kit_config.json',L/'work/n1fix2/inputs',K)
else:
    assert (B/'KIT_Q_INITIAL.json').exists(),'The initial kit must be staged from empty.'
if not (B/'KIT_Q_INITIAL.json').exists():(B/'KIT_Q_INITIAL.json').write_text(json.dumps(dict(initial_empty=True,base_seal=verify(K))))
ns='/tmp/q_90a20c41';pool='/project/community/jjyeung/okh7';nroot=pool+'/x_90a20c41';proot='x_ee227714'
cfg=load(B/'inputs/config.json');uploads={};missing={};seen=set()
def local(path):
    p=Path(path)
    if str(p).startswith(('/home/','/data')):return None
    if p.is_file():return p
    text=str(p)
    for marker in ('/work/','/fixtures/'):
        if marker in text:
            candidate=L/(marker.strip('/')+'/'+text.split(marker,1)[1])
            if candidate.is_file():return candidate
    return None
def visit(value,depth=0):
    if isinstance(value,dict):
        if isinstance(value.get('path'),str) and re.fullmatch('[a-f0-9]{64}',str(value.get('sha256',''))):
            h=value['sha256'];path=local(value['path'])
            if h not in seen:
                seen.add(h)
                if path and path.suffix not in ('.db','.sqlite','.pt','.safetensors','.bin','.png','.npz') and path.stat().st_size<30_000_000:
                    if sha256(path)!=h:raise ValueError('Static pin mismatch '+str(path))
                    uploads[h]=dict(local_path=str(path),opaque_name='u/'+h,sha256=h,bytes=path.stat().st_size)
                    if path.suffix=='.json' and depth<8:
                        try:nested=load(path)
                        except ValueError:nested=None
                        visit(nested,depth+1)
                else:missing[h]=dict(path=value['path'],sha256=h)
        for v in value.values():visit(v,depth)
    elif isinstance(value,list):
        for v in value:visit(v,depth)
visit(cfg)
room=file_pin(L/'work/build18/inputs/room_audit.json');visit(room)
withheld=file_pin(L/'fixtures/work/shared/WITHHELD_ROOMS_80.json');visit(withheld)
source=load(K/'k/a.json')['source'];archive=K/source['path']
staging=load(K/'k/s.json');bound=load(K/'k/c.json')['r1_training']['mix']['path']
cap('k/s.json',dict(entries={bound:staging['entries'][bound]},unresolved=[]))
closure={str(p.relative_to(T)):sha256(p) for p in source_files([T/'student_pilot/carrier_c1_run.py'])}
code=create(T,archive,closure,{},archive_path=ns+'/t.tar')
raw=(json.dumps(code,sort_keys=True,indent=2)+'\n').encode();(K/'k/c0.json').write_bytes(capraw(raw))
pfiles={n:h for h,n in (line.split('  ',1) for line in (E/'SHA256SUMS.txt').read_text().splitlines())}
# Only P's sealed metadata/code inputs enter the local staging copy; its run is never copied.
pfiles={n:h for n,h in pfiles.items() if n.startswith(('b/','k/','in_small/')) or n in ('ANON_OK.json',)}
pfiles['SHA256SUMS.txt']=sha256(E/'SHA256SUMS.txt')
spec=dict(pool=pool,n_root=nroot,p_root=proot,milestone='h_6ed2c7aa/m400',namespace=ns,
    p_identity='774503e26f274a10c96ad06210d339c49ebc9a704ac254df81f389b0da4d98a1',
    p_files=pfiles,p_pins=file_pin(E/'k/0.json'),room_sha256=room['sha256'],code_sha256=hashlib.sha256(raw).hexdigest(),
    uploads=list(uploads.values()),frame_roots=load(E/'k/launch.json')['in_job_admission']['frame_roots'])
cap('k/p.json',spec);cap('k/n.json',cfg);cap('k/r.json',load(L/'work/build17/proofs/operator/REQUEST_TEMPLATE.json'))
(K/'b/z.py').write_bytes((B/'joblib.py').read_bytes())
(K/'b/resolve.py').write_text('''import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import resolve
p=argparse.ArgumentParser();p.add_argument('--pool',required=True);p.add_argument('--listing',required=True);p.add_argument('--output',required=True)
a=p.parse_args();resolve(Path(__file__).resolve().parents[1],a.pool,a.listing,a.output)
''')
(K/'b/x.py').write_text('''import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import bootstrap
raise SystemExit(bootstrap(*sys.argv[1:]))
''')
(K/'b/v.py').write_text('''import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import seal
print(seal(sys.argv[1]))
''')
(K/'b/g.py').write_text("import json,os,re\nv=None;a=False;c=0;e=False;ec=0;n=None;m=None;d0=False;dc=False;x=False;ok=False\ntry:\n import torch\n v=str(torch.__version__)\n a=bool(torch.cuda.is_available())\n c=int(torch.cuda.device_count())\n s=os.environ.get('CUDA_VISIBLE_DEVICES')\n e=s is not None;ec=len(s.split(',')) if s else 0\n d0=bool(os.path.exists('/dev/nvidia0'))\n dc=bool(os.path.exists('/dev/nvidiactl'))\n if a and c:\n  p=torch.cuda.get_device_properties(0)\n  s=p.name;n=s if isinstance(s,str) and re.fullmatch(r'[A-Za-z0-9 ._-]{1,64}',s) else '?'\n  m=int(p.total_memory)\n ok=a and c>=1 and m is not None and m>=75*(1<<30)\nexcept Exception:\n x=True\nprint(json.dumps(dict(v=v,a=a,c=c,e=e,ec=ec,n=n,m=m,d0=d0,dc=dc,x=x)),flush=True)\nif x or not ok:\n raise RuntimeError('E42')\n")
entry=(K/'b/a.py').read_text()
entry=entry.replace("r=run(load(sys.argv[3]),root/'q')", "request=load(sys.argv[3])\n from student_pilot.r1_persisted import scope\n with scope(request.pop('_paths',{})):\n  r=run(request,root/'q')")
(K/'b/a.py').write_text(entry)
(K/'b/d.py').write_text('''import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import load,room_report
sys.path.insert(0,sys.argv[1])
from student_pilot.r1_persisted import scope
r=load(sys.argv[2])
with scope(r['_paths']):room_report(load(sys.argv[3]),sys.argv[4])
''')
shell=(E/'b/c.sh').read_text()
shell=shell.replace('S=/tmp/jjyeung/a_6ed2c7aa/root','S="$Q_ROOT/s"')
shell=shell.replace('NX=/tmp/jjyeung/a_6ed2c7aa/x_${SLURM_JOB_ID:-local}','NX="$Q_ROOT/x"').replace('NR=/tmp/jjyeung/a_6ed2c7aa/runs','NR="$Q_ROOT/rp"')
shell=shell[:shell.index('tk_persist_small()')]
shell+='''
tk_stage full
tk_env
tk_pythonpath c
tk_bwrap
BW+=(--bind "$Q_ROOT" "$Q_NS")
if [[ "${Q_CAPTURE:-0}" == 1 ]]; then
    /usr/bin/python3 "$Q_KIT/b/w.py" "$Q_ROOT/args.json" "${BW[@]}"
    exit 0
fi
"${BW[@]}" "$PILOT_VENV/bin/python" -s -B "$Q_KIT/b/g.py"
set +e
"${BW[@]}" "$PILOT_VENV/bin/python" -s -B "$Q_KIT/b/a.py" q "$Q_NS/p" "$Q_NS/r.json" > "$Q_ROOT/q.log" 2>&1
rc=$?
"${BW[@]}" "$PILOT_VENV/bin/python" -s -B "$Q_KIT/b/d.py" "$Q_NS/p/s" "$Q_NS/r.json" "$Q_NS/n.json" "$Q_NS/rooms.json" > "$Q_ROOT/rooms.log" 2>&1
rr=$?
/usr/bin/python3 "$Q_KIT/b/o.py" "$Q_ROOT" "$rc" "$rr"
exit "$rc"
'''
(K/'k/j.json').write_bytes(capraw(shell.encode()))
(K/'b/w.py').write_text('import json,sys\nfrom pathlib import Path\nPath(sys.argv[1]).write_text(json.dumps(sys.argv[2:]))\n')
(K/'b/o.py').write_text('''import json,sys,tarfile,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import load,write
k=Path(__file__).resolve().parents[1];s=load(k/'k/p.json');r=Path(sys.argv[1]);out=Path(s['n_root'])/'o'/os.environ['SLURM_JOB_ID'];out.mkdir(parents=True,exist_ok=True)
files=[r/n for n in ('q.log','rooms.log','rooms.json','p/q/RESULT.json','p/q/f.json') if (r/n).is_file()]
with tarfile.open(out/'o.tar','w:gz') as t:
 for p in files:t.add(p,arcname=str(p.relative_to(r)),recursive=False)
write(out/'RESULT.json',dict(proof_rc=int(sys.argv[2]),rooms_rc=int(sys.argv[3]),GO=False,submitted_by_build=False))
''')
(K/'job.sh').write_text('''#!/bin/bash
#SBATCH --partition=general
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=192G
#SBATCH --time=12:00:00
#SBATCH --gres=gpu:1
#SBATCH --no-requeue
set -euo pipefail
umask 077
ROOT="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
N="${SLURM_TMPDIR:-/tmp}/q_90a20c41_${SLURM_JOB_ID:?}"
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
python3 -I -s -B "$ROOT/b/v.py" "$ROOT"
exec python3 -I -s -B "$ROOT/b/x.py" "$ROOT" "${1:?}" "$N"
''')
for name in ('q.sh','q1.sh'):
    (K/'b'/name).write_text('#!/bin/bash\nset -eu\nROOT="$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")"\nexec /bin/bash "$ROOT/job.sh" "$@"\n')
sys.path.insert(0,str(L/'work/build24c'))
from runtime import harden_kit
harden_kit(K)
manifest={str(p.relative_to(K)):sha256(p) for p in K.rglob('*') if p.is_file() and p.name not in ('SHA256SUMS.txt','BUILD.json')}
(K/'SHA256SUMS.txt').write_text(''.join(f'{h}  {n}\n' for n,h in sorted(manifest.items())))
result=dict(GO=False,kit_sha256=verify(K),source_seal=code['tree_sha256'],resource_request=dict(partition='general',gpus=1,minimum_gpu_gib=75,cpus=8,memory_gib=192,wall_hours=12),sizing='GUESS; real model fit has not been measured')
cap('BUILD.json',result)
all_uploads=list(uploads.values())+[dict(local_path=str(p),opaque_name='q/'+str(p.relative_to(K)),bytes=p.stat().st_size,sha256=sha256(p)) for p in K.rglob('*') if p.is_file()]
(B/'UPLOADS.json').write_text(json.dumps(dict(files=all_uploads,total_bytes=sum(x['bytes'] for x in all_uploads)),indent=2))
rows=load(L/'work/build17/proofs/operator/STAGING.json')
for h in (cfg['r1_training']['component_rows']['sha256'],cfg['r1_training']['v7_k1_removal']['sha256']):
    assert h in uploads
    rows.append(dict(source=uploads[h]['local_path'],staged_name=uploads[h]['opaque_name'],bytes=uploads[h]['bytes'],sha256=h,category='upload_from_node',status='available'))
(O/'STAGING.json').write_text(json.dumps(rows,indent=2))
(O/'RESULT.json').write_text(json.dumps(dict(result,files=manifest,uploads=len(all_uploads),upload_bytes=sum(x['bytes'] for x in all_uploads),unavailable_static=missing),indent=2))
print(json.dumps(result,indent=2));print('upload bytes',sum(x['bytes'] for x in all_uploads))
