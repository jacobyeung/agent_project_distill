#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
BUN=/scratch/jjyeung/orch_n30/r1_ops/work/drv_c1/rehearsal_c3_9ttj77ab/queued/i_7f1589c1
KH=/scratch/jjyeung/orch_n30/r1_ops/work/drv_c1/rehearsal_c3_9ttj77ab/queued/x_7f1589c1
printf '%s  %s\n' '08f3a7b2ef2e1923ba77b464afcedbbe668a77a1915b4c32c0a815044ff7d9fd' "$BUN/p.tar" | sha256sum -c --quiet
[[ $# == 0 ]] || exit 2
cd "$BUN"
exec 9> "$BUN/rehearsal.lock"
flock -n 9 || { echo 'REFUSED: concurrent rehearsal'; exit 4; }
for name in rehearsal.started rehearsal.job.id rehearsal.sbatch.out rehearsal.json a4.json; do
 [[ ! -e "$BUN/$name" && ! -L "$BUN/$name" ]] || { echo "REFUSED: existing $name; inspect, never retry"; exit 4; }
done
Q=$(squeue -h -o '%i|%j|%P|%T')
printf '%s\n' "$Q"
[[ "$Q" != *a15_cot_ap05b8ac6a* && "$Q" != *a15_cot_ap05b8ac69* ]] || { echo 'REFUSED: C proof or rehearsal queued'; exit 4; }
true --kit "$KH" --bundle "$BUN" --binding "$BUN/BINDING.json" --partition general --out "$BUN/a4.json"
(set -o noclobber; date -u +%FT%TZ > "$BUN/rehearsal.started")
sbatch --partition=general --nodelist=orchard-community-0 --nodes=1 --ntasks=1 --cpus-per-task=4 --mem=32G --time=00:30:00 --gres=gpu:0 --job-name=a15_cot_ap05b8ac6a --no-requeue --output=/scratch/jjyeung/orch_n30/r1_ops/work/drv_c1/rehearsal_c3_9ttj77ab/queued/x_7f1589c1/o/%j.rehearsal.out --error=/scratch/jjyeung/orch_n30/r1_ops/work/drv_c1/rehearsal_c3_9ttj77ab/queued/x_7f1589c1/o/%j.rehearsal.err /scratch/jjyeung/orch_n30/r1_ops/work/drv_c1/rehearsal_c3_9ttj77ab/queued/i_7f1589c1/p_05b8ac69.sh /scratch/jjyeung/orch_n30/r1_ops/work/drv_c1/rehearsal_c3_9ttj77ab/queued/i_7f1589c1/a4.json --rehearsal /tmp/jjyeung/p_05b8ac69_172180/tmp/jjyeung/a_05b8ac69/root > "$BUN/rehearsal.sbatch.out"
python3 -I -B - "$BUN" <<'END'
import json,re,sys
from pathlib import Path
b=Path(sys.argv[1]);s=(b/'rehearsal.sbatch.out').read_text().strip()
m=re.fullmatch(r'Submitted batch job ([1-9][0-9]*)',s)
if not m:raise SystemExit('UNCERTAIN: no rehearsal ID; inspect; never resubmit')
job=m[1]
with (b/'rehearsal.job.id').open('x') as f:f.write(job+'\n')
with (b/'rehearsal.json').open('x') as f:json.dump(dict(job=job,kind='REHEARSAL',partition='general',gpus=0,authority='a4.json',proof=False),f,sort_keys=True)
print('SUBMITTED rehearsal_job='+job+'; never a PASS proof')
END
