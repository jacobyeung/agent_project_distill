#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
O=/project/community/jjyeung/okh7
BUN=$O/i_c5f3847d
H=$O/x_3fdda0fb
OLD=$O/i_1be16f28
KH=$O/x_c5f3847d
private() { [[ -d "$1" && ! -L "$1" && $(stat -c %a "$1") == 700 ]] || { echo "REFUSED: private directory required: $1" >&2; exit 3; }; }
fresh() { [[ ! -e "$1" && ! -L "$1" ]] || { echo "REFUSED: already exists: $1" >&2; exit 3; }; }
private "$O"
private "$BUN"
private "$KH"
exec 9> "$BUN/p0.lock"
flock -n 9 || { echo 'REFUSED: concurrent proof submission'; exit 4; }
fresh "$BUN/submission.started"
fresh "$BUN/job.id"
fresh "$BUN/a.json"
# Show the entire queue once, then use exactly that snapshot for the guard.
Q=$(squeue -u "$USER" -h -o '%i|%j|%P|%T')
printf '%s\n' 'JOBID|NAME|PARTITION|STATE' "$Q"
while IFS='|' read -r jid name part state; do
 [[ -n "$jid" ]] || continue
 if [[ "$name" == a15_cot_ap26cc98b7 ]]; then echo 'REFUSED: job name already queued'; exit 4; fi
 if [[ "$name" == a15_cot_ap* && ",$part," == *,advanced,* && "$state" == PENDING ]]; then echo 'REFUSED: a15_cot_ap job pending on advanced'; exit 4; fi
done <<< "$Q"
python3 -B - "$KH" "$BUN" <<'PYCODE'
import hashlib,json,stat,sys
from pathlib import Path
k,b=map(Path,sys.argv[1:]);load=lambda p:json.loads(p.read_text())
assert (b/'d0/rc').read_text().strip()=='0' and load(b/'compare.json')['status']=='READY'
auth=load(k/'k/4.json');assert auth['partition']=='advanced' and auth['modes']==['p'] and auth['production_go_granted'] is False
assert auth['gpu_cap']==4 and auth['max_parallel_jobs']==1 and auth['new_gpus']['p']==0
cert=load(k/'ANON_OK.json');assert cert['status']=='CLEAN' and cert['hits']==0 and cert.get('reviewer')
assert cert['manifest_sha256']==hashlib.sha256((k/'SHA256SUMS.txt').read_bytes()).hexdigest()
for entry in cert.get('external',[]):assert hashlib.sha256(Path(entry['path']).read_bytes()).hexdigest()==entry['sha256']
s=k/'sess.json';assert not s.is_symlink() and stat.S_IMODE(s.stat().st_mode)==0o600
sessions=load(s);assert set(sessions)==set((b/'e.txt').read_text().split()) and len(sessions)==20
assert len(set(sessions.values()))==20 and all(x.startswith('https://storage.googleapis.com/upload/') for x in sessions.values())
sys.path.insert(0,str(k/'b'));import a
a.main(k)
print('PASS sealed kit, independent scan, evidence, and 20 private sessions')
PYCODE
PARTITION=advanced
python3 -B "$BUN/p.py" --kit "$KH" --bundle "$BUN" --binding "$BUN/BINDING.json" --partition "$PARTITION" --out "$BUN/a.json"
mkdir -p -m 700 "$KH/o"
# A timeout or uncertain sbatch result must be reconciled manually; never resubmit.
(set -o noclobber; date -u +%FT%TZ > "$BUN/submission.started")
printf '%s\n' "TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable -J a15_cot_ap26cc98b7 -A mt01 -p advanced -N1 --ntasks=1 -c 48 --mem=800G -t 04:00:00 --no-requeue -o $KH/o/%j.out -e $KH/o/%j.err $BUN/p_26cc98b7.sh $BUN/a.json"
TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable -J a15_cot_ap26cc98b7 -A mt01 -p "$PARTITION" -N1 --ntasks=1 -c 48 --mem=800G -t 04:00:00 --no-requeue -o "$KH/o/%j.out" -e "$KH/o/%j.err" "$BUN/p_26cc98b7.sh" "$BUN/a.json" > "$BUN/sbatch.out"
answer=$(cat "$BUN/sbatch.out")
[[ "$answer" =~ ^[0-9]+(\;[A-Za-z0-9_-]+)?$ ]] || { echo 'UNCERTAIN: inspect queue; do not resubmit'; exit 4; }
job=${answer%%;*}
printf '%s\n' "$job" > "$BUN/job.id"
echo "SUBMITTED job_id=$job; production GO remains false"
