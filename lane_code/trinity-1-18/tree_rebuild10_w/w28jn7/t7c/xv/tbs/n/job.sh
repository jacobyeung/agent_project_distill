#!/bin/bash
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID:?}"
printf "=== t pid=1 where=admit RuntimeError\nTraceback (most recent call last):\n  RuntimeError: No CUDA GPUs are available\n\n" > "$N/tb.txt"; exit 1
