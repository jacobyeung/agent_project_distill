#!/bin/bash
N="${SLURM_TMPDIR}/q_22c714e1_${SLURM_JOB_ID}"
finish() { printf '%s
' "$1" > "$N/child.trap"; echo child-final; exit 17; }
trap 'finish TERM' TERM
trap 'finish USR1' USR1
printf ready > "$N/ready"
while true; do sleep .1; done
