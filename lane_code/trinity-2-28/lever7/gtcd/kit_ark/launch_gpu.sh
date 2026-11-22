#!/bin/bash
# GTC-D GPU job launcher, arm d only (lever7 runs it by hand, inside tmux, on trinity-0-13; it never relaunches anything).
#   bash kit/launch_gpu.sh [d]                       GPU pass over every OK capture of dense/DENSE_D.json
#   bash kit/launch_gpu.sh rehearse-cpu <capture>    CPU rehearsal: the same inner command line with --device cpu --captures
#   kit_ark (ARKit unit): append --dense <manifest> --out <track dir> (or set GTCD_DENSE, GTCD_TRACK_OUT; flags win), e.g.
#   bash kit_ark/launch_gpu.sh d --dense $ROOT/dense_ark/DENSE_D_ARK.json --out $ROOT/out_ark/track
#   Defaults are the ScanNet unit's dense/DENSE_D.json and out/track. A non-default manifest needs an explicit --out (the CPU
#   rehearsal defaults to work/rehearsal_cpu_ark), must match its <manifest>.sha256 (written by dense.py), and may not write into
#   out/track; the ScanNet manifest may not write into out_ark/track. Both paths must be on /scratch.
# Order (GPU): compute node (not the head node, not trinity-1-13, 0-23, 0-8, 3-23 or 0-18); run from /scratch; kit bytes match
# SHA256SUMS_GTCD_ARK (kit_ark's seal); two nvidia-smi readings 300 s apart show a card with >= 24e9 bytes, compute capability >= 8.0 and <= 100 MiB
# used in both; on trinity-0-13 the pass runs at normal priority, and off it under /data3/shared/scripts/vnice/vnice.sh
# (LANE_RULES), with a timeout. Every child's exit code goes to the log and EVENTS.jsonl, and its stderr to its own file.
# Work vnice or the timeout kills is reported, not rerun.
# Test hooks (GTC_DRY_LAUNCH=1 only): GTC_NVIDIA_SMI, GTC_WAIT_SECONDS, GTC_HOST.
set -u
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$KIT")"
DENSE_DEFAULT="$ROOT/dense/DENSE_D.json"; OUT_DEFAULT="$ROOT/out/track"; OUT_ARK_TRACK="$ROOT/out_ark/track"
SUMS=SHA256SUMS_GTCD_ARK
DENSE="${GTCD_DENSE:-$DENSE_DEFAULT}"; TOUT="${GTCD_TRACK_OUT:-}"
POS=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dense|--out) [ "$#" -ge 2 ] || { echo "usage: launch_gpu.sh [d] | rehearse-cpu <capture>  [--dense <manifest>] [--out <dir>]"; exit 1; }
                   if [ "$1" = --dense ]; then DENSE="$2"; else TOUT="$2"; fi; shift 2 ;;
    *) POS+=("$1"); shift ;;
  esac
done
set -- ${POS[@]+"${POS[@]}"}
PY=/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python
VNICE=/data3/shared/scripts/vnice/vnice.sh
TIMEOUT=5400
ARMS="d"; MAX_USED_MIB=100; MODE=gpu; CAPS=all
if [ "$#" = 2 ] && [ "$1" = rehearse-cpu ]; then MODE=cpu; CAPS="$2"
  if [ "$DENSE" = "$DENSE_DEFAULT" ]; then OUT="${TOUT:-$ROOT/work/rehearsal_cpu}"; else OUT="${TOUT:-$ROOT/work/rehearsal_cpu_ark}"; fi
