#!/bin/bash
#SBATCH -A mt01 -p general -N1 --ntasks=1 -c 32 --mem=800G -t 06:00:00 --no-requeue
#SBATCH -J a15_cot_ap543f18fd
# Job A (CPU): repack the step-544 milestone, then mode p.
# Kit status PREPARATION_ONLY: b/g.py lets mode p alone run. No GPU. No retry inside: any failure ends the job.
set -euo pipefail
export PATH=/usr/local/bin:/usr/bin:/bin
IN=/project/community/jjyeung/okh7/i_bb09a77d
KH=/project/community/jjyeung/okh7/x_7cb63d1e
W=/tmp/jjyeung/d0r_${SLURM_JOB_ID}
mkdir -p /tmp/jjyeung && chmod 700 /tmp/jjyeung && mkdir -p "$W"
step() { printf '%s | %s\n' "$(date -u +%FT%TZ)" "$*" >> "$KH/o/${SLURM_JOB_ID}.a.steps"; }
step "job A start on $(hostname -s); /tmp free $(df -Pk /tmp | awk 'NR==2 {print int($4/1048576)}') GiB"
if [[ ! -f "$IN/m.tar" ]]; then
    /usr/bin/python3 -I "$IN/repack_m544.py" "$IN/M544_SOURCE.json" 04e67f96 "$W" "$IN/m.tar" "$KH/o/${SLURM_JOB_ID}.REPACK.json" q8/69cb3a6a/9ec4a68bf49b.tar \
        > "$KH/o/${SLURM_JOB_ID}.repack.log" 2>&1 || { step "repack failed (no retry)"; exit 3; }
    step "repack done: $(tail -1 "$KH/o/${SLURM_JOB_ID}.repack.log")"
fi
/bin/bash "$KH/b/r.sh" p 0
step "mode p exit 0"
