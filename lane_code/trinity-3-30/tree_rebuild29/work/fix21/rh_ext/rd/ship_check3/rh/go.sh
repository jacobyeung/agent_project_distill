#!/bin/bash
# Training-start rehearsal for job $A15_JOB (default 174246), run on its node inside
#   srun --overlap --jobid <job> -N1 -n1 timeout -s TERM -k 30 900 bash /tmp/a15_rh_<job>/rh/go.sh
# during the job's review wait. Steps: guards; scratch layout; post-PASS acceptance with a stand-in record
# (not a review); the kit's launch line (t2.py) on four ranks for A15_STEPS (2) optimizer steps, then (A15_SAVE=1,
# the default) the first save in the ranks: one checkpoint and one export through the job's disk guard, each with
# its archive copy, into the scratch sink $RUN/w/sink (sx.py); then one pass of the kit's upload planner (pc.py)
# over that sink with a local session map and writer, in a sandbox without network (up.py, sw.py); GPU samples;
# stop of everything it started, with proof; summary.json. Writes only under /tmp/a15_rh_<job>. The sink holds
# about 270 GB on the real node (state + its archive copy, export + its archive copy) and is NOT cleared.
set -uo pipefail
export TZ=UTC
umask 077
JOB=${A15_JOB:-174246}
D=${A15_D:-/tmp/a15_rh_$JOB}; RH=$D/rh
HARD=${A15_HARD_S:-3600}             # budget from driver start (steps, save, export, archive copies, planner); then its own cleanup (srun timeout 3660 -k 20 is the backstop)
T0=$(date +%s); T_END=$((T0 + HARD))
RUN=$D/run_$(date -u +%Y%m%dT%H%M%SZ); LOG=$RUN/log
mkdir -p "$LOG" && chmod 700 "$D" "$RUN" && ln -sfn "$RUN" "$D/last"
say() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG/go.log"; }
export A15_LOG="$LOG" A15_STEPS=${A15_STEPS:-2}   # A15_RUN reaches only the sandbox (bwrap --setenv), so it marks exactly the rehearsal's processes
export A15_SAVE=${A15_SAVE:-1} A15_SINK="$RUN/w/sink"   # the first save's scratch sink (never cleared by the rehearsal)
PG=''; SMI=''; WATCH=''; PLAN=''; RESULT=unknown
marked() {  # pids of this rehearsal: every process whose environment carries A15_RUN=$RUN (the job's never do)
    local p
    for p in /proc/[0-9]*; do
        [[ -O "$p" ]] || continue
        tr '\0' '\n' 2>/dev/null < "$p/environ" | grep -qx "A15_RUN=$RUN" && echo "${p#/proc/}"
    done
}
cleanup() {
    trap - EXIT TERM INT
    say "cleanup ($1)"
    [[ -n "$WATCH" ]] && kill "$WATCH" 2>/dev/null
    if [[ -n "$PG" ]]; then kill -TERM -- "-$PG" 2>/dev/null; fi
    if [[ -n "$PLAN" ]]; then kill -TERM -- "-$PLAN" 2>/dev/null; fi
    local left; left=$(marked | tr '\n' ' ')
    if [[ -n "$left" ]]; then say "TERM to marked pids: $left"; kill -TERM $left 2>/dev/null; sleep 10; fi
    left=$(marked | tr '\n' ' ')
    if [[ -n "$left" ]]; then say "KILL to marked pids: $left"; kill -KILL $left 2>/dev/null; sleep 3; fi
    sleep 4
    [[ -n "$SMI" ]] && kill "$SMI" 2>/dev/null
    sleep 1
    left=$(marked | tr '\n' ' ')
    say "proof: marked processes left: [${left}]"
    ps -u "$(id -u)" -o pid=,ppid=,etime=,args= --width 220 | awk -v a="$$" -v b="$PPID" '$1 != a && $1 != b' | grep -F "$RUN" | grep -v -e grep -e ' ps ' -e "$RH/stop.sh" >> "$LOG/proof.txt"
    touch "$LOG/proof.txt"; say "proof: ps lines naming the rehearsal: $(grep -c . "$LOG/proof.txt")"
    say "proof: gpus $(nvidia-smi --query-gpu=index,memory.used --format=csv,noheader | tr '\n' ';') apps [$(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader | tr '\n' ';')]"
    /usr/bin/python3 -B -I "$RH/sum.py" "$RUN" "$RESULT" "$T0" > "$LOG/sum.out" 2>&1 && say "summary $RUN/summary.json" || say "summary failed: $(tail -c 600 "$LOG/sum.out")"
    say "end $RESULT, $(( $(date +%s) - T0 )) s"
    exit 0
}
trap 'cleanup exit' EXIT; trap 'RESULT="stopped by TERM (stop.sh or the srun timeout) while: $RESULT"; cleanup TERM' TERM INT
say "start on $(hostname -s) job $JOB run $RUN budget ${HARD}s steps $A15_STEPS save $A15_SAVE sink $A15_SINK"
# the job's own variables, from its running inner shell j.sh (x.py's launch_shell); defaults otherwise
JSH=$(pgrep -u "$(id -u)" -f "^/bin/bash /tmp/q_22c714e1_$JOB/j.sh$" | head -1)
envof() { [[ -n "$JSH" ]] && tr '\0' '\n' < "/proc/$JSH/environ" 2>/dev/null | sed -n "s/^$1=//p" | head -1; }
Q_ROOT=$(envof Q_ROOT); Q_ROOT=${Q_ROOT:-${A15_QROOT:-/tmp/q_22c714e1_$JOB}}
Q_NS=$(envof Q_NS); Q_NS=${Q_NS:-/tmp/q_22c714e1}
Q_KIT=$(envof Q_KIT); Q_KIT=${Q_KIT:-${A15_KIT:-/project/community/jjyeung/okh7/x_22c714e1/n}}
TK_KIT_HOME=$(envof TK_KIT_HOME); TK_KIT_HOME=${TK_KIT_HOME:-$Q_ROOT/h}
TK_JOBDIR=$(envof TK_JOBDIR); TK_JOBDIR=${TK_JOBDIR:-$Q_ROOT/j}
TK_JOB_START=$(envof TK_JOB_START); TK_JOB_START=${TK_JOB_START:-${A15_JOB_START:-}}
if [[ -z "$TK_JOB_START" ]]; then
    TK_JOB_START=$(scontrol show job "$JOB" 2>/dev/null | sed -n 's/.*StartTime=\([^ ]*\).*/\1/p' | head -1)
    TK_JOB_START=$(date -u -d "${TK_JOB_START:-now}" +%s)
