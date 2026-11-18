#!/bin/bash
set +x
set -Eeuo pipefail
export TZ=UTC
BUN=/scratch/jjyeung/orch_n30/r1_ops/work/drv_c1/monitor_c1_wm4mieu7/remote/i_7f1589c1
KH=/scratch/jjyeung/orch_n30/r1_ops/work/drv_c1/monitor_c1_wm4mieu7/remote/x_7f1589c1
job=$(cat "$BUN/job.id")
[[ "$job" =~ ^[1-9][0-9]*$ ]] || { echo 'REFUSED: invalid or failed proof job id'; exit 4; }
printf '%s  %s\n' 6a5c7d009a19cb5bac690b864f2be68bb5cebc29649923c93da36328d0f96888 "$BUN/p.tar" | sha256sum -c --quiet
sacct -j "$job" -X -o JobID,State,ExitCode,Elapsed,End -P
for suffix in proof.json proof.log; do
  printf '\n%s\n' "$job.$suffix"
  [[ -f "$KH/o/$job.$suffix" && ! -L "$KH/o/$job.$suffix" ]] || { echo NOT_YET; continue; }
  head -c 600000 "$KH/o/$job.$suffix"
done
