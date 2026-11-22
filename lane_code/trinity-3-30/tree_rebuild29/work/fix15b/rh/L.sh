# Sourced by go.sh. Rebuilds the kit inner shell's (j.sh, kit 7e23bbdd k/j.json 2ca9c9bd, decoded 9f7a02bb) environment and sandbox for the
# training start, lines 12-63, tk_env, tk_pythonpath c, tk_bwrap and the binds of lines 404-410, with three
# differences: (1) the job folder is read-only at all three of its names; (2) every path the job's sandbox
# binds read-write gets a scratch folder under $RUN/w at the same absolute path; (3) the scratch run folder
# and the rehearsal scripts are visible at their own paths. Needs: JOB RUN Q_ROOT Q_NS Q_KIT TK_KIT_HOME
# TK_JOBDIR TK_JOB_START; A15_TEST=1 only for the Trinity test.
W="$RUN/w"
export TMPDIR="$Q_ROOT/tmp" XDG_CACHE_HOME="$Q_ROOT/cache"
export HF_HOME="$Q_ROOT/cache/hf" TORCH_HOME="$Q_ROOT/cache/torch" TRITON_CACHE_DIR="$Q_ROOT/cache/triton"
export CUDA_CACHE_PATH="$Q_ROOT/cache/cu" MPLCONFIGDIR="$Q_ROOT/cache/plot"
export PATH=/usr/local/bin:/usr/bin:/bin
AS=/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung
AL=/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung
K=8865619b
X=$AS/ap/$K
P=/project/community/jjyeung/c7d31ddd
RR=runs/aws128p_20261025
EPOCHS=/home/jjyeung/6d00e578
HX="${TK_KIT_HOME:?}"
S="$Q_ROOT/s"
U=$S/aws/u
HM=$HX
NX="$Q_ROOT/x"
NR="$Q_ROOT/rp"
CUR=$HX/k/0.json
COMMIT=$(/usr/bin/python3 -B -I -c 'import json, sys; print(json.load(open(sys.argv[1]))["commit"])' "$CUR")
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
sha_is() { [[ "$(sha256sum < "$1" | cut -d' ' -f1)" == "$2" ]] || { echo "sha differs: $1"; return 3; }; }
read -r _rf rsha < <(tk_current record)
R1_RUNTIME_RECORD="$P/anyhost/$rsha.json"
# tk_env, verbatim
export R1_OPAQUE_LOGS=1
export Q_E5=6d38613965 R1_MODEL_DIR=a32330d0
export R1_MOUNT="$X" R1_TRAINER="$EPOCHS/$COMMIT" TRAINER="$EPOCHS/$COMMIT" ANYHOST_JOBS="$P/$CLOSURE_DIR"
export R1_RUNTIME_RECORD ANYHOST_NEUTRAL_RUNTIME="$R1_RUNTIME_RECORD"
export PILOT_VENV="$P/venvs/rwtrain_torch211_cu129"
export PATH="$ANYHOST_JOBS/provenance_bin:$PILOT_VENV/bin:/usr/local/bin:/usr/bin:/bin"
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PYTHONPATH="$ANYHOST_JOBS/site_alias"
export Q_E1=1 Q_E2=orchard A_SITE_PROFILE="$X/b/profile.json"
export Q_E3="$X/models"
case "${Q_NS:-}" in /tmp/?*) ;; *) echo E06 >&2; return 1 ;; esac
Q_NJ="/tmp/jjyeung/${Q_NS#/tmp/}"
export Q_E4="{\"/data2\": \"$Q_NJ/p/q/f/$(printf '%s' "$X/data2root" | sha256sum | cut -c1-64)\"}"
export C1_INIT_LOCAL="$P/init"
export HF_HOME="$TK_JOBDIR/cache/hf" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
export OMP_NUM_THREADS=48 MKL_NUM_THREADS=48 OPENBLAS_NUM_THREADS=48 TOKENIZERS_PARALLELISM=false WANDB_DISABLED=true
export Q_E6=1
export TMPDIR="$TK_JOBDIR/tmp"
export XDG_CACHE_HOME="$TK_JOBDIR/cache" TORCH_HOME="$TK_JOBDIR/cache/torch" TRITON_CACHE_DIR="$TK_JOBDIR/cache/triton"
# tk_pythonpath c, verbatim (without its step lines)
export PYTHONPATH="$X/b:$ANYHOST_JOBS:$ANYHOST_JOBS/site_alias"
if tk_has np; then export PYTHONPATH="$S/np226:$PYTHONPATH"; fi
if read -r fla_file fla_sha < <(tk_current fla 2>/dev/null); then
    sha_is "$(hp "$fla_file")" "$fla_sha" || return 3
    export PYTHONPATH="$(dirname "$fla_file")/p:$PYTHONPATH" C1_EXPECT_FLA=1
