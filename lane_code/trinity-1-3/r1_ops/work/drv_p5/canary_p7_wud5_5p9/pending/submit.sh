#!/bin/bash
# Usage: bash -s -- <PROOF_JOB> <sha256 of ORCH GO file>
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC
PROOF_JOB=${1:-}; GO_SHA=${2:-}
[[ $# == 2 && "$PROOF_JOB" =~ ^[1-9][0-9]*$ && "$PROOF_JOB" != 170956 && "$GO_SHA" =~ ^[0-9a-f]{64}$ ]] || { echo 'REFUSED: usage <PROOF_JOB> <GO_SHA (64 hex)>'; exit 2; }
export PROOF_JOB ADMISSION_JOB=170956
O=/scratch/jjyeung/orch_n30/r1_ops/work/drv_p5/canary_p7_wud5_5p9/pending; BUN=$O/i_69d2930d; KH=$O/x_69d2930d; JN=a15_cot_ap673bc60f
for dir in "$O" "$BUN" "$KH"; do
 [[ -d "$dir" && ! -L "$dir" && $(stat -c %a "$dir") == 700 ]] || { echo "REFUSED: private directory required: $dir"; exit 3; }
done
cd "$BUN"
printf '%s  %s\n' 9dd2fbb77503ecee875d538ebaed933cc95ff286f76e5955fc2591f63e3f0192 p.tar fbcbb76c43a3307a846eb2c73171dd3ae4f99da7ad273328ce3a1a2e53e7b847 s.sh 23eb51a0f6863e1086365acb4b542b3f62d4e8c3ba15dbf0bae6890cfad37bd8 sums.txt b6a1e4c8f4c0a8fce029233575d082fae69ba018a311288dc8391493efa4648f jb.sh | sha256sum -c --quiet
sha256sum -c --quiet sums.txt
[[ ! -L training.lock ]] || { echo 'REFUSED: linked training lock'; exit 3; }
exec 9> training.lock
flock -n 9 || { echo 'REFUSED: concurrent training submission'; exit 4; }
for file in training.started training.job.id training.sbatch.out training.json "$KH/o/$PROOF_JOB.canary.json"; do
 [[ ! -e "$file" && ! -L "$file" ]] || { echo "REFUSED: training submission evidence already exists: $file"; exit 5; }
done
/scratch/jjyeung/envs/p1cpu/bin/python -I -B - "$KH" "$BUN" "$PROOF_JOB" "$GO_SHA" <<'PY'
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
k,b,job,ref=Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3],sys.argv[4]
def refuse(message): raise SystemExit('REFUSED: '+message)
p=b/'job.id'
if p.is_symlink() or not p.is_file() or p.read_text().strip()!=job:
    refuse('PROOF_JOB must equal the fresh bundle job.id')
def query(args):
    return subprocess.run(args,env=dict(os.environ,TZ='UTC'),capture_output=True,text=True,check=True,timeout=30).stdout
rows=[line.strip().split('|') for line in query(['squeue','--noheader','--format=%i|%T|%j']).splitlines() if line.strip()]
if any(len(row)!=3 for row in rows): refuse('malformed squeue response')
proof=[row for row in rows if row[0]==job]
if len(proof)!=1 or proof[0][1] not in ('PENDING','RUNNING') or proof[0][2]!='a15_cot_ap673bc60f':
    refuse('proof job must be PENDING or RUNNING under the pinned name')
if any(row[2]=='a15_cot_ap673bc60f' and row[0]!=job for row in rows):
    refuse('another same-name job is in the queue')
history=query(['sacct','-X','-n','-P','-S','2026-11-17','--name','a15_cot_ap673bc60f','-o','JobIDRaw,JobName%128,State'])
for line in history.splitlines():
    if not line.strip(): continue
    fields=[field.strip() for field in line.split('|')]
    if len(fields)==4 and fields[-1]=='': fields.pop()
    if len(fields)!=3 or not re.fullmatch('[1-9][0-9]*',fields[0]) or fields[1]!='a15_cot_ap673bc60f':
        refuse('malformed or unexpected sacct response')
    if fields[0] not in (job,'170956'): refuse('a prior same-name allocation already exists')
ids=json.loads((b/'ids.json').read_text())
if ids['identity']!='fac0705214fdecb53561c633d7d94642cd469b50b662c5de81f09d11891d115f' or ids['job_name']!='a15_cot_ap673bc60f': refuse('bundle identity differs')
go=dict(production_go_granted=True,config_sha256=ids['identity'],admission_contract_sha256=ids['contract'],
        wrapper_sha256=hashlib.sha256((b/'jb.sh').read_bytes()).hexdigest(),
        manifest_sha256=hashlib.sha256((k/'SHA256SUMS.txt').read_bytes()).hexdigest(),authority='sha256:'+ref,canary=True)
data=json.dumps(go,sort_keys=True); p=b/'go.json'
if p.exists() or p.is_symlink():
    if p.is_symlink() or p.read_text()!=data: refuse('existing go.json differs; inspect, never overwrite')
    print('go.json exists and is byte-equal; reusing')
else:
    with p.open('x') as f: f.write(data)
    p.chmod(0o600); print('go.json written',go['config_sha256'][:8])
print('PASS active proof job.id binding; queue and accounting clear')
PY
# Preserve any failed or uncertain attempt. Never automatically retry sbatch.
(set -o noclobber; printf 'proof_job=%s admission_job=170956 authority=sha256:%s\n' "$PROOF_JOB" "$GO_SHA" > training.started)
set -o noclobber
if bash s.sh > training.sbatch.out 2>&1; then
 cat training.sbatch.out
else
 rc=$?; cat training.sbatch.out
 echo "UNCERTAIN: gate or sbatch failed rc=$rc; inspect retained evidence; do not resubmit" >&2
 exit "$rc"
fi
/scratch/jjyeung/envs/p1cpu/bin/python -I -B - "$KH" "$BUN" "$PROOF_JOB" "$GO_SHA" <<'PY'
import hashlib,json,re,sys
from pathlib import Path
k,b,proof,ref=Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3],sys.argv[4]
jobs=re.findall(r'^Submitted batch job ([1-9][0-9]*)\s*$',(b/'training.sbatch.out').read_text(),re.M)
assert len(jobs)==1 and jobs[0] not in (proof,'170956'), 'UNCERTAIN sbatch result; do not resubmit'
p=k/'o'/(proof+'.canary.json')
assert p.is_file() and not p.is_symlink(), 'UNCERTAIN: gate marker missing; inspect allocation'
marker=json.loads(p.read_text())
assert marker['canary'] is True and marker['proof_job']==proof and marker['admission_job']=='170956' and marker['submission']=='GATE_ACCEPTED'
record=dict(training_job=jobs[0],proof_job=proof,admission_job='170956',authority='sha256:'+ref,
            canary=True,gate_marker=str(p),gate_marker_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            go_sha256=hashlib.sha256((b/'go.json').read_bytes()).hexdigest())
with (b/'training.job.id').open('x') as f: f.write(jobs[0]+'\n')
with (b/'training.json').open('x') as f: json.dump(record,f,sort_keys=True); f.write('\n')
print('SUBMITTED canary training_job='+jobs[0]+' proof_job='+proof+' admission_job=170956')
PY
