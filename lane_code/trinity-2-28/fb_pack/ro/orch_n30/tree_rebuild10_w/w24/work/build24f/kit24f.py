"""Apply the launch resource and batch-shell persistence policy, then seal."""
from pathlib import Path
import base64
import hashlib
import json
import shutil
import sys

L=Path(__file__).resolve().parents[2]
D=L/'work/build24f'
T=L/'work/tree_r1'
sys.path[:0]=[str(L/'work/build24'),str(T)]
import joblib as J
from student_pilot.source_seal import inventory, archive, create, check_archive
from student_pilot.p3_provenance import digest, file_pin, source_files
from launch_r2.build import capsule_json


def cap(k,n,v):
    (k/n).write_bytes(capsule_json(v))


def reseal(k):
    fs={str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file() and p.name not in ('SHA256SUMS.txt','BUILD.json')}
    (k/'SHA256SUMS.txt').write_text(''.join(f'{h}  {n}\n' for n,h in sorted(fs.items())))
    b=J.load(k/'BUILD.json');b.update(kit_sha256=J.seal(k));cap(k,'BUILD.json',b)
    return J.seal(k)


def upgrade(k):
    k=Path(k)
    files=inventory(T);tree=digest(files)
    closure={str(p.relative_to(T)):J.sha(p) for p in source_files([T/'student_pilot/carrier_c1_run.py'])}
    target=D/('t_'+tree[:16]+'.tar')
    if not target.exists():archive(T,target,files,compress=True)
    check_archive(file_pin(target),files)
    control=J.load(k/'k/a.json');ns=J.load(k/'k/p.json')['namespace']
    shutil.copyfile(target,k/control['source']['path'])
    control['source'].update(sha256=J.sha(target),tree_sha256=tree)
    cap(k,'k/7.json',dict(schema='c1-sealed-source-v1',commit='sha256:'+tree,tree_sha256=tree,files=files,archive={key:control['source'][key] for key in ('path','sha256')},sources=closure,operation_sources=closure))
    code=create(T,target,closure,{},archive_path=ns+'/t.tar')
    raw=(json.dumps(code,sort_keys=True,indent=2)+'\n').encode()
    (k/'k/c0.json').write_text(json.dumps(dict(encoding='base64',payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())))
    spec=J.load(k/'k/p.json');spec['code_sha256']=hashlib.sha256(raw).hexdigest();cap(k,'k/p.json',spec)
    cfg=J.load(k/'k/c.json');cfg['code']=dict(path='k/7.json',sha256=J.sha(k/'k/7.json'));cap(k,'k/c.json',cfg)
    build=J.load(k/'BUILD.json');build['source_seal']=tree
    if J.load(k/'k/n.json')['r1_training']['proof_mode']=='train':
        resources=dict(partition='advanced',gpus=4,ranks=4,cpus=48,memory_gib=800,minimum_gpu_gib=75,wall_hours=24)
        control['resource_request']=resources;build['resource_request']=resources
        s=(k/'job.sh').read_text()
        s=s.replace('--cpus-per-task=8','--cpus-per-task=48').replace('--mem=192G','--mem=800G').replace('--time=12:00:00','--time=24:00:00')
        if '#SBATCH --signal=B:TERM@600' not in s:s=s.replace('#SBATCH --no-requeue','#SBATCH --signal=B:TERM@600\n#SBATCH --no-requeue')
        if 'export TK_JOB_START=' not in s:s=s.replace('export PYTHONDONTWRITEBYTECODE=1','export TK_JOB_START="$(date +%s)"\nexport PYTHONDONTWRITEBYTECODE=1',1)
        s=s.replace('export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8','export OMP_NUM_THREADS=48 MKL_NUM_THREADS=48 OPENBLAS_NUM_THREADS=48')
        if 'b/pc.sh' not in s:
            s=s.replace('cd "$N"','cd "$N"\nsource "$ROOT/b/pc.sh"')
            s=s.rstrip()+' &\nTK_WORK_PID=$!\nwait "$TK_WORK_PID"\n'
        (k/'job.sh').write_text(s)
        (k/'b/pc.py').write_bytes((D/'live.py').read_bytes())
        (k/'b/pc.sh').write_bytes((D/'live.sh').read_bytes())
        (k/'b/gc.py').write_bytes((T/'launch_s1/b/gcsput.py').read_bytes())
        cfg=J.load(k/'k/n.json');run=Path(cfg['output']).name
        names=dict(objects={label:f'q9/22c714e1/{run}_{label}.tar' for label in [*(f'm{s}' for s in cfg['recipe']['milestones']),'mstop','mstopB','mstopC','ckstop']})
        cap(k,'k/y.json',names)
        doc=json.loads((k/'k/j.json').read_text());s=base64.b64decode(doc['payload']).decode()
        s=s.replace('export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1','export OMP_NUM_THREADS=48 MKL_NUM_THREADS=48 OPENBLAS_NUM_THREADS=48')
        train='"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/t.py"'
        if 'export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8\n'+train not in s:
            s=s.replace(train,'export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8\n'+train)
        if '--setenv TK_JOB_START' not in s:s=s.replace('BW+=(--bind "$Q_ROOT" "$Q_NS")','BW+=(--bind "$Q_ROOT" "$Q_NS" --setenv TK_JOB_START "${TK_JOB_START:?}")')
        # The stage file stays on node storage and enters the small-file publication.
        s=s.replace('if [[ -n "${SLURM_JOB_ID:-}" && -d "$HM/o" ]]; then printf \'%s\\n\' "$line" >> "$HM/o/$SLURM_JOB_ID.steps" 2>/dev/null || true; fi', 'if [[ -n "${SLURM_JOB_ID:-}" ]]; then printf \'%s\\n\' "$line" >> "$Q_ROOT/$SLURM_JOB_ID.steps"; fi')
        raw=s.encode();doc.update(payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest());(k/'k/j.json').write_text(json.dumps(doc))
    cap(k,'k/a.json',control);cap(k,'BUILD.json',build)
    return reseal(k)


def main():
    records={}
    for name in ('q','n','n_go'):
        k=L/'out/kit_n_go' if name=='n_go' else L/'work/build24/kits'/name
        records[name]=dict(kit_seal=upgrade(k),tree_seal=J.load(k/'k/a.json')['source']['tree_sha256'],GO=J.load(k/'k/a.json')['GO'])
    J.write(D/'KIT.json',records)
    J.write(L/'out/TREE_SEAL.json',dict(tree_sha256=digest(inventory(T)),files=len(inventory(T))))
    J.write(D/'TREE_FILES.json',inventory(T))
    names=J.load(L/'work/build24/kits/n/k/y.json')['objects']
    J.write(L/'out/SESSION_NAMES_24F.json',dict(objects=names,parts=[f'{obj}.part{i:02d}-of-04' for obj in names.values() for i in range(4)],sessions_file='$TK_KIT_HOME/sess.json',contains_credentials=False))
    print(json.dumps(records,indent=2))


if __name__=='__main__':main()