fi
# scratch folders for every read-write bind of the job's sandbox
mkdir -p "$W/top/p/q/r" "$W/top/j/tmp" "$W/top/cache" "$W/top/tmp" "$W/top/rp" "$W/xo" "$W/xck" "$W/live"
# fix18 test of the in-job remedy: the two raw paths that ranks 1-3 read from the init artifact (the donor run's
# folder under $X/runs, which the job backs with its empty $Q_ROOT/rp) become links to the staged copies rank 0
# authenticates. The job-side equivalent is the same two links under $Q_ROOT/rp/6ed2c7aa/m400 (not made here).
A15_INIT_HEADS=e72208ac55e342a3ac7972383f63740be323eba28d6c3bd293da1ad47743d4a7
if [[ "${A15_INIT_LINKS:-1}" == 1 ]]; then
    mkdir -p "$W/top/rp/6ed2c7aa/m400"
    [[ -L "$W/top/rp/6ed2c7aa/m400/full_weights" ]] || ln -s "$Q_NS/p/q/w" "$W/top/rp/6ed2c7aa/m400/full_weights"
    [[ -L "$W/top/rp/6ed2c7aa/m400/heads.pt" ]] || ln -s "$Q_NS/p/q/u/$A15_INIT_HEADS" "$W/top/rp/6ed2c7aa/m400/heads.pt"
