#!/bin/bash
set +x
set -Eeuo pipefail
export TZ=UTC
BUN=/project/community/jjyeung/okh7/i_7f1589c1
KH=/project/community/jjyeung/okh7/x_7f1589c1
job=$(cat "$BUN/job.id")
[[ "$job" =~ ^[1-9][0-9]*$ ]] || { echo 'REFUSED: invalid or failed proof job id'; exit 4; }
printf '%s  %s\n' c60b901594843989b909cb785a5fdc9ad544ea0fdec8d78c63bf173e4f6e136c "$BUN/p.tar" | sha256sum -c --quiet
sacct -j "$job" -X -o JobID,State,ExitCode,Elapsed,End -P
for suffix in proof.json proof.log; do
  printf '\n%s\n' "$job.$suffix"
  [[ -f "$KH/o/$job.$suffix" && ! -L "$KH/o/$job.$suffix" ]] || { echo NOT_YET; continue; }
  head -c 600000 "$KH/o/$job.$suffix"
done