fi
say "job shell pid ${JSH:-none}; Q_ROOT=$Q_ROOT Q_NS=$Q_NS Q_KIT=$Q_KIT TK_KIT_HOME=$TK_KIT_HOME TK_JOBDIR=$TK_JOBDIR TK_JOB_START=$TK_JOB_START"
export JOB RUN RH Q_ROOT Q_NS Q_KIT TK_KIT_HOME TK_JOBDIR TK_JOB_START
NROOT=$(/usr/bin/python3 -B -I -c 'import sys; sys.path.insert(0,sys.argv[1]+"/b"); from z import load; print(load(sys.argv[1]+"/k/p.json")["n_root"])' "$Q_KIT")
REVIEW=$NROOT/n_r/review.json; JLIVE=$NROOT/o/$JOB/live
# ---- guards: the real start has not begun and cannot begin unseen
fail() { RESULT="refused: $*"; say "REFUSE: $*"; exit 0; }
started_marks() {  # any of these means the job's own acceptance or training is under way
    local m=''
    [[ -e "$Q_ROOT/t.log" ]] && m+=" t.log"; [[ -e "$Q_ROOT/p/rv.json" ]] && m+=" p/rv.json"
    [[ -e "$REVIEW" ]] && m+=" n_r/review.json"; [[ -e "$JLIVE/REVIEW_ACCEPTED.json" ]] && m+=" REVIEW_ACCEPTED"
    [[ -e "$JLIVE/REVIEW_REFUSED.json" ]] && m+=" REVIEW_REFUSED"; echo "$m"
}
[[ -d "$Q_ROOT" && -f "$Q_ROOT/v.json" && -f "$Q_ROOT/r.json" && -f "$Q_ROOT/p/q/RESULT.json" ]] || fail "job folder incomplete: $Q_ROOT"
[[ -d "$Q_ROOT/p/s" && ! -L "$Q_ROOT/p/s" ]] || fail "p/s is not a real directory"
m=$(started_marks); [[ -z "$m" ]] || fail "the job's own start is under way:$m"
if [[ "${A15_TEST:-0}" != 1 ]]; then
    [[ -f "$JLIVE/WAITING_REVIEW.json" ]] || fail "no WAITING_REVIEW.json in $JLIVE"
    want=$(/usr/bin/python3 -B -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["sha256"])' "$Q_KIT/k/j.json")
    [[ "$(sha256sum < "$Q_ROOT/j.sh" | cut -d' ' -f1)" == "$want" ]] || fail "the job's j.sh is not the kit's inner shell"
    gpu=$(nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits | tr -d ' ')
    say "gpus before: $(echo $gpu | tr ' ' ';') apps [$(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader | tr '\n' ';')]"
    [[ $(echo "$gpu" | grep -c .) == 4 ]] || fail "not four GPUs visible"
    echo "$gpu" | awk -F, '$2 > 1024 {bad=1} END {exit bad}' || fail "a GPU holds more than 1 GiB"
    [[ -z "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader)" ]] || fail "a compute process holds a GPU"
