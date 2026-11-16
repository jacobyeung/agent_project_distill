#!/usr/bin/env bash
#SBATCH -A mt01
#SBATCH -p advanced
#SBATCH -N 1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:4
#SBATCH --cpus-per-task=64
#SBATCH --mem=600G
#SBATCH --time=24:00:00
#SBATCH --no-requeue
#SBATCH --signal=B:TERM@120
#SBATCH -o /project/community/jjyeung/official_reads/logs/%x_%j.out
# Official reads on Orchard advanced, one packed 4-GPU job, one eval worker per GPU (lane official_reads).
# Runs the phases of PLAN (JSON list) in order with the official harness official/run_eval_hc.py of the P1 evaluator tree
# (p1_rt/reads/in/r.tar, sha 31fcfc3b): prompt ours, thinking on, 8192 cap, 32 frames, headcall own, scored by its
# official/score_and_aggregate.py (0bb536ca). Every item is flushed as it finishes; a phase with a DONE.json is skipped.
# Resumable stop: touch /project/community/jjyeung/official_reads/STOP (or scancel): workers stop, partial lines are
# trimmed on the next start, and resubmitting the same PLAN finishes only the missing items.
# usage: sbatch -J jjy_or_<tag> or_job.sh PLAN.json          dry check on the login node: OR_DRY=1 bash or_job.sh PLAN.json
set -euo pipefail
export PATH=/usr/local/bin:/usr/bin:/bin
START=$(date +%s)
PLAN="${1:?plan json}"
J=/project/community/jjyeung
O=$J/official_reads; K=$J/p1_rt; KC=$J/cp4tk_rt
Q=$J/q7e/stage/distill; E=$J/cp4tk_eval
P=$J/distill; RR=runs/aws128p_20261025
S=/tmp/jjy_tke/root            # shared node-local overlay (same stamps and lock as cp4tk_eval / p1 reads jobs)
PE=data2root/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/eval_instructed_provisional_e3e9ffb/artifacts/paper_eval
step() { printf '%s | %s\n' "$(date -u +%FT%TZ)" "$*"; }
[[ -f "$PLAN" ]] || { echo "plan $PLAN not found"; exit 2; }
if [[ "${OR_DRY:-0}" == 1 ]]; then
    exec python3 -I "$O/bin/or_drv.py" dry --plan "$PLAN"
fi
[[ ! -f "$O/STOP" ]] || { step "$O/STOP exists: not starting (remove it to run)"; exit 3; }
NG=$(tr ',' '\n' <<< "${CUDA_VISIBLE_DEVICES:-}" | grep -c . || true)
[[ "$NG" == 4 ]] || { step "need exactly 4 GPUs (CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-})"; exit 2; }
JD=/tmp/jjy_or/jd_${SLURM_JOB_ID:-nojob}
export HOME=$JD/home TMPDIR=$JD/tmp XDG_CACHE_HOME=$JD/cache/xdg PIP_CACHE_DIR=$JD/cache/pip TRITON_CACHE_DIR=$JD/cache/triton \
       TORCH_HOME=$JD/cache/torch HF_HOME=$JD/cache/hf PYTHONDONTWRITEBYTECODE=1
mkdir -p "$HOME" "$TMPDIR" "$XDG_CACHE_HOME" /tmp/jjy_tke "$S/.stamp" "$O/logs"
step "job=${SLURM_JOB_ID:-} host=$(hostname) plan=$PLAN gpus=$CUDA_VISIBLE_DEVICES"
nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv,noheader || true
free=$(df -Pk /tmp | awk 'NR==2 {print int($4 / 1048576)}')
step "/tmp free ${free} GiB"
(( free >= 120 )) || { step "need >= 120 GiB free on /tmp (venv 8 + model 19 + milestone 20 + media)"; exit 4; }
cp "$K/kit/CURRENT.json" "$JD/CURRENT.json"
cur() { python3 -I -c 'import json, sys; e = json.load(open(sys.argv[1]))[sys.argv[2]]; print(e["file"], e["sha256"])' "$JD/CURRENT.json" "$1"; }
kitx_once() {  # FILE SHA DEST: extract a sha-checked tar once per (node, sha) (cp4tk_eval tke_common.sh semantics)
    local file="$1" sha="$2" dest="$3"
    [[ -f "$S/.stamp/$sha" && -d "$dest" ]] && return 0
    [[ -e "$dest" ]] && mv "$dest" "$dest.old.$(date +%s)"
    mkdir -p "$(dirname "$dest")" "$S/.stamp"
    python3 -I "$KC/bin/kitx.py" "$file" "$sha" "$dest"
    touch "$S/.stamp/$sha"
}
exec 8>/tmp/jjy_tke/stage.lock; flock 8
read -r f s < <(cur venv);  kitx_once "$K/kit/$f" "$s" "$S/distill/venvs"
read -r f s < <(cur model); kitx_once "$K/kit/$f" "$s" "$S/distill/$RR/models"
if grep -q '"f17"' "$PLAN"; then
    read -r f s < <(cur f17); [[ "$f" == /* ]] || f="$K/in/$f"
    if [[ ! -f "$S/.stamp/f17.$s" || ! -d "$S/distill/$RR/r1d_8d19426a" ]]; then
        [[ -e "$S/distill/$RR/r1d_8d19426a.x" ]] && mv "$S/distill/$RR/r1d_8d19426a.x" "$S/distill/$RR/r1d_8d19426a.x.old.$(date +%s)"
        python3 -I "$KC/bin/kitx.py" "$f" "$s" "$S/distill/$RR/r1d_8d19426a.x"
        mv "$S/distill/$RR/r1d_8d19426a.x/r1d_8d19426a" "$S/distill/$RR/r1d_8d19426a"
        touch "$S/.stamp/f17.$s"
    fi
fi
[[ -f "$Q/../STAGE_OK" ]] || { step "q7 NFS stage missing (purged?): restore it before reading"; exit 3; }
python3 -I "$K/reads/bin/tk_eval_stage.py" "$Q" "$S/distill" "$PE/vstibench_repr450_v3" data2root/jjyeung/agent_project_data/vsibench_videos
python3 -I "$K/reads/bin/tk_eval_stage.py" "$E/inputs" "$S/distill" data2root
flock -u 8
step "kit staged ($(( $(date +%s) - START )) s)"
BW=("$K/kit/bwrap" --dev-bind / / --bind "$S/distill" "$P" --unshare-user --uid "$(id -u)" --gid "$(id -g)")
rc=0
"${BW[@]}" /usr/bin/python3 -I -u "$O/bin/or_drv.py" run --plan "$PLAN" & DRV=$!
trap 'step "TERM received: stopping driver"; kill -TERM $DRV 2>/dev/null || true' TERM
wait $DRV || rc=$?
[[ $rc -ge 128 ]] && { wait $DRV || rc=$?; }
step "driver exit $rc"
echo "JOB_END rc=$rc $(date -u +%FT%TZ)"
exit "$rc"
