import json,secrets
from pathlib import Path
L=Path.cwd();D=L/'work/build24m4z8';seal=json.loads((D/'PIN.json').read_bytes())['output']['seal']
s=(L/'inputs/jd6.sh').read_text().replace('a15_cot_ap24d9b8e2','a15_cot_ap'+secrets.token_hex(6)).replace('ROOT="$X/qd"','ROOT="$X/qp_'+seal[:8]+'"')
s=s.replace('set -euo pipefail','set -euo pipefail\nif [[ "${J7_NICE:-0}" != 1 ]]; then export J7_NICE=1; exec nice -n 10 /bin/bash "$0" "$@"; fi',1)
s=s.replace('setsid python3 -B -I -s "$N/j2.py"','if [[ "${J7_INNER:-0}" != 1 ]]; then\nsetsid python3 -B -I -s "$N/j2.py"',1)
parent='''mkdir -p "$N/ev" "$O"
BW=$(python3 -B -I -s "$X/j7.py" b "$ROOT")
rc=0
J7_INNER=1 "$BW" --bind / / --bind "$N/ev" "$O" /bin/bash "$0" || rc=$?
python3 -B -I -s "$X/j7.py" p "$N" "$O" "$ROOT" "$rc" || rc=1
python3 -B -I -s "$N/j2.py" "$ROOT" "$N" "$X" "$SLURM_JOB_ID" 999999999 >>"$N/j2.retry.log" 2>&1 || true
exit "$rc"
fi
'''
s=s.replace('export TMPDIR="$N/tmp" XDG_CACHE_HOME="$N/cache"',parent+'export TMPDIR="$N/tmp" XDG_CACHE_HOME="$N/cache"',1)
call='nice -n 10 python3 -I -s -B "$X/rdiff.py"'
s=s.replace(call,'python3 -B -I -s "$X/j7.py" m "$N/dr/p/q/n.json" "$N/dr" "$N/rdm.json" && '+call)
s=s.replace('--removal-manifest "$N/dr/p/q/n.json"','--removal-manifest "$N/rdm.json"')
s=s.replace('fi; done ) &\n( for','fi; done ) &\nJ7_DBB=$!\n( for',1)
s=s.replace('fi; done ) &\nrc=0','fi; done ) &\nJ7_RD=$!\nrc=0',1)
s=s.replace('test -e "$O/db_bytes.json" || nice','wait "$J7_DBB" || true\nwait "$J7_RD" || true\ntest -e "$O/db_bytes.json" || nice')
(L/'out/jd7.sh').write_text(s)
pp='''#!/bin/bash
#SBATCH -p preempt
#SBATCH --job-name=a15_cot_apJOB
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --output=/tmp/p_22c714e1_%j.log
#SBATCH --error=/tmp/p_22c714e1_%j.err
set -euo pipefail
if [[ "${J7_NICE:-0}" != 1 ]]; then export J7_NICE=1; exec nice -n 10 /bin/bash "$0" "$@"; fi
umask 077
ulimit -v 15728640
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export CUDA_VISIBLE_DEVICES=""
X=/project/community/jjyeung/okh7/x_22c714e1
ROOT="$X/qp_SEAL"
N="${SLURM_TMPDIR:-/tmp}/p_22c714e1_${SLURM_JOB_ID:?}"
O="$X/o/$SLURM_JOB_ID"
mkdir -p "$N"
export TMPDIR="$N/tmp" XDG_CACHE_HOME="$N/cache" HF_HOME="$N/cache/hf"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
cd "$N"
rc=0
python3 -B -I -s "$X/j7.py" q "$ROOT" "$N/a" /project/community/jjyeung/okh7 >"$N/p0.log" 2>&1 || rc=$?
mkdir -p "$O"
test "$(stat -c %s "$N/a/p0.json")" -lt 100000
cp "$N/a/p0.json" "$O/p0.json"
exit "$rc"
'''.replace('JOB',secrets.token_hex(6)).replace('SEAL',seal[:8])
(L/'out/pp').mkdir();(L/'out/pp/pp.sh').write_text(pp)
for p in (L/'out/jd7.sh',L/'out/pp/pp.sh'):p.chmod(0o755)
print('qp_'+seal[:8])