fi
PORT=''
for p in $(seq "${A15_PORT0:-29517}" "$(( ${A15_PORT0:-29517} + 20 ))"); do
    /usr/bin/python3 -B -I -c 'import socket,sys; s=socket.socket(); s.bind(("127.0.0.1",int(sys.argv[1]))); s.close()' "$p" 2>/dev/null && { PORT=$p; break; }
done
[[ -n "$PORT" ]] || fail "no free port"; export A15_PORT=$PORT
say "rendezvous port $PORT (job: --standalone, c10d on localhost:0, an ephemeral port chosen when its own t.py starts)"
# evidence that the job's folder is untouched: names, sizes, mtimes, and the hashes of the files the rehearsal mirrors
snap() { (cd "$Q_ROOT" && ls -lA --time-style=+%s . p p/q 2>/dev/null | awk '{print $1,$5,$6,$7}'; sha256sum v.json r.json p/q/RESULT.json 2>/dev/null) > "$1"; }
snap "$LOG/job_before.txt"
# ---- layout
cp -p "$Q_ROOT/v.json" "$RUN/v.json.orig"
source "$RH/L.sh" || fail "sandbox build failed"
cp -p "$Q_ROOT/v.json" "$W/top/v.json"
mkdir -p "$A15_SINK" "$RUN/pc"
printf '%s\n' "${BW[@]}" > "$LOG/bwrap_args.txt"
say "sandbox: $(grep -c . "$LOG/bwrap_args.txt") args; job folder read-only at $Q_ROOT, $Q_NS, $Q_NJ; scratch upper $W"
env | grep -E '^(Q_|TK_|R1_|C1_|PYTHONPATH|OMP|HF_|TMPDIR|XDG|TORCH|TRITON|CUDA|PATH|A15_)' | sort > "$LOG/env.txt"
# ---- acceptance stand-in, as j.sh runs rv.py (8 threads, nice, no device)
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
CUDA_VISIBLE_DEVICES='' "${BW[@]}" nice -n 10 "$PILOT_VENV/bin/python" -B -s "$RH/accept.py" "$Q_NS" "$Q_NS/v.json" > "$LOG/accept.log" 2>&1
rc=$?; say "acceptance stand-in rc=$rc: $(tail -c 700 "$LOG/accept.log")"
[[ $rc == 0 ]] || { RESULT="failed: acceptance stand-in rc=$rc"; exit 0; }
m=$(started_marks); [[ -z "$m" ]] || fail "the job's own start is under way:$m"
# ---- training start, as j.sh line 439 (8 threads), through t2.py; GPU samples every 2 s
nvidia-smi --query-gpu=timestamp,index,memory.used,utilization.gpu --format=csv,noheader,nounits -lms 2000 > "$LOG/smi.csv" 2>&1 &
SMI=$!; echo "$SMI" > "$LOG/smi.pid"
say "training start (four ranks, $A15_STEPS steps; first save into the sink: $A15_SAVE)"
date +%s > "$LOG/t0"
setsid bash -c 'echo $$ > "$A15_LOG/pgid"; "$@" 2>&1 | tee "$A15_LOG/t.raw.log" | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$A15_LOG/t.log"; echo "${PIPESTATUS[0]}" > "$A15_LOG/t.rc"' \
    bash "${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$RH/t2.py" "$Q_NS/p" "$Q_NS/v.json" &
