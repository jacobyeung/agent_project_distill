#!/bin/bash
# Rebuilds the job shell's sandbox with the job directory mounted read-only and a scratch
# folder read-write, then runs one command in it. usage: L.sh <python args...> | L.sh --sh <cmd...>
set -uo pipefail
umask 077
D=/tmp/a15_dbg_174134
export Q_ROOT=/tmp/q_22c714e1_174134 Q_NS=/tmp/q_22c714e1 Q_KIT=/project/community/jjyeung/okh7/x_22c714e1/n
export TK_KIT_HOME=$Q_ROOT/h TK_JOBDIR=$D/tr/j SLURM_JOB_ID=174134 PYTHONDONTWRITEBYTECODE=1
export TK_JOB_START=$(date +%s)
LIVE=/project/community/jjyeung/okh7/x_22c714e1/o/174134/live
mkdir -p "$D/tr/j" "$D/tr/rp" "$D/tr/live" "$D/tr/log"
cd "$D/tr"
export PATH=/usr/local/bin:/usr/bin:/bin
AS=/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung
AL=/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung
K=8865619b
X=$AS/ap/$K
HX="$TK_KIT_HOME"
P=/project/community/jjyeung/c7d31ddd
RR=runs/aws128p_20261025
EPOCHS=/home/jjyeung/6d00e578
S="$Q_ROOT/s"
U=$S/aws/u
NX="$Q_ROOT/x"
CUR=$HX/k/0.json
COMMIT=$(/usr/bin/python3 -B -I -c 'import json, sys; print(json.load(open(sys.argv[1]))["commit"])' "$CUR")
tk_step() { echo "$(date -u +%FT%TZ) | $*"; }
hp() {
    case "$1" in
        "$X"/*) printf '%s\n' "$NX/${1#"$X"/}" ;;
        "$AS"/*) printf '%s\n' "$U/${1#"$AS"/}" ;;
        "$AL"/*) printf '%s\n' "$U/${1#"$AL"/}" ;;
        *) printf '%s\n' "$1" ;;
    esac
}
tk_current() { /usr/bin/python3 -B -I -c 'import json, sys; e = json.load(open(sys.argv[1]))[sys.argv[2]]; print(e["file"], e["sha256"])' "$CUR" "$1"; }
tk_has() { /usr/bin/python3 -B -I -c 'import json,sys; sys.exit(0 if sys.argv[2] in json.load(open(sys.argv[1])) else 1)' "$CUR" "$1"; }
CLOSURE_DIR="_jobs/cp4tk_$(tk_current closure | cut -d' ' -f2 | cut -c1-12)"
sha_is() { [[ "$(sha256sum < "$1" | cut -d' ' -f1)" == "$2" ]] || { tk_step "sha differs: $1"; return 3; }; }
read -r rfile rsha < <(tk_current record)
R1_RUNTIME_RECORD="$P/anyhost/$rsha.json"
# environment of the job shell (its tk_env), with the job folder variable in scratch
export R1_OPAQUE_LOGS=1
export Q_E5=6d38613965 R1_MODEL_DIR=a32330d0
export R1_MOUNT="$X" R1_TRAINER="$EPOCHS/$COMMIT" TRAINER="$EPOCHS/$COMMIT" ANYHOST_JOBS="$P/$CLOSURE_DIR"
export R1_RUNTIME_RECORD ANYHOST_NEUTRAL_RUNTIME="$R1_RUNTIME_RECORD"
export PILOT_VENV="$P/venvs/rwtrain_torch211_cu129"
export PATH="$ANYHOST_JOBS/provenance_bin:$PILOT_VENV/bin:/usr/local/bin:/usr/bin:/bin"
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PYTHONPATH="$ANYHOST_JOBS/site_alias"
export Q_E1=1 Q_E2=orchard A_SITE_PROFILE="$X/b/profile.json"
export Q_E3="$X/models"
export Q_E4="{\"/data2\": \"$X/data2root\"}"
export C1_INIT_LOCAL="$P/init"
export HF_HOME="$TK_JOBDIR/cache/hf" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
export OMP_NUM_THREADS=${A15_THREADS:-48} MKL_NUM_THREADS=${A15_THREADS:-48} OPENBLAS_NUM_THREADS=${A15_THREADS:-48} TOKENIZERS_PARALLELISM=false WANDB_DISABLED=true
export Q_E6=1
export TMPDIR="$TK_JOBDIR/tmp"
export XDG_CACHE_HOME="$TK_JOBDIR/cache" TORCH_HOME="$TK_JOBDIR/cache/torch" TRITON_CACHE_DIR="$TK_JOBDIR/cache/triton"
export CUDA_CACHE_PATH="$TK_JOBDIR/cache/cu" MPLCONFIGDIR="$TK_JOBDIR/cache/plot"
mkdir -p "$TMPDIR"
# python path of the job shell (its tk_pythonpath c)
export PYTHONPATH="$X/b:$ANYHOST_JOBS:$ANYHOST_JOBS/site_alias"
if tk_has np; then export PYTHONPATH="$S/np226:$PYTHONPATH"; fi
if read -r fla_file fla_sha < <(tk_current fla 2>/dev/null); then
    sha_is "$(hp "$fla_file")" "$fla_sha" || exit 3
    export PYTHONPATH="$(dirname "$fla_file")/p:$PYTHONPATH" C1_EXPECT_FLA=1
fi
# sandbox of the job shell (its tk_bwrap); differences: job directory read-only at both of its
# names, scratch read-write, scratch folders in place of the run folder and of the live folder
read -r bw sha < <(tk_current bwrap)
[[ -x "$bw" ]] && sha_is "$bw" "$sha" || { echo "sandbox binary check failed"; exit 3; }
BW=("$bw")
for entry in /* /.[!.]* /..?*; do
    case "$entry" in /home|/dev|/proc) continue ;; esac
    [[ -e "$entry" || -L "$entry" ]] || continue
    if [[ -L "$entry" ]]; then BW+=(--symlink "$(readlink "$entry")" "$entry"); else BW+=(--ro-bind "$entry" "$entry"); fi
done
BW+=(--tmpfs /tmp --ro-bind "$Q_ROOT" "$Q_ROOT" --bind "$D" "$D" --dev-bind /dev /dev --proc /proc
    --tmpfs /home --dir /home/jjyeung
    --ro-bind "$U" "$AS"
    --ro-bind "$U" "$AL"
    --ro-bind "$NX" "$X"
    --bind "$D/tr/rp" "$X/runs"
    --ro-bind "$U/ap/$K/u" "$X/u"
    --ro-bind "$S/c7d31ddd/data2root" "$X/data2root"
    --ro-bind "$S/c7d31ddd/$RR/models" "$X/models"
    --ro-bind "$S/c7d31ddd" "$P"
    --ro-bind "$S/epochs" "$EPOCHS"
    --remount-ro /home
    --unshare-user --uid "$(id -u)" --gid "$(id -g)"
    --ro-bind "$Q_ROOT" "$Q_NS" --setenv TK_JOB_START "$TK_JOB_START")
SLIVE="${A15_LIVE:-$D/tr/live}"; mkdir -p "$SLIVE"
if [[ -d "$LIVE" ]]; then BW+=(--bind "$SLIVE" "$LIVE"); fi
export PATH="$(dirname "${BW[0]}"):$PATH"
if [[ "${1:-}" == --sh ]]; then shift; exec "${BW[@]}" "$@"; fi
exec "${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$@"
