#!/bin/bash
set -euo pipefail
ROOT="$E2_N/k"
N="$E2_N/n"
export PATH="$E2_N/bin:$PATH"
source "$ROOT/b/pc.sh"
printf '%s\n' "$TK_LOG_PID" > "$E2_N/pid"
printf '%s\n' started > "$N/started"
while [[ ! -f "$E2_N/finish" ]]; do
    printf 'q 1\n' >> "$N/t.log"
    sleep 1
done
exit 0