sleep 1; PG=$(cat "$LOG/pgid" 2>/dev/null)
# ---- watch: end, steps, the job's own start (stop at once), budget
RESULT=running; seen=0; saw=''; guards=0; declare -A PS_DONE PS_WARN
while :; do
    sleep 5
    if [[ -s "$LOG/t.rc" ]]; then RESULT="ended rc=$(cat "$LOG/t.rc")"; say "training ended by itself: rc $(cat "$LOG/t.rc")"; break; fi
    m=$(started_marks); if [[ -n "$m" ]]; then RESULT="stopped: the job's own start began:$m"; say "STOP NOW: $RESULT"; break; fi
    if (( $(date +%s) >= T_END )); then RESULT="stopped: budget ${HARD}s reached"; say "$RESULT"; break; fi
    n=$(cat "$LOG"/ev_rank*.jsonl 2>/dev/null | grep -c '"kind": "STEP"')
    if (( n != seen )); then say "step records $n (of $((4 * A15_STEPS)))"; seen=$n; fi
    if [[ "$A15_SAVE" == 1 ]]; then   # save progress (rank 0's stages) and every disk guard result, once each
        s=$(grep -ho '"stage": "\(save_checkpoint\|persist_checkpoint\|save_export\|persist_export\)"' "$LOG"/ev_rank0.jsonl 2>/dev/null | tr -d '"' | tr '\n' ' ')
        [[ "$s" != "$saw" ]] && { say "save stages (rank 0 begins and ends): $s"; saw=$s; }
        g=$(grep -c '"kind": "DISK_GUARD"' "$LOG"/ev_rank0.jsonl 2>/dev/null); g=${g:-0}
        (( g > guards )) && { say "disk guard: $(grep -h '"kind": "DISK_GUARD"' "$LOG"/ev_rank0.jsonl | tail -n 1 | cut -c1-700)"; guards=$g; }
        for st in persist_checkpoint persist_export; do   # rank 0 archives while ranks 1-3 wait in an NCCL broadcast (timeout 900 s)
            e=$(grep -h "\"kind\": \"END\", \"stage\": \"$st\"" "$LOG"/ev_rank0.jsonl 2>/dev/null | head -1 | sed -n 's/.*"seconds": \([0-9.]*\).*/\1/p')
            if [[ -n "$e" && -z "${PS_DONE[$st]:-}" ]]; then PS_DONE[$st]=1
                v="OK under a 900 s and an 1800 s process-group timeout"
                awk -v x="$e" 'BEGIN{exit !(x > 800)}' && v="DANGER under a 900 s timeout (tree 9d2bbb8a); OK under 1800 s (tree db42866f) only below 1600 s"
                awk -v x="$e" 'BEGIN{exit !(x > 1600)}' && v="DANGER under both the 900 s and the 1800 s timeout"
                say "########## PERSIST_SECONDS $st=$e s on rank 0 ($v) ##########"
            fi
            b=$(grep -h "\"kind\": \"BEGIN\", \"stage\": \"$st\"" "$LOG"/ev_rank0.jsonl 2>/dev/null | head -1 | sed -n 's/.*"t": \([0-9]*\).*/\1/p')
            if [[ -n "$b" && -z "$e" && -z "${PS_WARN[$st]:-}" ]] && (( $(date +%s) - b > 800 )); then PS_WARN[$st]=1
                say "########## PERSIST_SECONDS $st still running after 800 s (DANGER under a 900 s timeout; watch for 1600 s under 1800 s) ##########"; fi
        done
        sd=$(cat "$LOG"/ev_rank*.jsonl 2>/dev/null | grep -c '"kind": "SAVE_DONE"')
        if (( sd >= 4 )) && [[ -z "${DONE_AT:-}" ]]; then DONE_AT=$(date +%s); fi
    elif (( n >= 4 * A15_STEPS )) && [[ -z "${DONE_AT:-}" ]]; then DONE_AT=$(date +%s); fi
    if [[ -n "${DONE_AT:-}" ]] && (( $(date +%s) - DONE_AT > 90 )); then RESULT="stopped: steps done, no exit in 90 s"; say "$RESULT"; break; fi
