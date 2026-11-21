#!/bin/bash
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID:?}"
trap "exit 143" TERM; sleep 30 & wait $!; exit 0
