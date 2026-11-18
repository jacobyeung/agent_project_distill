#!/bin/bash
# Usage: bash -s -- <GO_SHA>; Cprime admission runs in the training job.
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME PROOF_JOB
export TZ=UTC PYTHONDONTWRITEBYTECODE=1
GO_SHA=${1:-}
[[ $# == 1 && "$GO_SHA" == 1f3dff81041a58c45966e83535ec50182a616de94d036fcfcfa5142141862b7e ]] || { echo 'REFUSED: expected pinned ORDER SHA'; exit 4; }
export ADMISSION_JOB=172180 ADMISSION_KIT=/project/community/jjyeung/okh7/x_7f1589c1.f172180
O=/project/community/jjyeung/okh7
BUN=/project/community/jjyeung/okh7/i_ee227714
KH=/project/community/jjyeung/okh7/x_ee227714
for path in "$O" "$BUN" "$KH"; do
 [[ -d "$path" && ! -L "$path" && $(stat -c %a "$path") == 700 ]] || { echo "REFUSED: private directory required: $path"; exit 4; }
done
cd "$BUN"
exec 9> "$BUN/training.lock"
flock -n 9 || { echo 'REFUSED: concurrent training submission'; exit 4; }
for name in training.started training.job.id training.json training.sbatch.out; do
 [[ ! -e "$BUN/$name" && ! -L "$BUN/$name" ]] || { echo "REFUSED: prior attempt: $name; inspect, never resubmit"; exit 4; }
done
printf '%s  %s\n' '3233765535fc95eb34b876b2e96895b5f684bd8b4e6c5c93f9e23123d320317b' p.tar '203fc15d232a9de9e5ffef186c8a35f8e72e38cedd6e38363fe7d0c2ab54bc09' s.sh '03f1c2178f9a2c5748081eedbcedb9d06e1d339acb9e3bcead74f48cdcd3be3b' sums.txt '24f7b8b187ffa92de386846f7d31798a1c15284127a3a37bb1be7f5b8938b23d' jb.sh | sha256sum -c --quiet
sha256sum -c --quiet sums.txt
python3 -I -B - "$BUN" "$KH" "$GO_SHA" <<'PY'
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
b,k=map(Path,sys.argv[1:3]);ref=sys.argv[3]
def require(ok,why):
 if not ok:raise SystemExit('REFUSED: '+why)
def load(p):
 require(p.is_file() and not p.is_symlink(),'missing or linked '+str(p));return json.loads(p.read_text())
def rows(args,fields):
 raw=subprocess.run(args,check=True,capture_output=True,text=True,timeout=30).stdout
 out=[]
 for line in raw.splitlines():
  if not line.strip():continue
  parts=[v.strip() for v in line.split('|')]
  if len(parts)==fields+1 and parts[-1]=='':parts.pop()
  require(len(parts)==fields,'malformed scheduler row');out.append(parts)
 return out
for p in k.iterdir():
 require(not p.is_symlink() and p.name in {'SHA256SUMS.txt','ANON_OK.json','b','k','job.sh','job8.sh','o','arm','runs','sess.json'},'unexpected kit entry '+p.name)
require(not (k/'o/canary_delta.json').exists(),'prior delta gate marker')
queue=rows(['squeue','-u',os.environ['USER'],'-h','-o','%i|%j|%P|%T|%R'],5)
for jid,name,part,state,reason in queue:
 require(name!='a15_cot_ap6ed2c7aa','same-name job already queued')
 if jid=='171377' or (name=='a15_cot_ap673bc60f' and 'advanced' in part.split(',')):
  require(state in ('PENDING','PD'),'A may still hold advanced allocation')
history=rows(['sacct','-X','-n','-P','-S','2026-11-17','--name','a15_cot_ap6ed2c7aa','-o','JobIDRaw,JobName%64,State,ExitCode'],4)
require(not history,'same-name accounting exists; inspect before submission')
donor=rows(['sacct','-X','-n','-P','-j','171377','-o','JobIDRaw,JobName%64,State,ExitCode'],4)
require(len(donor)==1 and donor[0][:2]==['171377','a15_cot_ap673bc60f'],'A accounting missing or ambiguous')
require(donor[0][2].split()[0].rstrip('+') in ('COMPLETED','FAILED','CANCELLED','TIMEOUT','OUT_OF_MEMORY','NODE_FAIL','PREEMPTED','BOOT_FAIL','DEADLINE','PENDING','PD'),'A may still hold advanced allocation')
cfg=load(b/'config.json');ids=load(b/'ids.json')
require(ids['identity']=='774503e26f274a10c96ad06210d339c49ebc9a704ac254df81f389b0da4d98a1' and ids['run_key']=='6ed2c7aa','Cprime identity')
require(cfg['continuation']['rows']=='rebind' and cfg['continuation']['root']=='/project/community/jjyeung/okh7/r/673bc60f','resume pointer')
source=Path(cfg['continuation']['root']);require(source.is_dir() and not source.is_symlink(),'A slot root')
found=[]
for slot in ('A','B'):
 p=source/(slot+'.json')
 if p.exists() or p.is_symlink():
  v=load(p)
  if v.get('verified') is True and type(v.get('step')) is int and v['step']==200:found.append(slot)
require(found,'A verified step-200 slot required')
go=dict(production_go_granted=True,config_sha256=ids['identity'],admission_contract_sha256=ids['contract'],
 wrapper_sha256=hashlib.sha256((b/'jb.sh').read_bytes()).hexdigest(),
 manifest_sha256=hashlib.sha256((k/'SHA256SUMS.txt').read_bytes()).hexdigest(),authority='sha256:'+ref,canary_delta=True)
raw=json.dumps(go,sort_keys=True).encode();p=b/'go.json'
if p.exists() or p.is_symlink():require(not p.is_symlink() and p.read_bytes()==raw,'existing GO differs')
else:
 with p.open('xb') as f:f.write(raw)
 p.chmod(0o600)
print('PASS pinned GO and donor pointer; sealed gate authenticates C4 and exact config delta')
PY
(set -o noclobber; date -u +%FT%TZ > "$BUN/training.started")
if ! env -u PROOF_JOB bash s.sh > "$BUN/training.sbatch.out" 2>&1; then
 echo 'REFUSED or UNCERTAIN: inspect training.sbatch.out; no retry'; exit 4
fi
python3 -I -B - "$BUN" "$KH" "$GO_SHA" <<'PY'
import json,re,sys
from pathlib import Path
b,k=map(Path,sys.argv[1:3]);authority=sys.argv[3]
lines=(b/'training.sbatch.out').read_text().splitlines()
jobs=[m[1] for line in lines if (m:=re.fullmatch(r'Submitted batch job ([1-9][0-9]*)',line))]
if len(jobs)!=1:raise SystemExit('UNCERTAIN: no unique training ID; inspect, never resubmit')
marker=json.loads((k/'o/canary_delta.json').read_text())
assert marker.get('canary_delta') is True and marker.get('admission_job')=='172180' and marker.get('authority')=='sha256:'+authority
assert marker.get('config_identity')=='774503e26f274a10c96ad06210d339c49ebc9a704ac254df81f389b0da4d98a1' and marker.get('submission')=='GATE_ACCEPTED'
with (b/'training.job.id').open('x') as f:f.write(jobs[0]+'\n')
with (b/'training.json').open('x') as f:json.dump(dict(run='6ed2c7aa',mode='CANARY_DELTA',admission_job='172180',training_job=jobs[0],authority='sha256:'+authority),f,sort_keys=True);f.write('\n')
print('SUBMITTED training_job='+jobs[0]+' advanced gpu=4 time=24:00:00')
PY
