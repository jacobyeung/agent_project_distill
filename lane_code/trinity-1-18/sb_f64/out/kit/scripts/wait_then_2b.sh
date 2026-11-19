#!/bin/bash
# Starts the second stage-2 chain after the first one finishes (one dry-run process at a time).
L=/scratch/jjyeung/orch_n30/sb_f64/work/logs
until grep -q ALL_DONE "$L/stage2.done" 2>/dev/null; do sleep 30; done
exec /scratch/jjyeung/orch_n30/sb_f64/work/scripts/run_stage2b.sh "$@"
