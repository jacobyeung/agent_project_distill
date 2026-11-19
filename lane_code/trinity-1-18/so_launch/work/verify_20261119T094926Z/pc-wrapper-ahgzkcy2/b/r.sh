#!/bin/bash
# Orchard single-node entry: r.sh MODE ARM   (MODE p=prepare, c=first-batch check on one GPU, t=train, u=resume)
set -euo pipefail
export PATH=/usr/local/bin:/usr/bin:/bin
export TK_JOB_START="${TK_JOB_START:-$(date +%s)}"
for key in $(compgen -e); do
    case "$key" in *_API_KEY|*_SECRET*|*_TOKEN|*_CREDENTIAL*|CLOUDSDK_*) unset "$key" ;; esac
done
HX="$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")"
export TK_KIT_HOME="$HX"
child="" admission_child="" X=""
stop_file="$HX/o/${SLURM_JOB_ID:-local}.stop"
on_stop() {
    printf 'USR1\n' >> "$stop_file"
    # The sandbox kit is a separate staging directory. Publish the same request there.
    if [[ -n "${NX:-}" && -d "$NX/o" ]]; then
        printf 'USR1\n' >> "$NX/o/${SLURM_JOB_ID:-local}.stop"
    fi
    if [[ -n "$admission_child" ]]; then
        kill -USR1 "$admission_child" 2>/dev/null || true
    elif [[ -n "$child" && -n "$X" ]]; then
        /usr/bin/python3 -I "$HX/b/h.py" "$child" "$X/b/i.py" "$X"
    fi
}
trap on_stop USR1
/usr/bin/python3 -B "$HX/b/a.py" "$HX"
[[ ! -e "$stop_file" ]] || exit 75
if [[ "${TK_PREPARED_INPUT_CACHE:-0}" == 1 && "${1:-}" =~ ^[ptu]$ ]]; then
    pc_run=$(/usr/bin/python3 -I -c 'import json,pathlib,sys; print(pathlib.Path(json.load(open(sys.argv[1]))["run_directory"]))' "$HX/k/launch.json")
    pc_lock="$(dirname "$pc_run")/.prepare-locks/$(basename "$pc_run").lock"
    mkdir -p "$(dirname "$pc_lock")"
    # Hold this through training as well as preparation. The recursive p leg
    # inherits the same open file description, so it must not reopen the lock.
    if [[ "${TK_PC_LOCK_HELD:-0}" != "$PPID" ]]; then
        exec 7>"$pc_lock"
        flock -w 600 7 || exit 75
        export TK_PC_LOCK_HELD="$$"
    fi
fi
if [[ "${1:-}" == t || "${1:-}" == u ]] && /usr/bin/python3 -I -c 'import json,sys; sys.exit(0 if json.load(open(sys.argv[1])).get("in_job_admission") else 1)' "$HX/k/launch.json"; then
    /bin/bash "$HX/b/r.sh" p "${2:?}" &
    admission_child=$!
    while true; do
        set +e; wait "$admission_child"; admission_rc=$?; set -e
        if kill -0 "$admission_child" 2>/dev/null; then continue; fi
        break
    done
    admission_child=""
    [[ "$admission_rc" -eq 0 ]] || exit "$admission_rc"
fi
[[ ! -e "$stop_file" ]] || exit 75
/usr/bin/python3 -I "$HX/b/g.py" "$HX" "${1:?}"
export TK_RUNS_DIR="$(/usr/bin/python3 -I -c 'import json,pathlib,sys; print(pathlib.Path(json.load(open(sys.argv[1]))["run_directory"]).parent)' "$HX/k/launch.json")"
source "$HX/b/c.sh"
export TK_JOBDIR=/scratch/jjyeung/orch_n30/so_launch/work/verify_20261119T094926Z/pc-wrapper-ahgzkcy2/tmp/okit_$K/jobs/${SLURM_JOB_ID:?}.${1:-x}
mkdir -p "$TK_JOBDIR" "$HM/o"
if [[ "${1:-}" == p ]] && ! /usr/bin/python3 -I -c 'import json,sys; sys.exit(0 if json.load(open(sys.argv[1])).get("in_job_admission") else 1)' "$HX/k/launch.json"; then
    export TK_LIGHT=1
