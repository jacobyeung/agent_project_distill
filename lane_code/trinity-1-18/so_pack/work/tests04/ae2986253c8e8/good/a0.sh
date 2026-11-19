#!/bin/bash
#SBATCH --exclude=orchard-community-2
set -uo pipefail
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/B5/package
L=/scratch/jjyeung/orch_n30/so_pack/work/tests04/ae2986253c8e8/good/a0.log
R=/scratch/jjyeung/orch_n30/so_pack/work/tests04/ae2986253c8e8/good/a0.capture
fin(){ rc=$?; { head -n 1 "$L"; echo "exit $rc"; tail -n 60 "$L"; } > "$R" 2>/dev/null || true; exit $rc; }
trap fin EXIT
echo "node fixture" > "$L"
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - >>"$L" 2>&1 <<'A' &
raise RuntimeError('pack planted early failure')
A
PID=$!
trap 'kill -USR1 $PID 2>/dev/null' USR1
while true; do wait $PID; rc=$?; kill -0 $PID 2>/dev/null || break; done
exit $rc
