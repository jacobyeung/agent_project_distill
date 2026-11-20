#!/bin/bash
#SBATCH -p advanced
#SBATCH --job-name=a15_cot_apb2edfac4
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:4
#SBATCH --cpus-per-task=48
#SBATCH --mem=800G
#SBATCH --time=24:00:00
#SBATCH --no-requeue
#SBATCH --signal=B:TERM@600
#SBATCH --output=/tmp/q_22c714e1_%j.log
#SBATCH --error=/tmp/q_22c714e1_%j.err
set -euo pipefail
umask 077
export PYTHONDONTWRITEBYTECODE=1
X='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z2/work/enospc2/wrapper/x'
ROOT="$X/n"
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID:?}"
mkdir -p "$N"
exec >>"$N/j2.log" 2>>"$N/j2.err"
cat > "$N/j2.py" <<'PYJ2'
import os,sys,time
from pathlib import Path
kit,node,target,job,parent=sys.argv[1:6]
node=Path(node);target=Path(target)/'o'/job
sys.path.insert(0,str(Path(kit)/'b'))
from z import load,screen
words=load(Path(kit)/'k/g.json');hashes=load(Path(kit)/'b/wh.json')
interval=float(sys.argv[6]) if len(sys.argv)>6 else 600
# This process owns no training pipe; failed publication cannot close one.
def publish():
    try:
        target.mkdir(parents=True,exist_ok=True,mode=0o700)
        for name in ('j2.log','j2.err'):
            with (node/name).open('rb') as f:
                f.seek(max(0,os.fstat(f.fileno()).st_size-300000))
                raw=screen(f.read().decode('utf-8','replace'),words,hashes).encode()[-300000:]
            temp=target/(name+'.part')
            with temp.open('wb') as f:f.write(raw)
            os.replace(temp,target/name)
    except OSError as e:
        with (node/'j2.retry.log').open('a') as f:
            f.write(str(int(time.time()))+' E'+str(e.errno)+'\n')
while True:
    publish()
    try:os.kill(int(parent),0)
    except ProcessLookupError:break
    time.sleep(interval)
PYJ2
setsid python3 -B -I -s "$N/j2.py" "$ROOT" "$N" "$X" "$SLURM_JOB_ID" "$$" >>"$N/j2.retry.log" 2>&1 &
python3 -I -s -B "$SLURM_TMPDIR/child.py" "$N" 2>&1 | python3 -I -s -B "$ROOT/b/l.py" "$ROOT"
while [[ ! -f "$SLURM_TMPDIR/finish" ]]; do sleep .1; done
