set -euo pipefail
C=${1:?cache}
MODEL=${2:?model}
BUNDLE=${3:?bundle}
BSHA=${4:?bundle_sha256}
case "$MODEL" in cp1m200|f17) ;; *) exit 2;; esac
[[ "$BSHA" =~ ^[0-9a-f]{64}$ ]] || exit 2
C2=${C2:-/project/community/jjyeung/bd8ae51c}
JID=${SLURM_JOB_ID:?Requires a Slurm allocation}
S=/tmp/jjyeung/ocam_$JID
O=$C2/o/$JID
L=/scratch/jjyeung/orch_cd/evalx/work/camera
PC=$S/sj/orch_cd/evalx/work/camera
AP=/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap
FSWU=/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung
PY=/scratch/jjyeung/envs/p1cpu/bin/python
VPY=$AP/19252904/e/bin/python
RUN=$L/run
PR=$PC/run
ATT=camera_${MODEL}_${JID}
CHILD=
SAVE_SLOT=0
SAVE_FAILED=0
MIN_PROJECT_FREE_BYTES=214748364800
test ! -e "$S"
test ! -e "$O"
test "$(df -B1 --output=avail /tmp | tail -1)" -ge 214748364800
if [ "$(df -B1 --output=avail "$C2" | tail -1)" -lt "$MIN_PROJECT_FREE_BYTES" ]; then
  printf 'Project space is below the 200 GiB floor\n' >&2
  exit 78