fi
# compose NAME: the job folder at NAME, read-only entry by entry, inside the scratch folder $W/top; the
# entries training or the post-PASS steps write (v.json, p/rv.json, p/pr.json, p/q/r, j, cache, tmp, rp)
# are scratch. Symlinks are recreated as symlinks; nothing is bound over a symlink.
A15_SKIP_TOP=" v.json p j cache tmp rp "
A15_SKIP_P=" q rv.json pr.json "
A15_SKIP_Q=" r "
compose() {
    local name="$1" level src dest skip e n
    BW+=(--bind "$W/top" "$name")
    for level in top p q; do
        case $level in
            top) src="$Q_ROOT"; dest="$name"; skip="$A15_SKIP_TOP" ;;
            p) src="$Q_ROOT/p"; dest="$name/p"; skip="$A15_SKIP_P" ;;
            q) src="$Q_ROOT/p/q"; dest="$name/p/q"; skip="$A15_SKIP_Q" ;;
        esac
        for e in "$src"/* "$src"/.[!.]*; do
            [[ -e "$e" || -L "$e" ]] || continue
            n=${e##*/}
            [[ "$skip" == *" $n "* ]] && continue
            if [[ -L "$e" ]]; then
                local w="$W/top${dest#"$name"}/$n"
                [[ -L "$w" ]] || ln -sfn "$(readlink "$e")" "$w"
            else
                BW+=(--ro-bind "$e" "$dest/$n")
            fi
        done
    done
}
# tk_bwrap, with the read-write binds replaced
read -r bw bwsha < <(tk_current bwrap)
[[ -x "$bw" ]] && sha_is "$bw" "$bwsha" || { echo "sandbox binary check failed"; return 3; }
BW=("$bw")
for entry in /* /.[!.]* /..?*; do
    case "$entry" in /home|/dev|/proc) continue ;; esac
    if [[ "${A15_TEST:-0}" == 1 ]]; then case "$entry" in /scratch|/project|/lustre) continue ;; esac; fi
    [[ -e "$entry" || -L "$entry" ]] || continue
    if [[ -L "$entry" ]]; then BW+=(--symlink "$(readlink "$entry")" "$entry"); else BW+=(--ro-bind "$entry" "$entry"); fi
done
BW+=(--tmpfs /tmp)
compose "$Q_ROOT"
BW+=(--dev-bind /dev /dev --proc /proc
    --tmpfs /home --dir /home/jjyeung
    --ro-bind "$U" "$AS"
    --ro-bind "$U" "$AL"
    --ro-bind "$NX" "$X"
    --bind "$W/xo" "$X/o"
    --bind "$W/xck" "$X/ck"
    --bind "$W/top/rp" "$X/runs"
    --ro-bind "$U/ap/$K/u" "$X/u"
    --ro-bind "$S/c7d31ddd/data2root" "$X/data2root"
    --ro-bind "$S/c7d31ddd/$RR/models" "$X/models"
    --ro-bind "$S/c7d31ddd" "$P"
    --ro-bind "$S/epochs" "$EPOCHS"
    --bind "$W/top/j" "$TK_JOBDIR"
    --remount-ro /home
    --unshare-user --uid "$(id -u)" --gid "$(id -g)")
compose "$Q_NS"
compose "$Q_NJ"
BW+=(--setenv TK_JOB_START "${TK_JOB_START:?}")
# the live folder (rv.py --live: n_root/o/<job>/live) gets a scratch folder; nothing is created on the host
Q_LIVE="$(/usr/bin/python3 -B -I -c 'import json,sys; sys.path.insert(0,sys.argv[1]+"/b"); from z import load; print(load(sys.argv[1]+"/k/p.json")["n_root"])' "$Q_KIT")/o/$JOB/live"
if [[ -d "$Q_LIVE" || "${A15_TEST:-0}" == 1 ]]; then BW+=(--bind "$W/live" "$Q_LIVE"); else echo "live folder absent: $Q_LIVE"; return 3; fi
BW+=(--bind "$RUN" "$RUN" --ro-bind "$RH" "$RH")
if [[ "${A15_TEST:-0}" == 1 ]]; then
    for e in ${A15_TEST_BINDS:-}; do BW+=(--ro-bind "$e" "$e"); done
fi
export PATH="$(dirname "${BW[0]}"):$PATH"
# The values above are the sandbox's; hand them to bwrap and give the host-side driver its own scratch
# values, so that no host command of the rehearsal can write into the job folder through them.
for v in TMPDIR XDG_CACHE_HOME HF_HOME TORCH_HOME TRITON_CACHE_DIR CUDA_CACHE_PATH MPLCONFIGDIR PATH PYTHONPATH; do BW+=(--setenv "$v" "${!v}"); done
BW+=(--setenv A15_RUN "$RUN")
mkdir -p "$RUN/htmp"
export TMPDIR="$RUN/htmp" XDG_CACHE_HOME="$RUN/htmp" HF_HOME="$RUN/htmp" TORCH_HOME="$RUN/htmp" TRITON_CACHE_DIR="$RUN/htmp" CUDA_CACHE_PATH="$RUN/htmp" MPLCONFIGDIR="$RUN/htmp" PATH=/usr/local/bin:/usr/bin:/bin
unset PYTHONPATH
# Safety check: every writable bind of this sandbox comes from the scratch run folder (or is /dev).
for ((i = 1; i < ${#BW[@]}; i++)); do
    case "${BW[$i]}" in
        --bind|--bind-try|--dev-bind|--dev-bind-try)
            src="${BW[$((i + 1))]}"
            [[ "$src" == "$RUN" || "$src" == "$RUN"/* || "$src" == /dev ]] || { echo "writable bind from outside the scratch run folder: $src"; return 3; } ;;
    esac
done
