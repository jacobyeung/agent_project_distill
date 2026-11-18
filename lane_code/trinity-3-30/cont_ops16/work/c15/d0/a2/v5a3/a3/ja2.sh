#!/bin/bash
#SBATCH -A mt01 -p general -N1 --ntasks=1 -c 64 --mem=800G -t 06:00:00 --no-requeue
# CPU job, two stages (the repacked step-544 milestone is reused). Kit status PREPARATION_ONLY: b/g.py lets mode p alone run.
# Stage 1: mode p, then a read-only family census; its status is written to project and to GCS before stage 2 starts.
# Stage 2 (only after stage 1 passed and was published): every rank's first batch through the full forward on CPU (a3/s2.sh), capped at 3 h, four rank processes at once.
# No stage-2 outcome changes stage 1's status or the job's exit code. No GPU. No retry inside.
set -euo pipefail
export PATH=/usr/local/bin:/usr/bin:/bin
IN=/project/community/jjyeung/okh7/i_bb09a77d
KH=/project/community/jjyeung/okh7/x_8417c021
J=${SLURM_JOB_ID:?} T0=$(date +%s) WALL=21600
G=gs://cmu-gpucloud-jjyeung/q8/7c31288e
W=/tmp/jjyeung/w_$J
mkdir -p /tmp/jjyeung && chmod 700 /tmp/jjyeung && mkdir -p "$W"
step() { printf '%s | %s\n' "$(date -u +%FT%TZ)" "$*" >> "$KH/o/$J.a.steps" 2>/dev/null || true; }  # logging never ends the job
gput() {  # one small object; returns the upload's success
    if env CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_FILE_LOGGING=1 CLOUDSDK_CORE_DISABLE_PROMPTS=1 \
        CLOUDSDK_COMPONENT_MANAGER_DISABLE_UPDATE_CHECK=1 CLOUDSDK_CORE_DISABLE_USAGE_REPORTING=1 \
        timeout -k 30 900 gcloud storage cp "$1" "$G/$2" > "$W/$2.gcs.log" 2>&1; then
        step "on GCS: $2 sha256 $(sha256sum < "$1" | cut -c1-16)"; return 0
    fi
    step "GCS upload of $2 failed"; return 1
}
step "job A2 start on $(hostname -s); /tmp free $(df -Pk /tmp | awk 'NR==2 {print int($4/1048576)}') GiB"
[[ -f "$IN/m.tar" ]] || { step "m.tar absent"; exit 3; }   # repacked by job 170050 (42457dbd); vt.py checks its members and stream hash
# Actual archive contents of every new staging entry, before c.sh extracts them (vt.py; sealed k/0.json pinned inside).
/usr/bin/python3 -I "$IN/vt.py" "$KH" /project/community/jjyeung/okh7/x_07ca49df/k/0.json > "$KH/o/$J.vt.json" 2>&1 \
    || { step "staging entry check refused: $(tail -c 300 "$KH/o/$J.vt.json")"; exit 3; }
step "staging entries verified"
# Stage 1
set +e; /bin/bash "$KH/b/r.sh" p 0; rc=$?; set -e
step "mode p exit $rc"
timeout -k 30 1800 /usr/bin/python3 -I "$IN/a3/fam.py" /tmp/jjyeung/okit_8865619b/root/aws/u/ap/bb09a77d/v/rows.sqlite \
    /tmp/jjyeung/okit_8865619b/runs/fdca77e7/inputs > "$KH/o/$J.fam.json" 2>&1 \
    && step "family census written" || step "family census failed"
s1=FAIL; [[ $rc -eq 0 ]] && s1=PASS
# Stage 1 publication: the status file on project, then one GCS object; stage 2 runs only if both succeeded.
pub=0
printf '{"job": "%s", "stage": 1, "status": "%s", "mode_p_rc": %d, "utc": "%s"}\n' "$J" "$s1" "$rc" "$(date -u +%FT%TZ)" > "$KH/o/$J.s1.json" \
    && [[ -s "$KH/o/$J.s1.json" ]] && step "stage 1 status $s1 on project" || { pub=1; step "stage 1 status write to project failed"; }
if timeout -k 30 600 tar cf "$W/${J}a.tar" -C "$KH" --ignore-failed-read o/$J.a.steps o/$J.steps o/$J.err o/$J.vt.json o/$J.fam.json o/$J.s1.json runs 2> "$W/a.tar.log"; then
    gput "$W/${J}a.tar" "${J}a.tar" || pub=1
else
    pub=1; step "stage 1 tar failed"
fi
[[ $rc -eq 0 ]] || exit "$rc"
(( pub == 0 )) || { step "stage 2 not run: stage 1 publication failed"; exit 0; }
# Stage 2
left=$(( T0 + WALL - $(date +%s) - 3000 )); cap=$(( left < 10800 ? left : 10800 ))
if (( cap > 900 )); then
    set +e; /bin/bash "$IN/a3/s2.sh" "$cap"; s2rc=$?; set -e
    step "stage 2 exit $s2rc (cap $cap s)"
    timeout -k 30 900 /usr/bin/python3 -I "$IN/a3/s2sum.py" /tmp/jjyeung/okit_8865619b/runs/fdca77e7/inputs > "$KH/o/$J.s2.json" 2>&1 \
        && step "stage 2 summary written" || step "stage 2 summary failed"
else
    step "stage 2 not run: $cap s left under the wall limit"
fi
timeout -k 30 600 tar cf "$W/${J}b.tar" -C "$KH" --ignore-failed-read o/$J.a.steps o/$J.s2.steps o/$J.s2.json o/$J.s2.r0.log o/$J.s2.r1.log o/$J.s2.r2.log o/$J.s2.r3.log o/$J.s2.final.log runs 2> "$W/b.tar.log" \
    && gput "$W/${J}b.tar" "${J}b.tar" || step "stage 2 tar failed"
exit 0
