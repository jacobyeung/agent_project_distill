#!/bin/bash
#SBATCH --exclude=orchard-community-2
set -uo pipefail
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/B5/package
L=/scratch/jjyeung/orch_n30/so_pack/work/verified_tests/a9452502036de/bad/a1.log
R=/scratch/jjyeung/orch_n30/so_pack/work/verified_tests/a9452502036de/bad/a1.capture
fin(){ rc=$?; { head -n 1 "$L"; echo "exit $rc"; tail -n 60 "$L"; } > "$R" 2>/dev/null || true; exit $rc; }
trap fin EXIT
echo "node fixture" > "$L"
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - >>"$L" 2>&1 <<'A' &
import signal,time
from pathlib import Path
ready=Path('/scratch/jjyeung/orch_n30/so_pack/work/verified_tests/a9452502036de/bad/a1.ready');stop=Path('/scratch/jjyeung/orch_n30/so_pack/work/verified_tests/a9452502036de/bad/a1.stop');end=Path('/scratch/jjyeung/orch_n30/so_pack/work/verified_tests/a9452502036de/bad/a1.end')
signal.signal(signal.SIGUSR1,signal.SIG_IGN)
ready.write_text('ready\n')
deadline=time.time()+1.5
while time.time()<deadline and not stop.exists():time.sleep(0.01)
if stop.exists():end.write_text('slot\n')
raise SystemExit(0 if end.exists() else 7)

A
PID=$!
trap 'kill -USR1 $PID 2>/dev/null' USR1
while true; do wait $PID; rc=$?; kill -0 $PID 2>/dev/null || break; done
exit $rc
