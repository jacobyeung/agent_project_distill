#!/bin/bash
# PASS proof only. Usage: bash -s -- <PASSING_PROOF_JOB> <sha256 of ORCH GO file>
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1
PROOF_JOB=${1:-}; GO_SHA=${2:-}
[[ $# == 2 && "$PROOF_JOB" =~ ^[1-9][0-9]*$ && "$GO_SHA" =~ ^[0-9a-f]{64}$ ]] || { echo 'usage: <PASSING_PROOF_JOB> <GO_SHA (64 hex)>'; exit 2; }
O=/scratch/jjyeung/orch_n30/r1_ops/work/drv_c1/training_c1_0_7xib21/success
BUN=$O/i_7f1589c1; KH=$O/x_7f1589c1; JN=a15_cot_ap05b8ac69
for path in "$O" "$BUN" "$KH"; do
 [[ -d "$path" && ! -L "$path" && $(stat -c %a "$path") == 700 ]] || { echo "REFUSED: private directory required: $path"; exit 4; }
done
cd "$BUN"
exec 9> "$BUN/training.lock"
flock -n 9 || { echo 'REFUSED: concurrent training submission'; exit 4; }
for name in training.started training.job.id training.json training.sbatch.out; do
 [[ ! -e "$BUN/$name" && ! -L "$BUN/$name" ]] || { echo "REFUSED: prior training attempt: $name; inspect, never resubmit"; exit 4; }
done
printf '%s  %s\n' 'c60b901594843989b909cb785a5fdc9ad544ea0fdec8d78c63bf173e4f6e136c' p.tar '5f15c65f0cc1355330314300fe1f269accc642b953eccf7f42bde3851cd500f6' s.sh '078993d52347598376457431c2081a1dfb5266f7fab0aa7644bb886626127207' sums.txt '5e03795db020451f3705d322505273a38f10130c6a007f0c86752de17e6e1605' jb.sh | sha256sum -c --quiet
sha256sum -c --quiet sums.txt
python3 -I -B - "$BUN" "$KH" "$PROOF_JOB" "$GO_SHA" <<'PY'
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
b,k=map(Path,sys.argv[1:3]);job,ref=sys.argv[3:]
def require(ok, why):
 if not ok:raise SystemExit('REFUSED: '+why)
def load(p):
 require(not p.is_symlink() and p.is_file(),'missing or linked record '+str(p))
 return json.loads(p.read_text())
def command(args):
 try:return subprocess.run(args,check=True,capture_output=True,text=True).stdout
 except subprocess.CalledProcessError:raise SystemExit('REFUSED: scheduler query failed: '+args[0])
def rows(raw, fields):
 result=[]
 for line in raw.splitlines():
  if not line.strip():continue
  parts=[v.strip() for v in line.split('|')]
  if len(parts)==fields+1 and parts[-1]=='':parts.pop()
  require(len(parts)==fields,'malformed scheduler row')
  result.append(parts)
 return result
require(not (b/'job.id').is_symlink() and (b/'job.id').read_text().strip()==job,'proof differs from C job.id')
require((b/'submission.started').is_file() and not (b/'submission.started').is_symlink(),'missing proof submission marker')
answer=(b/'sbatch.out').read_text().strip()
require(re.fullmatch(r'[1-9][0-9]*(?:;[A-Za-z0-9_-]+)?',answer) and answer.split(';')[0]==job,'proof sbatch receipt differs')
proof=load(k/'o'/(job+'.proof.json'))
require(proof.get('status')=='PASS' and type(proof.get('rc')) is int and proof['rc']==0 and proof.get('job')==job,'completed PASS proof required')
require(proof.get('config_identity')=='6594f46cdc16168514aca26a6ce38285907adfc6ece0b75d8e10428ea0b2fe74' and proof.get('checks',{}).get('resume_pointer',{}).get('status')=='PASS','C proof or resume-pointer check differs')
require(not list((k/'o').glob('*.canary.json')),'canary marker exists')
queue=rows(command(['squeue','-u',os.environ['USER'],'-h','-o','%i|%j|%P|%T|%R']),5)
for jid,name,part,state,reason in queue:
 if name=='a15_cot_ap05b8ac69':
  require(jid==job,'another C job is queued: '+jid+' '+state)
  require(False,'PASS proof still appears in queue: '+jid+' '+state)
 if name=='a15_cot_ap673bc60f' or jid=='171377':
  print('A queue: '+jid+' '+state+' '+part+' '+reason,flush=True)
  require(state in ('PENDING','PD'),'A still holds or may hold its advanced allocation')
history=rows(command(['sacct','-X','-n','-P','-S','2026-11-17','--name','a15_cot_ap05b8ac69','-o','JobIDRaw,JobName%64,State,ExitCode']),4)
require(bool(history),'C proof accounting is absent')
for jid,name,state,rc in history:
 require(name=='a15_cot_ap05b8ac69' and jid==job,'C training history or unexpected accounting row: '+jid+' '+name)
 require(state=='COMPLETED' and rc=='0:0','proof accounting is not COMPLETED 0:0')
require(len(history)==1,'ambiguous proof accounting')
donor=rows(command(['sacct','-X','-n','-P','-j','171377','-o','JobIDRaw,JobName%64,State,ExitCode']),4)
require(len(donor)==1 and donor[0][0]=='171377' and donor[0][1]=='a15_cot_ap673bc60f','A accounting is missing or ambiguous')
state=donor[0][2].split()[0].rstrip('+')
print('A training 171377 state='+donor[0][2]+' exit='+donor[0][3],flush=True)
require(state in ('COMPLETED','FAILED','CANCELLED','TIMEOUT','OUT_OF_MEMORY','NODE_FAIL','PREEMPTED','BOOT_FAIL','DEADLINE'),'A training 171377 may still hold advanced node')
# This is a small pointer preflight only. The sealed b/c0.py authenticates the
# donor archive, binding, manifest, optimizer and shards inside C's allocation.
source=b.parent/'r/673bc60f'
require(source.is_dir() and not source.is_symlink(),'A slot root is missing or linked')
found=[]
for slot in ('A','B'):
 p=source/(slot+'.json')
 if not p.exists() and not p.is_symlink():continue
 r=load(p)
 if r.get('verified') is True and type(r.get('step')) is int and r['step']==200:
  found.append(slot)
require(bool(found),'A needs a verified step-200 A/B slot record')
print('PASS A verified step-200 slot record: '+','.join(found)+'; runtime verifies full contents',flush=True)
ids=load(b/'ids.json')
require(ids['identity']=='6594f46cdc16168514aca26a6ce38285907adfc6ece0b75d8e10428ea0b2fe74' and ids['run_key']=='05b8ac69','C identity differs')
go=dict(production_go_granted=True,config_sha256=ids['identity'],admission_contract_sha256=ids['contract'],
 wrapper_sha256=hashlib.sha256((b/'jb.sh').read_bytes()).hexdigest(),
 manifest_sha256=hashlib.sha256((k/'SHA256SUMS.txt').read_bytes()).hexdigest(),authority='sha256:'+ref)
data=json.dumps(go,sort_keys=True);p=b/'go.json'
if p.exists() or p.is_symlink():
 require(not p.is_symlink() and p.read_bytes()==data.encode(),'existing go.json differs; never overwrite')
 print('go.json exists and is byte-equal; reusing')
else:
 with p.open('x') as f:f.write(data)
 p.chmod(0o600);print('go.json written '+ids['identity'][:8])
PY
(set -o noclobber; date -u +%FT%TZ > "$BUN/training.started")
if ! PROOF_JOB="$PROOF_JOB" bash s.sh > "$BUN/training.sbatch.out" 2>&1; then
 echo 'REFUSED or UNCERTAIN: sealed gate failed; inspect training.sbatch.out; no retry'; exit 4
fi
cat "$BUN/training.sbatch.out"
python3 -I -B - "$BUN" "$PROOF_JOB" "$GO_SHA" <<'PY'
import json,re,sys
from pathlib import Path
b=Path(sys.argv[1]);proof,authority=sys.argv[2:]
lines=(b/'training.sbatch.out').read_text().splitlines()
jobs=[m[1] for line in lines if (m:=re.fullmatch(r'Submitted batch job ([1-9][0-9]*)',line))]
if len(jobs)!=1 or jobs[0]==proof:raise SystemExit('UNCERTAIN: no unique training ID; inspect; never resubmit')
job=jobs[0]
with (b/'training.job.id').open('x') as f:f.write(job+'\n')
with (b/'training.json').open('x') as f:json.dump(dict(run='05b8ac69',mode='PASS',training_job=job,proof_job=proof,authority='sha256:'+authority),f,sort_keys=True);f.write('\n')
print('SUBMITTED training_job='+job+' proof_job='+proof+' advanced gpu=4 time=24:00:00')
PY
