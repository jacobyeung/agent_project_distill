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
import signal,time,sys
got=[]
signal.signal(signal.SIGUSR1,lambda *a:got.append(1))
print('waiting',flush=True)
for i in range(50):
  time.sleep(0.1)
  if got: print('got usr1');sys.exit(0)
sys.exit(9)
A
PID=$!
trap 'kill -USR1 $PID 2>/dev/null' USR1
while true; do wait $PID; rc=$?; kill -0 $PID 2>/dev/null || break; done
exit $rc
