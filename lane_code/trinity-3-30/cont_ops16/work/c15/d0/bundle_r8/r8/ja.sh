#!/bin/bash
#SBATCH -A mt01 -p general -N1 --ntasks=1 -c 32 --mem=800G -t 06:00:00 --no-requeue
# Job A (CPU): repack the step-544 milestone, then mode p.
# Kit status PREPARATION_ONLY: b/g.py lets mode p alone run. No GPU. No retry inside: any failure ends the job.
set -euo pipefail
export PATH=/usr/local/bin:/usr/bin:/bin
IN=/project/community/jjyeung/okh7/i_bb09a77d
KH=/project/community/jjyeung/okh7/x_3b862883
W=/tmp/jjyeung/w_${SLURM_JOB_ID}
mkdir -p /tmp/jjyeung && chmod 700 /tmp/jjyeung && mkdir -p "$W"
step() { printf '%s | %s\n' "$(date -u +%FT%TZ)" "$*" >> "$KH/o/${SLURM_JOB_ID}.a.steps"; }
step "job A start on $(hostname -s); /tmp free $(df -Pk /tmp | awk 'NR==2 {print int($4/1048576)}') GiB"
# No reuse: an existing m.tar has no verified receipt in this job, so the job refuses it.
if [[ -e "$IN/m.tar" || -e "$IN/m.tar.partial" ]]; then step "m.tar exists; refusing unverified reuse"; exit 3; fi
/usr/bin/python3 -I "$IN/repack_m544.py" "$IN/M544_SOURCE.json" 93ccadab "$W" "$IN/m.tar" "$KH/o/${SLURM_JOB_ID}.REPACK.json" q8/69cb3a6a/9ec4a68bf49b.tar \
    > "$KH/o/${SLURM_JOB_ID}.repack.log" 2>&1 || { step "repack failed (no retry)"; exit 3; }
step "repack done: $(tail -1 "$KH/o/${SLURM_JOB_ID}.repack.log")"
# Actual archive contents of every new staging entry, before c.sh extracts them (vt.py; sealed k/0.json pinned inside).
/usr/bin/python3 -I "$IN/vt.py" "$KH" /project/community/jjyeung/okh7/x_07ca49df/k/0.json > "$KH/o/${SLURM_JOB_ID}.vt.json" 2>&1 \
    || { step "staging entry check refused: $(tail -c 300 "$KH/o/${SLURM_JOB_ID}.vt.json")"; exit 3; }
step "staging entries verified"
/bin/bash "$KH/b/r.sh" p 0
step "mode p exit 0"
