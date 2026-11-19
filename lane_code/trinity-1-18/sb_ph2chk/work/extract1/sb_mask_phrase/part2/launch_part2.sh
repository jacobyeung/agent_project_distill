#!/usr/bin/env bash
# CPU scoring launcher. One process avoids shard-admission races and uses at most 8 cores.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
mode=${1:-}
case "$mode" in capture|fixture-capture) ;; *) echo "mode: capture | fixture-capture" >&2; exit 2;; esac
export PYTHONDONTWRITEBYTECODE=1
/scratch/jjyeung/envs/p1cpu/bin/python -B part2/gate.py "$mode"
# Logs are created only after bars and scored-output admission have passed.
logdir=out/part2/logs
mkdir -p "$logdir"
bash run.sh part2/price.py "$mode" 0 1 "${@:2}" > "$logdir/${mode}.log" 2>&1
