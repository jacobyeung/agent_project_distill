#!/bin/bash
# J1 GPU job launcher (lever8 runs it by hand inside tmux on trinity-0-13; it never relaunches anything).
#   bash kit/launch_gpu.sh                                   GPU pass over the 46 captures of out/PROMPTS_J1.json, ONE card
#   bash kit/launch_gpu.sh rehearse-cpu <capture> [anchors]  CPU rehearsal: the same inner command line with the CPU device,
#                                                            the one capture and, only if given, an anchor limit (default 32)
# Order (GPU): the host is trinity-0-13 (refused: the head node, trinity-1-13, 0-23, 0-8, 3-23, 0-18 and every other host); run
# from /scratch; kit bytes match SHA256SUMS_J1; the SAM 3 checkpoint, receipt and source exist; two nvidia-smi readings of the
# cards 300 s apart, inside this command, show a card with >= 24e9 bytes, compute capability >= 8.0 and <= 100 MiB used in both;
# both readings go to EVENTS.jsonl; the pass runs on that one card at normal priority under a timeout. Every child's exit code
# goes to the log and EVENTS.jsonl, and its stderr to its own file. Work the timeout or a signal kills is reported, not rerun.
# Test hooks (J1_DRY_LAUNCH=1 only): J1_NVIDIA_SMI, J1_WAIT_SECONDS, J1_HOST.
set -u
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$KIT")"
OUT="$ROOT/out/detect"
PY=/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python
TIMEOUT=3600
MAX_USED_MIB=100; MODE=gpu; CAPS=all; AL=32
if [ "$#" -ge 2 ] && [ "$#" -le 3 ] && [ "$1" = rehearse-cpu ]; then MODE=cpu; CAPS="$2"; AL="${3:-32}"; OUT="$ROOT/work/rehearsal_cpu"
elif [ "$#" = 0 ]; then :
else echo "usage: launch_gpu.sh | launch_gpu.sh rehearse-cpu <capture> [anchors]"; exit 1; fi
case "$AL" in ''|*[!0-9]*) echo "usage: anchors is an integer 1..32"; exit 1 ;; esac
DRY="${J1_DRY_LAUNCH:-0}"; SMI=nvidia-smi; WAIT=300; HOST="$(hostname -s)"
if [ "$DRY" = 1 ]; then SMI="${J1_NVIDIA_SMI:-$SMI}"; WAIT="${J1_WAIT_SECONDS:-$WAIT}"; HOST="${J1_HOST:-$HOST}"; OUT="$ROOT/work/dry_launch"; fi
mkdir -p "$OUT"; STAMP="$(date -u +%Y%m%dT%H%M%SZ)"; LOG="$OUT/launch_$STAMP.log"; ERRD="$OUT/stderr_$STAMP"; mkdir -p "$ERRD"
note() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG" >&2; }   # to stderr, so a $(child ...) capture holds only the child's stdout
ev() { echo "{\"time\": \"$(date -u +%FT%TZ)\", \"event\": \"$1\", \"host\": \"$HOST\", \"detail\": \"$2\"}" >> "$OUT/EVENTS.jsonl"; note "$1 $2"; }
refuse() { ev LAUNCH_REFUSED "$1"; exit 1; }
# child NAME CMD...: runs CMD with stdout to the caller, stderr to $ERRD/NAME.err; logs and returns its exit code.
child() { local name="$1"; shift; "$@" 2> "$ERRD/$name.err"; local rc=$?; ev CHILD "name=$name exit=$rc stderr=$ERRD/$name.err bytes=$(stat -c %s "$ERRD/$name.err")"; return $rc; }
case "$HOST" in trinity) refuse head_node ;; trinity-1-13|trinity-0-23|trinity-0-8|trinity-3-23|trinity-0-18) refuse "host_not_allowed_$HOST" ;; trinity-*) ;; *) refuse not_a_trinity_compute_node ;; esac
[ "$MODE" = gpu ] && [ "$HOST" != trinity-0-13 ] && refuse "gpu_launch_only_on_trinity-0-13_not_$HOST"
case "$ROOT" in /scratch/*) ;; *) refuse not_on_scratch ;; esac
cd "$ROOT"
[ -f "$OUT/KILLED" ] && refuse previous_pass_killed_report_it_do_not_rerun
(cd "$ROOT" && child sha256sum sha256sum --quiet -c SHA256SUMS_J1) >> "$LOG" || refuse kit_bytes_differ_from_SHA256SUMS_J1
for f in /scratch/jjyeung/b01ec87a6f29b/d/k/sam3.pt /scratch/jjyeung/b01ec87a6f29b/d/k/SAM3_RECEIPT.json /scratch/jjyeung/b01ec87a6f29b/d/s/sam3/model_builder.py "$PY"; do
  [ -e "$f" ] || refuse "missing_$f"; done
W="$ROOT/work/gpu_cache"; mkdir -p "$W/tmp"
INNER="$ROOT/work/${MODE}_inner_$STAMP.sh"
if [ "$MODE" = gpu ]; then
  read_cards() { "$SMI" --query-gpu=index,memory.total,memory.used,compute_cap --format=csv,noheader,nounits | tr -d ' '; }
  R1="$(child nvidia_smi_1 read_cards)" || refuse nvidia_smi_failed; ev NVIDIA_SMI_1 "$(echo $R1 | tr ' ' ';')"
  sleep "$WAIT"
  R2="$(child nvidia_smi_2 read_cards)" || refuse nvidia_smi_failed; ev NVIDIA_SMI_2 "$(echo $R2 | tr ' ' ';') seconds_after_1=$WAIT"
  PICK=""
  for line in $R1; do
    IFS=, read -r idx total used cap <<< "$line"
    line2="$(echo "$R2" | tr ' ' '\n' | grep "^$idx,")" || continue
    IFS=, read -r _ _ used2 _ <<< "$line2"; major="${cap%%.*}"
    if [ $((total * 1048576)) -ge 24000000000 ] && [ "$major" -ge 8 ] && [ "$used" -le "$MAX_USED_MIB" ] && [ "$used2" -le "$MAX_USED_MIB" ]; then PICK="$idx"; break; fi
  done
  [ -n "$PICK" ] || refuse no_card_free_in_both_readings
  ev LAUNCH "gpu=$PICK priority=normal reading1=$(echo $R1 | tr ' ' ';') reading2=$(echo $R2 | tr ' ' ';')"
  DEVENV="CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=$PICK"; DEV=cuda
else
  ev LAUNCH "rehearsal device=cpu captures=$CAPS anchors=$AL"
  DEVENV="CUDA_VISIBLE_DEVICES="; DEV=cpu
fi
# The one inner command line; the CPU rehearsal differs only in the device environment, --device, --captures and --anchor-limit.
cat > "$INNER" <<EOF
#!/bin/bash
cd "$KIT"
export $DEVENV PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export XDG_CACHE_HOME=$W/xdg HF_HOME=$W/hf TORCH_HOME=$W/torch TRITON_CACHE_DIR=$W/triton TORCHINDUCTOR_CACHE_DIR=$W/inductor
export CUDA_CACHE_PATH=$W/nv MPLCONFIGDIR=$W/mpl TMPDIR=$W/tmp HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
timeout -k 30 $TIMEOUT $PY -B detect.py --device $DEV --out $OUT --hard-stop $((TIMEOUT-300)) --captures $CAPS --anchor-limit $AL
EOF
note "inner: $(tail -1 "$INNER")"
if [ "$DRY" = 1 ]; then note "dry launch: would run bash $INNER"; exit 0; fi
if [ "$MODE" = cpu ]; then child pass nice -n 10 setsid --wait bash "$INNER" > "$OUT/pass_$STAMP.log"
else child pass setsid --wait bash "$INNER" > "$OUT/pass_$STAMP.log"; fi
CODE=$?
case "$CODE" in
  0) ev PASS_DONE "exit=0" ;;
  2) ev PASS_STOPPED "exit=2 hard stop, RSS guard or failed capture; see INDEX.json" ;;
  124|137|143) date -u +%FT%TZ > "$OUT/KILLED"; ev KILLED "exit=$CODE (timeout or operator signal); report, do not rerun" ;;
  *) ev PASS_FAILED "exit=$CODE; stderr $ERRD/pass.err; report, do not rerun" ;;
esac
exit "$CODE"
