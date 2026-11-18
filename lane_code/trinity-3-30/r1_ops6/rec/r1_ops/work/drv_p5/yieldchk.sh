#!/bin/bash
set +x
set -Eeuo pipefail
export TZ=UTC
BUN=/project/community/jjyeung/okh7/i_69d2930d
KH=/project/community/jjyeung/okh7/x_69d2930d
job=$(cat "$BUN/job.id")
[[ "$job" =~ ^[1-9][0-9]*$ && "$job" != 170956 ]] || { echo 'REFUSED: invalid or failed proof job id'; exit 4; }
printf '%s  %s\n' 9dd2fbb77503ecee875d538ebaed933cc95ff286f76e5955fc2591f63e3f0192 "$BUN/p.tar" | sha256sum -c --quiet
q=$(squeue -u "$USER" -h -p general -o '%i|%j|%T|%r')
printf '%s\n' "$q"
# Report contention for the operator; this monitor never cancels a job.
if printf '%s\n' "$q" | grep -E 'jjy_.*QOSMaxJobsPerUser' >/dev/null; then
  echo "YIELD_REVIEW_REQUIRED job=$job; notify the orchestrator before any stop"
fi
