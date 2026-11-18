#!/bin/bash
set +x
set -Eeuo pipefail
export TZ=UTC
BUN=/scratch/jjyeung/orch_n30/r1_ops/work/drv_c1/monitor_c1_djht8y90/remote/i_7f1589c1
KH=/scratch/jjyeung/orch_n30/r1_ops/work/drv_c1/monitor_c1_djht8y90/remote/x_7f1589c1
job=$(cat "$BUN/job.id")
[[ "$job" =~ ^[1-9][0-9]*$ ]] || { echo 'REFUSED: invalid or failed proof job id'; exit 4; }
printf '%s  %s\n' 08f3a7b2ef2e1923ba77b464afcedbbe668a77a1915b4c32c0a815044ff7d9fd "$BUN/p.tar" | sha256sum -c --quiet
sacct -j "$job" -X -o JobID,State,ExitCode,Elapsed,End -P
for suffix in proof.json proof.log; do
  printf '\n%s\n' "$job.$suffix"
  [[ -f "$KH/o/$job.$suffix" && ! -L "$KH/o/$job.$suffix" ]] || { echo NOT_YET; continue; }
  head -c 600000 "$KH/o/$job.$suffix"
done
