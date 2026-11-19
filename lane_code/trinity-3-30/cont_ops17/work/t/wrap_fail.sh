#!/bin/bash
#SBATCH --exclude=orchard-community-2
set -uo pipefail
P=/scratch/jjyeung/orch_n30/cont_ops17/work/t/pk_a2901e3d9fd05
L=/tmp/a${SLURM_JOB_ID:-0}.l
R=$P/a/x${SLURM_JOB_ID:-0}
fin(){ rc=$?; { head -n 1 "$L"; echo "exit $rc"; tail -n 60 "$L"; } > "$R" 2>/dev/null || true; exit $rc; }
trap fin EXIT
echo "node $(hostname -s) tmp_free_kb $(df -Pk /tmp | awk 'NR==2{print $4}') gpus $(nvidia-smi -L 2>/dev/null | wc -l) cvd ${CUDA_VISIBLE_DEVICES:-none}" > "$L" 2>/dev/null
/usr/bin/python3 -I -s -B - >>"$L" 2>&1 <<'A' &
import sys
print('hello')
sys.exit(3)
A
PID=$!
trap 'kill -USR1 $PID 2>/dev/null' USR1
while true; do wait $PID; rc=$?; kill -0 $PID 2>/dev/null || break; done
exit $rc
