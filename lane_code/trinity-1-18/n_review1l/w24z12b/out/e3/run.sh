#!/bin/bash
set -euo pipefail
ROOT="$E3_N/k"
N="$E3_N/n"
export PATH="$E3_N/bin:$PATH"
source "$ROOT/b/pc.sh"
printf '%s\n' "$TK_LOG_PID" > "$E3_N/pid"
printf '%s\n' started > "$N/started"
while [[ ! -f "$E3_N/finish" ]]; do
    printf 'q 1\n' >> "$N/t.log"
    sleep 1
done
exit 0
