#!/bin/bash
#SBATCH -A mt01 -p general -N1 --ntasks=1 -c 32 --mem=800G -t 06:00:00 --no-requeue
# CPU job: mode p on the derived kit, then a read-only family census (the repacked step-544 milestone is reused).
# Kit status PREPARATION_ONLY: b/g.py lets mode p alone run. No GPU. No retry inside: any failure ends the job.
set -euo pipefail
export PATH=/usr/local/bin:/usr/bin:/bin
IN=/project/community/jjyeung/okh7/i_bb09a77d
KH=/project/community/jjyeung/okh7/x_8417c021
W=/tmp/jjyeung/w_${SLURM_JOB_ID}
mkdir -p /tmp/jjyeung && chmod 700 /tmp/jjyeung && mkdir -p "$W"
step() { printf '%s | %s\n' "$(date -u +%FT%TZ)" "$*" >> "$KH/o/${SLURM_JOB_ID}.a.steps"; }
step "job A start on $(hostname -s); /tmp free $(df -Pk /tmp | awk 'NR==2 {print int($4/1048576)}') GiB"
[[ -f "$IN/m.tar" ]] || { step "m.tar absent"; exit 3; }   # repacked by job 170050 (42457dbd); vt.py checks its members and stream hash
# Actual archive contents of every new staging entry, before c.sh extracts them (vt.py; sealed k/0.json pinned inside).
/usr/bin/python3 -I "$IN/vt.py" "$KH" /project/community/jjyeung/okh7/x_07ca49df/k/0.json > "$KH/o/${SLURM_JOB_ID}.vt.json" 2>&1 \
    || { step "staging entry check refused: $(tail -c 300 "$KH/o/${SLURM_JOB_ID}.vt.json")"; exit 3; }
step "staging entries verified"
set +e; /bin/bash "$KH/b/r.sh" p 0; rc=$?; set -e
step "mode p exit $rc"
# Read-only census of the admitted rows by family (node-local prepared databases of this run), whatever mode p's outcome.
/usr/bin/python3 -I "$IN/a2/fam.py" /tmp/jjyeung/okit_8865619b/runs/fdca77e7/inputs > "$KH/o/${SLURM_JOB_ID}.fam.json" 2>&1 \
    && step "family census written" || step "family census failed"
exit $rc
