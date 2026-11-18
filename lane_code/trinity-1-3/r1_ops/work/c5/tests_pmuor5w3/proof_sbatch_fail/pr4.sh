#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
O=/scratch/jjyeung/orch_n30/r1_ops/work/c5/tests_pmuor5w3/proof_sbatch_fail
BUN=$O/i_7f1589c1
H=$O/x_3fdda0fb
OLD=$O/i_1be16f28
KH=$O/x_7f1589c1
private() { [[ -d "$1" && ! -L "$1" && $(stat -c %a "$1") == 700 ]] || { echo "REFUSED: private directory required: $1" >&2; exit 3; }; }
fresh() { [[ ! -e "$1" && ! -L "$1" ]] || { echo "REFUSED: already exists: $1" >&2; exit 3; }; }
packet() { printf '%s  %s\n' 'd7b862d96e335437389ec6eae2503599c37487d9b78ac822f8a2f37e0cc6d4fa' "$BUN/p.tar" | sha256sum -c --quiet; }
private "$O"
PARTITION=general
# The waiver authorizes only a held CPU proof submission.
[[ ${1:-} != general ]] || shift
[[ $# == 4 && "$1" == --hold && "$2" == --waive-rehearsal && "$3" =~ ^[0-9a-f]{64}$ && "$4" == /* ]] || {
 echo 'REFUSED: use pr4.sh [general] --hold --waive-rehearsal <sha256> <absolute event file>'; exit 4;
}
HOLD=(--hold)
WAIVER_SHA=$3
WAIVER_FILE=$4
private "$BUN"
packet
private "$KH"
exec 9> "$BUN/p0.lock"
flock -n 9 || { echo 'REFUSED: concurrent proof submission'; exit 4; }
fresh "$BUN/submission.started"
fresh "$BUN/job.id"
fresh "$BUN/a.json"
# Show the entire queue once, then use exactly that snapshot for the guard.
Q=$(squeue -h -o '%i|%j|%P|%T')
printf '%s\n' 'JOBID|NAME|PARTITION|STATE' "$Q"
while IFS='|' read -r jid name part state; do
 [[ -n "$jid" ]] || continue
 if [[ "$name" == a15_cot_ap05b8ac69 ]]; then echo 'REFUSED: job name already queued'; exit 4; fi
done <<< "$Q"
python3 -I -B - <<'HISTORY'
"""Only the failed C proof is an allocated predecessor; bootstrap had no ID."""
import os, subprocess
from pathlib import Path
b=Path('/scratch/jjyeung/orch_n30/r1_ops/work/c5/tests_pmuor5w3/proof_sbatch_fail/i_7f1589c1.f172180')
rows=subprocess.run(['sacct','-X','-n','-P','-S','2026-11-17','--name','a15_cot_ap05b8ac69','-o','JobIDRaw,JobName%64,State,ExitCode'],check=True,capture_output=True,text=True,timeout=60).stdout
seen=[]
for line in rows.splitlines():
 if not line.strip():continue
 r=line.strip().rstrip('|').split('|')
 if r!=['172180','a15_cot_ap05b8ac69','FAILED','1:0']:raise SystemExit('REFUSED: unexpected C accounting history: '+line)
 seen.append(r)
if len(seen)!=1:raise SystemExit('REFUSED: FAILED 172180 accounting missing or ambiguous')
if (b/'job.id').read_text().strip()!='172180':raise SystemExit('REFUSED: moved proof ID differs')
for name in ('sbatch.out.a1_bootstrap','submission.started.a1_bootstrap','a.json.a1_bootstrap'):
 p=b/name
 if p.is_symlink() or not p.is_file():raise SystemExit('REFUSED: rejected bootstrap provenance missing')
if (b/'sbatch.out.a1_bootstrap').stat().st_size:raise SystemExit('REFUSED: bootstrap attempt has a submission receipt')
print('PASS history: FAILED 172180 and rejected bootstrap only')

HISTORY
python3 -B - "$KH" "$BUN" "$PARTITION" "$WAIVER_SHA" "$WAIVER_FILE" <<'PYCODE'
"""Sealed resource authority for one continuation kit; GO is separate."""
import copy


def fields():
    return dict(
        modes=['p', 't', 'u'], new_gpus={'p': 0, 't': 4, 'u': 4},
        partition='advanced', allowed_partitions=['advanced', 'general', 'bootstrap'],
        wall_seconds=86400, nodes=1, resume='latest', arm='0', gpu_cap=4,
        other_running_and_pending_gpus=0, max_parallel_jobs=1,
        production_go_granted=False, production_go_required_separately=True,
        mode_resources={
            'p': dict(partitions=['general', 'bootstrap'], nodes=1, gpus=0, wall_seconds=14400),
            't': dict(partitions=['advanced'], nodes=1, gpus=4, wall_seconds=86400),
            'u': dict(partitions=['advanced'], nodes=1, gpus=4, wall_seconds=86400)},
    )


def bind(auth):
    value=copy.deepcopy(auth)
    value.update(fields())
    value.update(scope='Sealed CPU proof and continuation resources; separate identity-bound GO required for training.',
                 conditions=['Mode p: general/bootstrap, one node, zero GPUs, four hours.',
                             'Modes t/u: advanced, one node, four GPUs, 24 hours; resume latest.',
                             'Certify the final manifest before proof; never mutate the certified kit.',
                             'Training submission requires a separate identity-bound go.json.'])
    return value


def validate(auth):
    for key, value in fields().items():
        # JSON equality alone would admit booleans in place of integer counts.
        import json
        if json.dumps(auth.get(key),sort_keys=True)!=json.dumps(value,sort_keys=True):
            raise ValueError('Continuation authority differs: '+key)


def allocation(auth, mode, environment):
    validate(auth)
    if mode not in auth['modes']:
        raise ValueError('Operation not authorized')
    # Native admission runs mode p inside the already allocated training job.
    # The sealed entry sets its allocation mode before p0 and recursive r.sh p.
    allocation_mode=environment.get('TK_ALLOCATION_MODE',mode)
    if allocation_mode not in auth['modes'] or (mode!='p' and allocation_mode!=mode):
        raise ValueError('Allocation mode differs')
    limits=auth['mode_resources'][allocation_mode]
    if environment.get('SLURM_JOB_PARTITION') not in limits['partitions']:
        raise ValueError('Partition not authorized for mode '+mode)
    if (environment.get('SLURM_JOB_NUM_NODES')!='1'
            or environment.get('SLURM_GPUS_ON_NODE','0')!=str(limits['gpus'])):
        raise ValueError('Resources differ')
    if allocation_mode=='p' and environment.get('CUDA_VISIBLE_DEVICES','') not in ('','-1','NoDevFiles'):
        raise ValueError('Proof must be CPU-only')
    # Slurm does not export this variable on every site. The sealed job script
    # and launch slot also pin the wall limit; check the allocation when supplied.
    wall=environment.get('SLURM_TIMELIMIT')
    if wall is not None:
        if wall.isdigit():
            seconds=int(wall)*60
        else:
            days, clock=wall.split('-',1) if '-' in wall else ('0',wall)
            parts=[int(v) for v in clock.split(':')]
            if len(parts)==2:parts=[0,*parts]
            if len(parts)!=3:raise ValueError('Invalid allocation wall limit')
            seconds=int(days)*86400+parts[0]*3600+parts[1]*60+parts[2]
        if seconds!=limits['wall_seconds']:
            raise ValueError('Allocation wall limit differs')
    return limits

def check_authority(kit):
    """Authenticate the deployed authority before checking its resource limits."""
    import hashlib
    import json
    import re
    from pathlib import Path
    for entry in kit.iterdir():
        if entry.is_symlink() or entry.name not in {'SHA256SUMS.txt','ANON_OK.json','b','k','job.sh','job8.sh','o','arm','runs','sess.json'}:
            raise ValueError('Unexpected kit top-level entry: '+entry.name)
    manifest = kit/'SHA256SUMS.txt'
    if manifest.is_symlink() or not manifest.is_file():
        raise ValueError('Missing or linked derived manifest')
    pins = {}
    for line in manifest.read_text().splitlines():
        digest, name = line.split('  ', 1)
        if (not re.fullmatch('[0-9a-f]{64}', digest) or name in pins
                or Path(name).is_absolute() or '..' in Path(name).parts):
            raise ValueError('Invalid derived manifest')
        pins[name] = digest
    path = kit/'k/4.json'
    if (path.parent.is_symlink() or path.is_symlink() or not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != pins.get('k/4.json')):
        raise ValueError('Authority SHA differs from derived manifest')
    auth = json.loads(path.read_bytes())
    validate(auth)
    for key, value in dict(config_sha256='6594f46cdc16168514aca26a6ce38285907adfc6ece0b75d8e10428ea0b2fe74',
                           source_revision='sha256:b83a8a35d420815b9d6396e1fc1178e94c20d47ad459aa6da964e85bdec0f87b',
                           admission_contract_sha256='26059aff098020a08adcef7ad6ced09ab2aedb2edd4f3c6607028e496ebb8970').items():
        if auth.get(key) != value:
            raise ValueError('Authority identity differs: '+key)
    print('PASS sealed p/t/u authority; k/4.json SHA matches derived manifest')
    return auth

import hashlib,json,stat,sys
from pathlib import Path
k,b=map(Path,sys.argv[1:3]);partition=sys.argv[3];load=lambda p:json.loads(p.read_text())
waiver_sha,waiver_path=sys.argv[4:6]
wp=Path(waiver_path)
assert wp.is_absolute() and wp.is_file() and not wp.is_symlink() and wp.resolve()==wp, 'regular absolute waiver file required'
assert hashlib.sha256(wp.read_bytes()).hexdigest()==waiver_sha, 'waiver SHA differs'
rp=k/'o/172467.rehearsal.json'
assert rp.is_file() and not rp.is_symlink(), 'failed rehearsal receipt required'
raw=rp.read_bytes();r=json.loads(raw)
assert r.get('job')=='172467' and r.get('status')=='REHEARSAL_FAIL' and r.get('rc')==1 and r.get('admission_executed') is False, 'failed rehearsal receipt differs'
waiver=dict(waiver_file=str(wp),waiver_sha256=waiver_sha,failing_rehearsal='172467',
            failing_receipt=str(rp),failing_receipt_sha256=hashlib.sha256(raw).hexdigest(),
            partition='general',held=True,rehearsal_waived=True,production_go_granted=False)
marker=k/'o/pr4.waiver.json'
assert not marker.exists() and not marker.is_symlink(), 'waiver marker exists; inspect, never retry'
assert (b/'d0/rc').read_text().strip()=='0' and load(b/'compare.json')['status']=='READY'
auth=check_authority(k)
assert partition in auth['mode_resources']['p']['partitions']
cert=load(k/'ANON_OK.json');assert cert['status']=='CLEAN' and cert['hits']==0 and cert.get('reviewer')
assert cert.get('config_identity')=='6594f46cdc16168514aca26a6ce38285907adfc6ece0b75d8e10428ea0b2fe74' and cert.get('operator_archive_sha256')=='d7b862d96e335437389ec6eae2503599c37487d9b78ac822f8a2f37e0cc6d4fa'
assert cert.get('scan_record_sha256') and cert.get('exemption_sha256')=='22a371b35e86ff8a48ed0b03c718d15fb656d1d342dd3c441d9986ac70ea0720'
assert cert['manifest_sha256']==hashlib.sha256((k/'SHA256SUMS.txt').read_bytes()).hexdigest()
for entry in cert.get('external',[]):assert hashlib.sha256(Path(entry['path']).read_bytes()).hexdigest()==entry['sha256']
s=k/'sess.json';assert not s.is_symlink() and stat.S_IMODE(s.stat().st_mode)==0o600
sessions=load(s);assert set(sessions)==set((b/'e.txt').read_text().split()) and len(sessions)==20
assert len(set(sessions.values()))==20 and all(x.startswith('https://storage.googleapis.com/upload/') for x in sessions.values())
sys.path.insert(0,str(k/'b'));import a
a.main(k)
print('PASS sealed kit, independent scan, evidence, and 20 private sessions')
with marker.open('x') as f:json.dump(waiver,f,sort_keys=True);f.write('\n')
print('PASS explicit rehearsal waiver; HELD proof only')
PYCODE
python3 -B "$BUN/p.py" --kit "$KH" --bundle "$BUN" --binding "$BUN/BINDING.json" --partition "$PARTITION" --out "$BUN/a.json"
mkdir -p -m 700 "$KH/o"
# A timeout or uncertain sbatch result must be reconciled manually; never resubmit.
(set -o noclobber; date -u +%FT%TZ > "$BUN/submission.started")
printf '%s\n' "TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable ${HOLD[*]} -J a15_cot_ap05b8ac69 -A mt01 -p $PARTITION -N1 --ntasks=1 -c 48 --mem=800G -t 04:00:00 --no-requeue -o $KH/o/%j.out -e $KH/o/%j.err $BUN/p_05b8ac69.sh $BUN/a.json"
TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable "${HOLD[@]}" -J a15_cot_ap05b8ac69 -A mt01 -p "$PARTITION" -N1 --ntasks=1 -c 48 --mem=800G -t 04:00:00 --no-requeue -o "$KH/o/%j.out" -e "$KH/o/%j.err" "$BUN/p_05b8ac69.sh" "$BUN/a.json" > "$BUN/sbatch.out"
answer=$(cat "$BUN/sbatch.out")
[[ "$answer" =~ ^[1-9][0-9]*(\;[A-Za-z0-9_-]+)?$ ]] || { echo 'UNCERTAIN: inspect queue; do not resubmit'; exit 4; }
job=${answer%%;*}
printf '%s\n' "$job" > "$BUN/job.id"
python3 -I -B - "$KH" "$job" <<'LEDGER'
import json,sys
from pathlib import Path
k=Path(sys.argv[1]);job=sys.argv[2]
r=json.loads((k/'o/pr4.waiver.json').read_text())
r.update(job=job,submission='HELD_REQUESTED')
with (k/'o'/(job+'.waiver.json')).open('x') as f:json.dump(r,f,sort_keys=True);f.write('\n')
LEDGER
echo "SUBMITTED job_id=$job; HELD requested; production GO remains false"
