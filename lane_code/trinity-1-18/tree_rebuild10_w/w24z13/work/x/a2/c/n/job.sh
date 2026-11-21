#!/bin/bash
set -euo pipefail
printf 'C00\n'
trap 'printf "TERM\n" > "$T_CASE/signal.TERM"; echo C37; exit 37' TERM
trap 'printf "USR1\n" > "$T_CASE/signal.USR1"; echo C38; exit 38' USR1
printf 'ready\n' > "$T_CASE/child.ready"
if [[ -n "$T_SIGNAL" ]]; then
    while true; do sleep 0.05; done
fi
echo C23
exit 23