fi
mkdir -p "$S" "$O"
log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a "$O/steps"; }
snapshot() {
  log "CARD $* CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
  printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" >> "$O/card_readings.txt"
  nvidia-smi --query-gpu=index,uuid,memory.used,utilization.gpu --format=csv,noheader >> "$O/card_readings.txt" 2>&1 || true
  nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader >> "$O/card_readings.txt" 2>&1 || true
  pgrep -fu "$USER" '[/]evalx/work/camera/direct.py launch' >> "$O/card_readings.txt" || true
}
save() {
  if [ -d "$PR/results" ]; then
    if python3 -I -B "$PC/runtime.py" --source "$PC" --output "$O" --slot "$SAVE_SLOT" >> "$O/saves.jsonl"; then
      SAVE_SLOT=$((1-SAVE_SLOT))
    else
      SAVE_FAILED=1
      return 1
    fi
  fi
  [ ! -f "$S/j/launch/launch.log" ] || cp "$S/j/launch/launch.log" "$O/launch.log"
}
stop() {
  local reason=$1 code=$2
  trap - USR1 TERM INT
  log "STOP $reason"
  if [ -n "$CHILD" ] && kill -0 "$CHILD" 2>/dev/null; then
    kill -TERM -- -"$CHILD" 2>/dev/null || true
    sleep 20
    kill -KILL -- -"$CHILD" 2>/dev/null || true
  fi
  if [ "$SAVE_FAILED" = 0 ]; then save || log "SAVE unavailable; existing archives retained"; fi
  snapshot "$reason"
  exit "$code"
}
trap 'stop time_limit 75' USR1
trap 'stop signal 76' TERM INT
log "START model=$MODEL host=$(hostname -s) bundle=$BSHA"
snapshot before_stage
test "$(sha256sum "$BUNDLE" | cut -d' ' -f1)" = "$BSHA"
tar -xf "$BUNDLE" -C "$S" --no-same-owner
python3 -I -B "$PC/package.py" --verify "$PC"
declare -A NP=([4fe70504]=2 [50011a59]=10 [371be2e2]=1)
for tok in 4fe70504 50011a59 371be2e2; do
  PL=()
  for k in $(seq -f %02g 0 $((NP[$tok]-1))); do
    if [ -s "$C2/p/d59945c1/SHA256SUMS.$tok.$k" ]; then R=$C2; else R=${C%/p/*}; fi
    (cd "$R" && sha256sum -c --quiet "p/d59945c1/SHA256SUMS.$tok.$k")
    PL+=("$R/p/d59945c1/$tok.$k")
  done
  cat "${PL[@]}" | timeout 3600 tar -xf - -C "$S"
  log "STAGED $tok"
done
cp /project/community/jjyeung/cp4tk_rt/kit/bwrap "$S/bwrap"
chmod +x "$S/bwrap"
mkdir -p "$S/m/ap/85fc3486" "$S/fsw" "$PC/frames"
timeout 3600 tar -xf /project/community/jjyeung/cp4tk_rt/kit/model_qwen35_9b_c2022362.tar \
  -C "$S/m/ap/85fc3486" --strip-components=3
if [ "$MODEL" = cp1m200 ]; then
  cat /project/community/jjyeung/distill/okit/in/cr/m200.p{00..10} |
    timeout 3600 tar -xf - -C "$S/fsw" --no-same-owner
  KIT=/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_vl64rt
else
  mkdir -p "$S/m/ap/bdad3598/k"
  timeout 3600 cp /project/community/jjyeung/cp4tk_f17/f17.tar "$S/m/ap/bdad3598/k/f17.tar"
  KIT=/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_eval_gaps
fi
timeout 3600 "$S/sj/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3" -s -B \
  "$S/x/pull.py" "$S/x/need_frames.txt" /project/community/jjyeung/cp4tk_fr/k6tk \
  2>>"$O/pull.log" | tar -xf - -C "$PC/frames"
log "STAGED model_and_frames"
python3 -I -B "$PC/package.py" --verify "$PC"
BW=$S/bwrap
NS=()
for d in /*; do
  n=${d#/}
  case "$n" in proc|dev|tmp|scratch|home|lustre|data|data2|data3|data4|project) continue;; esac
  if [ -L "$d" ]; then NS+=(--symlink "$(readlink "$d")" "$d"); else NS+=(--bind "$d" "$d"); fi
done
NS+=(--dev-bind /dev /dev --proc /proc --bind /tmp /tmp --dir /scratch --bind "$S/sj" /scratch/jjyeung
  --bind "$S/fsw" "$FSWU" --dir /lustre --bind "$S/m/ap" "$AP"
  --dir /home/jyeung/.local/share/uv/python
  --ro-bind "$S/sj/uv-python/cpython-3.12.13-linux-x86_64-gnu" /home/jyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu
  --dir /home/jjyeung --die-with-parent)
inns() {
  local J=$1; shift
  mkdir -p "$J/cache" "$J/t"
  env -i PATH=/usr/local/bin:/usr/bin:/bin USER="$USER" CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:?}" \
    HOME="$J" TMPDIR="$J/t" XDG_CACHE_HOME="$J/cache" HF_HOME="$J/cache/hf" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
    HF_HUB_DISABLE_TELEMETRY=1 TOKENIZERS_PARALLELISM=false VLLM_NO_USAGE_STATS=1 DO_NOT_TRACK=1 \
    VLLM_USE_FLASHINFER_SAMPLER=0 PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 \
    "$BW" "${NS[@]}" --chdir "$J" "$@"
}
inns "$S/j/bind" "$PY" -I -s -B "$L/direct.py" bind --family camera --cell "$MODEL" --kit "$KIT" \
  --models "$L/models.json" --frames-root "$L/frames" --dest "$RUN" > "$O/bind.log" 2>&1
python3 -I -B -c 'import json,sys;b=json.load(open(sys.argv[1]));assert b["ready"] and not b["dry"] and b["tasks"]==450' "$PR/BIND_STATUS.json"
log "BOUND model=$MODEL"
mkdir -p "$S/j/launch"
{
  declare -p NS BW S USER
  declare -f inns
  printf 'inns %q %q -s -B %q launch --dest %q --attempt %q\n' "$S/j/launch" "$VPY" "$L/direct.py" "$RUN" "$ATT"
} > "$S/launch.sh"
progress() {
  du -sb --apparent-size "$PR/models" "$PR/results" "$S/j" 2>/dev/null | awk '{s+=$1} END{print s+0}'
}
log "LAUNCH model=$MODEL attempt=$ATT guard=1200s vnice=retained-marker"
setsid bash "$PC/vnice/vnice.sh" bash "$S/launch.sh" > "$S/j/launch/launch.log" 2>&1 &
CHILD=$!
snapshot launched
last=$(progress || true)
t0=$(date +%s)
n=0
while kill -0 "$CHILD" 2>/dev/null; do
  sleep 30 & wait $!
  n=$((n+1))
  p=$(progress || true)
  if [ "$p" != "$last" ]; then last=$p; t0=$(date +%s); fi
  if [ $((n % 4)) = 0 ]; then
    save || stop save_failed 78
    log "PROGRESS bytes=$p"
  fi
  [ $(( $(date +%s)-t0 )) -le 1200 ] || stop stall 77
done
rc=0
wait "$CHILD" || rc=$?
CHILD=
save || stop save_failed 78
snapshot ended
log "END model=$MODEL rc=$rc"
exit "$rc"
