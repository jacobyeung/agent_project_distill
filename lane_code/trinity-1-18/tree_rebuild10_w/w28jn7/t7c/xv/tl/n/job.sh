#!/bin/bash
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID:?}"
: > "$N/t.log"; exit 1
