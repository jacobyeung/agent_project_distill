#!/bin/bash
trap 'echo child_TERM; printf TERM > "$SLURM_TMPDIR/caught"; exit 7' TERM
trap 'echo child_USR1; printf USR1 > "$SLURM_TMPDIR/caught"; exit 9' USR1
printf ready > "$SLURM_TMPDIR/ready"
while true; do sleep .1; done
