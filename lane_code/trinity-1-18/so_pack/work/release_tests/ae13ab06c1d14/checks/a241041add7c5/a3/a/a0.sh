#!/bin/bash
#SBATCH --exclude=orchard-community-2
set -uo pipefail
P=/scratch/jjyeung/orch_n30/so_pack/work/release_tests/ae13ab06c1d14/a15_cot_apd45befa4edc73
L=/scratch/jjyeung/orch_n30/so_pack/work/release_tests/ae13ab06c1d14/checks/a241041add7c5/a3/a/a0.log
R=/scratch/jjyeung/orch_n30/so_pack/work/release_tests/ae13ab06c1d14/checks/a241041add7c5/a3/a/a0.capture
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
