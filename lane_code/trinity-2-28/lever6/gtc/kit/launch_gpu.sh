#!/bin/bash
# GTC GPU job launcher (lever6 runs it by hand, inside tmux, on trinity-2-28; it never relaunches anything).
#   bash kit/launch_gpu.sh [t]        default: both arms, t first; "t" runs arm t only
# Order: compute node (not the head node); two nvidia-smi readings 300 s apart show a card with >= 24e9 bytes, compute
# capability >= 8.0 and <= 1024 MiB used in both; then off trinity-0-13 the pass runs under
# /data3/shared/scripts/vnice/vnice.sh (LANE_RULES), with a timeout. Work vnice kills is reported, not rerun.
# Test hooks (GTC_DRY_LAUNCH=1 only): GTC_NVIDIA_SMI, GTC_WAIT_SECONDS, GTC_HOST.
set -u
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$KIT")"
OUT="$ROOT/out/track"
PY=/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python
VNICE=/data3/shared/scripts/vnice/vnice.sh
TIMEOUT=3600
ARMS="t,s"; [ "${1:-}" = t ] && ARMS="t"
[ "$#" -le 1 ] && { [ "$#" = 0 ] || [ "$1" = t ]; } || { echo "usage: launch_gpu.sh [t]"; exit 1; }
DRY="${GTC_DRY_LAUNCH:-0}"; SMI=nvidia-smi; WAIT=300; HOST="$(hostname -s)"
if [ "$DRY" = 1 ]; then SMI="${GTC_NVIDIA_SMI:-$SMI}"; WAIT="${GTC_WAIT_SECONDS:-$WAIT}"; HOST="${GTC_HOST:-$HOST}"; OUT="$ROOT/work/dry_launch"; fi
mkdir -p "$OUT"; STAMP="$(date -u +%Y%m%dT%H%M%SZ)"; LOG="$OUT/launch_$STAMP.log"
note() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
ev() { echo "{\"time\": \"$(date -u +%FT%TZ)\", \"event\": \"$1\", \"host\": \"$HOST\", \"detail\": \"$2\"}" >> "$OUT/EVENTS.jsonl"; note "$1 $2"; }
refuse() { ev LAUNCH_REFUSED "$1"; exit 1; }
case "$HOST" in trinity) refuse head_node ;; trinity-*) ;; *) refuse not_a_trinity_compute_node ;; esac
[ -f "$OUT/KILLED" ] && refuse previous_pass_killed_report_it_do_not_rerun
(cd "$ROOT" && sha256sum --quiet -c SHA256SUMS_GTC) >> "$LOG" 2>&1 || refuse kit_bytes_differ_from_SHA256SUMS_GTC
read_cards() { "$SMI" --query-gpu=index,memory.total,memory.used,compute_cap --format=csv,noheader,nounits | tr -d ' '; }
R1="$(read_cards)" || refuse nvidia_smi_failed; note "reading 1: $(echo $R1)"
sleep "$WAIT"
R2="$(read_cards)" || refuse nvidia_smi_failed; note "reading 2: $(echo $R2)"
PICK=""
for line in $R1; do
  IFS=, read -r idx total used cap <<< "$line"
  line2="$(echo "$R2" | tr ' ' '\n' | grep "^$idx,")" || continue
  IFS=, read -r _ _ used2 _ <<< "$line2"; major="${cap%%.*}"
  if [ $((total * 1048576)) -ge 24000000000 ] && [ "$major" -ge 8 ] && [ "$used" -le 1024 ] && [ "$used2" -le 1024 ]; then PICK="$idx"; break; fi
done
[ -n "$PICK" ] || refuse no_card_free_in_both_readings
ev LAUNCH "gpu=$PICK arms=$ARMS reading1=$(echo $R1 | tr ' ' ';') reading2=$(echo $R2 | tr ' ' ';')"
W="$ROOT/work/gpu_cache"; mkdir -p "$W/tmp"
INNER="$ROOT/work/gpu_inner_$STAMP.sh"
cat > "$INNER" <<EOF
#!/bin/bash
cd "$KIT"
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=$PICK PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export XDG_CACHE_HOME=$W/xdg HF_HOME=$W/hf TORCH_HOME=$W/torch TRITON_CACHE_DIR=$W/triton TORCHINDUCTOR_CACHE_DIR=$W/inductor
export CUDA_CACHE_PATH=$W/nv MPLCONFIGDIR=$W/mpl TMPDIR=$W/tmp HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
exec timeout -k 30 $TIMEOUT $PY -B track.py --device cuda --arms $ARMS --out $OUT --hard-stop $((TIMEOUT-120))
EOF
if [ "$DRY" = 1 ]; then note "dry launch: would run $([ "$HOST" = trinity-0-13 ] || echo "bash $VNICE ")bash $INNER"; exit 0; fi
if [ "$HOST" = trinity-0-13 ]; then setsid --wait bash "$INNER" > "$OUT/pass_$STAMP.log" 2>&1
else note "vnice sha256 $(sha256sum "$VNICE" | cut -c1-64)"; setsid --wait bash "$VNICE" bash "$INNER" > "$OUT/pass_$STAMP.log" 2>&1; fi
CODE=$?
case "$CODE" in
  0) ev PASS_DONE "exit=0" ;;
  2) ev PASS_STOPPED "exit=2 hard stop; see INDEX.json" ;;
  124|137|143) date -u +%FT%TZ > "$OUT/KILLED"; ev KILLED "exit=$CODE (timeout or vnice/operator signal); report, do not rerun" ;;
  *) ev PASS_FAILED "exit=$CODE; report, do not rerun" ;;
esac
exit "$CODE"
