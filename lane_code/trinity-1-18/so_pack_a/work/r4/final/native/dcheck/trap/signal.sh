#!/bin/bash
#SBATCH --exclude=orchard-community-2
set -uo pipefail
umask 077
P=/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final/native/dcheck/trap/p
L=/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final/native/dcheck/trap/0.log
R=$P/a/x${SLURM_JOB_ID:-0}
fin(){ rc=$?; { sed -n '1p' "$L"; echo "exit $rc"; tail -n 60 "$L"; } > "$R" 2>/dev/null || true; exit $rc; }
trap fin EXIT
echo "node $(hostname -s) tmp_free_kb $(df -Pk /tmp | awk 'NR==2{print $4}') gpus 0 cvd ${CUDA_VISIBLE_DEVICES:-none}" > "$L" 2>/dev/null
/usr/bin/python3 -I -s -B - >>"$L" 2>&1 <<'A' &
import signal,time
from pathlib import Path
def stop(*a):
 Path('/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final/native/dcheck/trap/slot').write_text('slot');raise SystemExit(0)
signal.signal(signal.SIGUSR1,stop)
Path('/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final/native/dcheck/trap/ready').write_text('ready')
time.sleep(10)
A
PID=$!
trap 'kill -USR1 $PID 2>/dev/null' USR1
while true; do wait $PID; rc=$?; kill -0 $PID 2>/dev/null || break; done
exit $rc
