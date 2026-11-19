#!/bin/bash
#SBATCH --exclude=orchard-community-2
set -uo pipefail
P=/scratch/jjyeung/orch_n30/so_pack/work/tests04/a78a381cd6aa1/a15_cot_apdc01c6a1bee84
L=/scratch/jjyeung/orch_n30/so_pack/work/tests04/a78a381cd6aa1/checks/ad14678df8c64/a3/a/a0.log
R=/scratch/jjyeung/orch_n30/so_pack/work/tests04/a78a381cd6aa1/checks/ad14678df8c64/a3/a/a0.capture
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