done
# ---- the kit's upload planner, one pass over the sink, local sessions and writer, no network namespace route
if [[ "$A15_SAVE" == 1 && "$RESULT" == "ended rc=0" ]]; then
    left=$(( T_END - $(date +%s) ))
    if (( left < 60 )); then say "planner skipped: ${left}s of budget left"; else
        say "planner start (kit pc.py Copier pass over $A15_SINK, writer rh/sw.py, --unshare-net, timeout ${left}s)"
        setsid bash -c 'echo $$ > "$A15_LOG/plan.pgid"; "$@" > "$A15_LOG/plan.log" 2>&1; echo $? > "$A15_LOG/plan.rc"' \
            bash timeout -s TERM -k 10 "$left" "${BW[@]}" --unshare-net "$PILOT_VENV/bin/python" -B -I -s "$RH/up.py" "$A15_SINK" "$RUN/pc" "$JOB" &
        sleep 1; PLAN=$(cat "$LOG/plan.pgid" 2>/dev/null)
        while [[ ! -s "$LOG/plan.rc" ]]; do
            sleep 5
            m=$(started_marks); if [[ -n "$m" ]]; then RESULT="stopped during the planner: the job's own start began:$m"; say "STOP NOW: $RESULT"; break; fi
            if (( $(date +%s) >= T_END )); then RESULT="stopped: budget ${HARD}s reached in the planner"; say "$RESULT"; break; fi
        done
        [[ -s "$LOG/plan.rc" ]] && { say "planner rc=$(cat "$LOG/plan.rc"): $(tail -c 1500 "$LOG/plan.log")"; [[ "$(cat "$LOG/plan.rc")" == 0 ]] || RESULT="ended rc=0, planner rc=$(cat "$LOG/plan.rc")"; PLAN=''; }
    fi
fi
say "sink $A15_SINK holds $(du -sb "$A15_SINK" 2>/dev/null | cut -f1) bytes (not cleared by the rehearsal)"
snap "$LOG/job_after.txt"
cmp -s "$LOG/job_before.txt" "$LOG/job_after.txt" && say "job folder top, p, p/q and hashes unchanged" || say "NOTE job folder listing changed (the job itself writes there too): $(diff "$LOG/job_before.txt" "$LOG/job_after.txt" | head -5 | tr '\n' '|')"
exit 0