else
    unset TK_LIGHT
fi
TK_PC_PREPARE=0
if [[ "${TK_PREPARED_INPUT_CACHE:-0}" == 1 && "${1:-}" == p && -z "${TK_LIGHT:-}" ]]; then
    : "${TK_PREPARED_CACHE_ROOT:?set an absolute pool cache directory}"
    [[ "$TK_PREPARED_CACHE_ROOT" == /* ]] || exit 2
    TK_PC_PREPARE=1
fi
case "${1:-}" in
    p|c|t|u|x) tk_stage prep ;;
    *) exit 2 ;;
esac
[[ ! -e "$stop_file" ]] || exit 75
if [[ "$TK_PC_PREPARE" == 1 && "${TK_PC_HIT:-0}" == 1 ]]; then
    tk_step "prepared input cache verified; CPU admission phases reused"
    exit 0
fi
tk_bwrap
tk_env
# Use a path visible through the shared kit bind, not the host-only kit path.
export K3="$X/o/${SLURM_JOB_ID:-local}.stop"
export R1_STOP_FILE="$K3"
if [[ "${1:-}" == p || "${1:-}" == c ]]; then
    threads="${SLURM_CPUS_PER_TASK:-8}"
    if [[ "$threads" -gt 16 ]]; then threads=16; fi
    export OMP_NUM_THREADS="$threads" MKL_NUM_THREADS="$threads" OPENBLAS_NUM_THREADS="$threads"
fi
if [[ "${1:-}" == p ]]; then export CUDA_VISIBLE_DEVICES="" STUDENT_IO_THREADS=16; fi
case "${1:-}" in
    c|t|u)
        export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True TORCH_NCCL_AVOID_RECORD_STREAMS=1
        ;;
esac
case "${1:-}" in
    t|u) export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 OMP_WAIT_POLICY=PASSIVE ;;
esac
tk_pythonpath "${1:?}"
tk_step "launch $* on $(hostname -s) gpus=${SLURM_GPUS_ON_NODE:-0}"
( while sleep 600; do tk_persist_small; tk_persist_exports; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader >> "$HM/o/${SLURM_JOB_ID}.gpu" 2>/dev/null || true; done ) &
persister=$!
# bwrap ignores USR1 (Slurm signals every process of the step); i.py installs its own relay handler.
/usr/bin/python3 -I -c 'import os, signal, sys; signal.signal(signal.SIGUSR1, signal.SIG_IGN); os.execvp(sys.argv[1], sys.argv[1:])' \
    "${BW[@]}" "$PILOT_VENV/bin/python" -B "$X/b/i.py" "$X" "$@" &
child=$!
[[ ! -e "$stop_file" ]] || on_stop
while true; do
    set +e; wait "$child"; rc=$?; set -e
    if kill -0 "$child" 2>/dev/null; then continue; fi
    break
done
kill "$persister" 2>/dev/null || true
if [[ "$rc" == 0 && "$TK_PC_PREPARE" == 1 && "${TK_PC_HIT:-0}" != 1 ]]; then
    if /usr/bin/python3 -I "$HX/b/pc.py" seal "$HX" "$S" "$TK_PREPARED_CACHE_ROOT" "$SLURM_JOB_ID"; then
        tk_step "prepared input cache published; receipt $HM/o/$SLURM_JOB_ID.prepared-cache.json"
    else
        tk_step "prepared input cache publication refused; preparation remains usable"
    fi
fi
tk_persist_small; tk_persist_exports; tk_persist_small
tk_step "exit rc=$rc"
exit "$rc"