elif [ "$#" -le 1 ] && { [ "$#" = 0 ] || [ "$1" = d ]; }; then OUT="${TOUT:-$OUT_DEFAULT}"
else echo "usage: launch_gpu.sh [d] | rehearse-cpu <capture>  [--dense <manifest>] [--out <dir>]"; exit 1; fi
DRY="${GTC_DRY_LAUNCH:-0}"; SMI=nvidia-smi; WAIT=300; HOST="$(hostname -s)"
# LOGD holds the launcher's log, EVENTS.jsonl and child stderr: the track dir itself, except in a dry launch (work/dry_launch,
# which is then also the track dir unless --out was given, so the dry inner line names the real ARKit --out).
LOGD="$OUT"
if [ "$DRY" = 1 ]; then SMI="${GTC_NVIDIA_SMI:-$SMI}"; WAIT="${GTC_WAIT_SECONDS:-$WAIT}"; HOST="${GTC_HOST:-$HOST}"; LOGD="$ROOT/work/dry_launch"; OUT="${TOUT:-$LOGD}"; fi
mkdir -p "$LOGD"; STAMP="$(date -u +%Y%m%dT%H%M%SZ)"; LOG="$LOGD/launch_$STAMP.log"; ERRD="$LOGD/stderr_$STAMP"; mkdir -p "$ERRD"
note() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG" >&2; }   # to stderr, so a $(child ...) capture holds only the child's stdout
ev() { echo "{\"time\": \"$(date -u +%FT%TZ)\", \"event\": \"$1\", \"host\": \"$HOST\", \"detail\": \"$2\"}" >> "$LOGD/EVENTS.jsonl"; note "$1 $2"; }
refuse() { ev LAUNCH_REFUSED "$1"; exit 1; }
# child NAME CMD...: runs CMD with stdout to the caller, stderr to $ERRD/NAME.err; logs and returns its exit code.
child() { local name="$1"; shift; "$@" 2> "$ERRD/$name.err"; local rc=$?; ev CHILD "name=$name exit=$rc stderr=$ERRD/$name.err bytes=$(stat -c %s "$ERRD/$name.err")"; return $rc; }
case "$HOST" in trinity) refuse head_node ;; trinity-1-13|trinity-0-23|trinity-0-8|trinity-3-23|trinity-0-18) refuse "host_not_allowed_$HOST" ;; trinity-*) ;; *) refuse not_a_trinity_compute_node ;; esac
case "$ROOT" in /scratch/*) ;; *) refuse not_on_scratch ;; esac
case "$DENSE" in /scratch/*) ;; *) refuse dense_manifest_not_on_scratch ;; esac
case "$OUT" in /scratch/*) ;; *) refuse track_out_not_on_scratch ;; esac
case "$(pwd -P)" in /scratch/*) ;; *) cd "$ROOT" ;; esac
[ -f "$DENSE" ] || refuse "dense_manifest_missing_$DENSE"
if [ "$DENSE" != "$DENSE_DEFAULT" ]; then
  [ "$MODE" = cpu ] || [ -n "$TOUT" ] || refuse non_default_dense_needs_explicit_out
  [ "$(readlink -m "$OUT")" != "$(readlink -m "$OUT_DEFAULT")" ] || refuse non_scannet_manifest_into_scannet_out_track
  (cd "$(dirname "$DENSE")" && child dense_sha256 sha256sum --quiet -c "$(basename "$DENSE").sha256") >> "$LOG" || refuse dense_manifest_differs_from_its_sha256
else
  [ "$(readlink -m "$OUT")" != "$(readlink -m "$OUT_ARK_TRACK")" ] || refuse scannet_manifest_into_out_ark_track
fi
[ -f "$OUT/KILLED" ] && refuse previous_pass_killed_report_it_do_not_rerun
(cd "$ROOT" && child sha256sum sha256sum --quiet -c "$SUMS") >> "$LOG" || refuse "kit_bytes_differ_from_$SUMS"
W="$ROOT/work/gpu_cache"; mkdir -p "$W/tmp"
INNER="$ROOT/work/${MODE}_inner_$STAMP.sh"
if [ "$MODE" = gpu ]; then
  read_cards() { "$SMI" --query-gpu=index,memory.total,memory.used,compute_cap --format=csv,noheader,nounits | tr -d ' '; }
  R1="$(child nvidia_smi_1 read_cards)" || refuse nvidia_smi_failed; note "reading 1: $(echo $R1)"
  sleep "$WAIT"
  R2="$(child nvidia_smi_2 read_cards)" || refuse nvidia_smi_failed; note "reading 2: $(echo $R2)"
  PICK=""
  for line in $R1; do
    IFS=, read -r idx total used cap <<< "$line"
    line2="$(echo "$R2" | tr ' ' '\n' | grep "^$idx,")" || continue
    IFS=, read -r _ _ used2 _ <<< "$line2"; major="${cap%%.*}"
    if [ $((total * 1048576)) -ge 24000000000 ] && [ "$major" -ge 8 ] && [ "$used" -le "$MAX_USED_MIB" ] && [ "$used2" -le "$MAX_USED_MIB" ]; then PICK="$idx"; break; fi
  done
  [ -n "$PICK" ] || refuse no_card_free_in_both_readings
  ev LAUNCH "gpu=$PICK arms=$ARMS dense=$DENSE out=$OUT reading1=$(echo $R1 | tr ' ' ';') reading2=$(echo $R2 | tr ' ' ';')"
  DEVENV="CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=$PICK"; DEV=cuda
else
  ev LAUNCH "rehearsal device=cpu arms=$ARMS captures=$CAPS dense=$DENSE out=$OUT"
  DEVENV="CUDA_VISIBLE_DEVICES="; DEV=cpu
fi
# The one inner command line; the CPU rehearsal differs only in the device environment, --device and --captures.
cat > "$INNER" <<EOF
#!/bin/bash
cd "$KIT"
export $DEVENV PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export XDG_CACHE_HOME=$W/xdg HF_HOME=$W/hf TORCH_HOME=$W/torch TRITON_CACHE_DIR=$W/triton TORCHINDUCTOR_CACHE_DIR=$W/inductor
export CUDA_CACHE_PATH=$W/nv MPLCONFIGDIR=$W/mpl TMPDIR=$W/tmp HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
timeout -k 30 $TIMEOUT $PY -B track.py --device $DEV --arms $ARMS --out $OUT --hard-stop $((TIMEOUT-120)) --captures $CAPS --dense $DENSE
EOF
note "inner: $(tail -1 "$INNER")"
if [ "$DRY" = 1 ]; then note "dry launch: would run $([ "$MODE" = gpu ] && [ "$HOST" != trinity-0-13 ] && echo "bash $VNICE ")bash $INNER"; exit 0; fi
if [ "$MODE" = cpu ] || [ "$HOST" = trinity-0-13 ]; then
  if [ "$MODE" = cpu ]; then child pass nice -n 10 setsid --wait bash "$INNER" > "$LOGD/pass_$STAMP.log"; else child pass setsid --wait bash "$INNER" > "$LOGD/pass_$STAMP.log"; fi
else note "vnice sha256 $(sha256sum "$VNICE" | cut -c1-64)"; child pass setsid --wait bash "$VNICE" bash "$INNER" > "$LOGD/pass_$STAMP.log"; fi
CODE=$?
case "$CODE" in
  0) ev PASS_DONE "exit=0" ;;
  2) ev PASS_STOPPED "exit=2 hard stop; see INDEX.json" ;;
  124|137|143) date -u +%FT%TZ > "$OUT/KILLED"; ev KILLED "exit=$CODE (timeout or vnice/operator signal); report, do not rerun" ;;
  *) ev PASS_FAILED "exit=$CODE; stderr $ERRD/pass.err; report, do not rerun" ;;
esac
exit "$CODE"
