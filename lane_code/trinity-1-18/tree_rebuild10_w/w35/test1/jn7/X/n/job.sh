#!/bin/bash
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID}"; C=$(cat /tmp/case_${SLURM_JOB_ID})
start() { mkdir -p "$N/p/q/r"; : > "$N/t.log"; echo '{}' > "$N/p/rv.json"; }
case $C in
  presave) start; exit 1 ;;
  stop) start; trap 'exit 143' TERM; sleep 300 & wait $! ; exit 143 ;;
  saved) start; mkdir -p "$N/p/q/r/checkpoint_000001"; echo '{}' > "$N/p/q/r/checkpoint_000001/complete.json"; exit 1 ;;
  exported) start; mkdir -p "$N/p/q/r/m100"; echo '{}' > "$N/p/q/r/m100/artifact.json"; exit 1 ;;
  pretrain) exit 4 ;;
  success) start; exit 0 ;;
esac
