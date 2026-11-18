#!/bin/bash
set +x
set -Eeuo pipefail
export TZ=UTC
BUN=/project/community/jjyeung/okh7/i_69d2930d
KH=/project/community/jjyeung/okh7/x_69d2930d
job=$(cat "$BUN/job.id")
[[ "$job" =~ ^[1-9][0-9]*$ && "$job" != 170956 ]] || { echo 'REFUSED: invalid or failed proof job id'; exit 4; }
printf '%s  %s\n' 9dd2fbb77503ecee875d538ebaed933cc95ff286f76e5955fc2591f63e3f0192 "$BUN/p.tar" | sha256sum -c --quiet
sacct -j "$job" -X -o JobID,State,ExitCode,Elapsed,End -P
for suffix in proof.json proof.log; do
  printf '\n%s\n' "$job.$suffix"
  [[ -f "$KH/o/$job.$suffix" && ! -L "$KH/o/$job.$suffix" ]] || { echo NOT_YET; continue; }
  head -c 600000 "$KH/o/$job.$suffix"
done
