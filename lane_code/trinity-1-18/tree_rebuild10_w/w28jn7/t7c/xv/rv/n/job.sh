#!/bin/bash
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID:?}"
mkdir -p "$N/p"; echo "{}" > "$N/p/rv.json"; exit 1
