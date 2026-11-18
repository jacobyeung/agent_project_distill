#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
O=/scratch/jjyeung/orch_n30/r1_ops/work/drv_c1/guards_p5_jm49ukg1/same_name_running
BUN=$O/i_7f1589c1
H=$O/x_3fdda0fb
OLD=$O/i_1be16f28
KH=$O/x_7f1589c1
private() { [[ -d "$1" && ! -L "$1" && $(stat -c %a "$1") == 700 ]] || { echo "REFUSED: private directory required: $1" >&2; exit 3; }; }
fresh() { [[ ! -e "$1" && ! -L "$1" ]] || { echo "REFUSED: already exists: $1" >&2; exit 3; }; }
packet() { printf '%s  %s\n' '6a5c7d009a19cb5bac690b864f2be68bb5cebc29649923c93da36328d0f96888' "$BUN/p.tar" | sha256sum -c --quiet; }
private "$O"
PARTITION=${1:-bootstrap}
[[ $# -le 1 && ( "$PARTITION" == general || "$PARTITION" == bootstrap ) ]] || { echo 'REFUSED: partition must be bootstrap or general'; exit 4; }
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
python3 -B - "$KH" "$BUN" "$PARTITION" <<'PYCODE'
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
assert (b/'d0/rc').read_text().strip()=='0' and load(b/'compare.json')['status']=='READY'
auth=check_authority(k)
assert partition in auth['mode_resources']['p']['partitions']
cert=load(k/'ANON_OK.json');assert cert['status']=='CLEAN' and cert['hits']==0 and cert.get('reviewer')
assert cert.get('config_identity')=='6594f46cdc16168514aca26a6ce38285907adfc6ece0b75d8e10428ea0b2fe74' and cert.get('operator_archive_sha256')=='6a5c7d009a19cb5bac690b864f2be68bb5cebc29649923c93da36328d0f96888'
assert cert.get('scan_record_sha256') and cert.get('exemption_sha256')=='22a371b35e86ff8a48ed0b03c718d15fb656d1d342dd3c441d9986ac70ea0720'
assert cert['manifest_sha256']==hashlib.sha256((k/'SHA256SUMS.txt').read_bytes()).hexdigest()
for entry in cert.get('external',[]):assert hashlib.sha256(Path(entry['path']).read_bytes()).hexdigest()==entry['sha256']
s=k/'sess.json';assert not s.is_symlink() and stat.S_IMODE(s.stat().st_mode)==0o600
sessions=load(s);assert set(sessions)==set((b/'e.txt').read_text().split()) and len(sessions)==20
assert len(set(sessions.values()))==20 and all(x.startswith('https://storage.googleapis.com/upload/') for x in sessions.values())
sys.path.insert(0,str(k/'b'));import a
a.main(k)
print('PASS sealed kit, independent scan, evidence, and 20 private sessions')
PYCODE
python3 -B "$BUN/p.py" --kit "$KH" --bundle "$BUN" --binding "$BUN/BINDING.json" --partition "$PARTITION" --out "$BUN/a.json"
mkdir -p -m 700 "$KH/o"
# A timeout or uncertain sbatch result must be reconciled manually; never resubmit.
(set -o noclobber; date -u +%FT%TZ > "$BUN/submission.started")
printf '%s\n' "TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable -J a15_cot_ap05b8ac69 -A mt01 -p $PARTITION -N1 --ntasks=1 -c 48 --mem=800G -t 04:00:00 --no-requeue -o $KH/o/%j.out -e $KH/o/%j.err $BUN/p_05b8ac69.sh $BUN/a.json"
TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable -J a15_cot_ap05b8ac69 -A mt01 -p "$PARTITION" -N1 --ntasks=1 -c 48 --mem=800G -t 04:00:00 --no-requeue -o "$KH/o/%j.out" -e "$KH/o/%j.err" "$BUN/p_05b8ac69.sh" "$BUN/a.json" > "$BUN/sbatch.out"
answer=$(cat "$BUN/sbatch.out")
[[ "$answer" =~ ^[1-9][0-9]*(\;[A-Za-z0-9_-]+)?$ ]] || { echo 'UNCERTAIN: inspect queue; do not resubmit'; exit 4; }
job=${answer%%;*}
printf '%s\n' "$job" > "$BUN/job.id"
echo "SUBMITTED job_id=$job; production GO remains false"
