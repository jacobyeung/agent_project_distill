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
    run_dir=$(/usr/bin/python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["run_directory"])' "$HX/k/launch.json")
    mkdir -p "$run_dir"
    printf 'USR1\n' >> "$run_dir/stop.${SLURM_JOB_ID:-local}.request"
    if [[ -n "$admission_child" ]]; then
        kill -USR1 "$admission_child" 2>/dev/null || true
    elif [[ -n "$child" && -n "$X" ]]; then
        /usr/bin/python3 -I "$HX/b/h.py" "$child" "$X/b/i.py" "$X"
    fi
}
trap on_stop USR1
/usr/bin/python3 -B "$HX/b/a.py" "$HX"
[[ ! -e "$stop_file" ]] || exit 75
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
export TK_JOBDIR=/tmp/jjyeung/a_26cc98b7/jobs/${SLURM_JOB_ID:?}.${1:-x}
mkdir -p "$TK_JOBDIR" "$HM/o"
if [[ "${1:-}" == p ]] && ! /usr/bin/python3 -I -c 'import json,sys; sys.exit(0 if json.load(open(sys.argv[1])).get("in_job_admission") else 1)' "$HX/k/launch.json"; then
    export TK_LIGHT=1
else
    unset TK_LIGHT
fi
case "${1:-}" in
    p|c|t|u|x) tk_stage prep ;;
    *) exit 2 ;;
esac
[[ ! -e "$stop_file" ]] || exit 75
tk_bwrap
tk_env
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
tk_persist_small; tk_persist_exports; tk_persist_small
tk_step "exit rc=$rc"
exit "$rc"
