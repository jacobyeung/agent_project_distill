#!/usr/bin/env bash
# The pinned vnice wrapper starts this local monitor. Its control file stays in the pass output.
set -euo pipefail
pid=$1
file="$PART2_OUT/vnice-${pid}"
printf 'Remove this file to stop the GPU pass.\n' > "$file"
chmod a+rw "$file"
while [[ -d /proc/$pid ]]; do
  if [[ ! -e "$file" ]]; then
    # The launcher creates a separate session; this group contains only this pass.
    group=$(ps -o pgid= "$pid" | tr -d ' ')
    kill -KILL -- "-$group"
    exit 1
  fi
  sleep 1
done
