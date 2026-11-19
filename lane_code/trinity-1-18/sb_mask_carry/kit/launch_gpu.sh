#!/bin/bash
# GPU tracker pass launcher. Run it by hand on the GPU node, inside tmux; it never relaunches anything.
#   bash kit/launch_gpu.sh
# Checks, in order: compute node other than trinity-0-13; kit bytes equal out/KIT_MANIFEST.sha256; the ledger records
# no stop or kill; the CPU preflight finds every staged input; two nvidia-smi readings 300 s apart show a card with
# >= 48e9 bytes total and <= 1024 MiB used in both. Then: setsid --wait -> vnice.sh -> gpu_inner.sh -> timeout -> python.
# Test hooks (MC_DRY_LAUNCH=1 only): MC_NVIDIA_SMI, MC_WAIT_SECONDS, MC_HOST, MC_TEST_OUT, MC_SKIP_PREFLIGHT.
set -u
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$KIT")"
OUT="$ROOT/out/track"
VNICE=/data3/shared/scripts/vnice/vnice.sh
PY=/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python
HARD_STOP=7200
MIN_BYTES=48000000000
MAX_USED_MIB=1024
DRY="${MC_DRY_LAUNCH:-0}"
SMI=nvidia-smi; WAIT=300; HOST="$(hostname -s)"; SKIP_PREFLIGHT=0
if [ "$DRY" = 1 ]; then
  SMI="${MC_NVIDIA_SMI:-$SMI}"; WAIT="${MC_WAIT_SECONDS:-$WAIT}"; HOST="${MC_HOST:-$HOST}"
  OUT="${MC_TEST_OUT:-$OUT}"; SKIP_PREFLIGHT="${MC_SKIP_PREFLIGHT:-0}"
fi
mkdir -p "$OUT"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$OUT/launch_$STAMP.log"

note() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
launch_event() {  # kind, then key=value pairs (values without spaces or quotes)
  local kind="$1"; shift
  local kv="\"time\": \"$(date -u +%FT%TZ)\", \"event\": \"$kind\", \"host\": \"$HOST\", \"launcher_pid\": $$"
  for p in "$@"; do kv="$kv, \"${p%%=*}\": \"${p#*=}\""; done
  echo "{$kv}" >> "$OUT/EVENTS.jsonl"
  note "$kind $*"
}
refuse() { launch_event LAUNCH_REFUSED "reason=$1"; exit 1; }

case "$HOST" in
  trinity) refuse head_node ;;
  trinity-0-13) refuse trinity-0-13_is_excluded ;;
  trinity-*) ;;
  *) refuse not_a_trinity_compute_node ;;
esac
[ -x "$VNICE" ] || [ -f "$VNICE" ] || refuse vnice_missing
[ -f "$ROOT/out/KIT_MANIFEST.sha256" ] || refuse kit_manifest_missing
(cd "$ROOT" && sha256sum --quiet -c out/KIT_MANIFEST.sha256) >> "$LOG" 2>&1 || refuse kit_bytes_differ_from_manifest
RESUME="${MC_RESUME_AFTER_STOP:-0}"
if [ -f "$OUT/BUDGET.json" ] && grep -q '"stopped": "' "$OUT/BUDGET.json" && [ "$RESUME" != 1 ]; then
  refuse ledger_records_stop_or_kill_report_it
fi

if [ "$SKIP_PREFLIGHT" != 1 ]; then
  (cd "$KIT" && CUDA_VISIBLE_DEVICES='' PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$KIT" "$PY" -B mc_preflight.py) >> "$LOG" 2>&1 \
    || refuse preflight_failed_see_$(basename "$LOG")
fi

SPENT="$("$PY" -c "import json,sys; p=sys.argv[1]; import os; print(int(json.load(open(p))['spent_seconds']) if os.path.exists(p) else 0)" "$OUT/BUDGET.json")"
REMAIN=$((HARD_STOP - SPENT))
[ "$REMAIN" -gt 300 ] || refuse budget_spent_${SPENT}s_of_${HARD_STOP}s

read_cards() { "$SMI" --query-gpu=index,memory.total,memory.used --format=csv,noheader,nounits | tr -d ' '; }
R1="$(read_cards)" || refuse nvidia_smi_failed
note "reading 1: $(echo $R1)"
sleep "$WAIT"
R2="$(read_cards)" || refuse nvidia_smi_failed
note "reading 2: $(echo $R2)"
PICK=""
for line in $R1; do
  IFS=, read -r idx total used <<< "$line"
  line2="$(echo "$R2" | tr ' ' '\n' | grep "^$idx,")" || continue
  IFS=, read -r _ total2 used2 <<< "$line2"
  if [ $((total * 1048576)) -ge "$MIN_BYTES" ] && [ "$used" -le "$MAX_USED_MIB" ] && [ "$used2" -le "$MAX_USED_MIB" ]; then
    PICK="$idx"; break
  fi
done
[ -n "$PICK" ] || refuse no_card_with_48e9_bytes_and_at_most_1024MiB_used_in_both_readings
launch_event LAUNCH "gpu=$PICK" "reading1=$(echo $R1 | tr ' ' ';')" "reading2=$(echo $R2 | tr ' ' ';')" \
  "timeout_seconds=$REMAIN" "spent_seconds=$SPENT" "resume_after_stop=$RESUME" \
  "manifest_sha256=$(sha256sum "$ROOT/out/KIT_MANIFEST.sha256" | cut -c1-64)"

export MC_GPU="$PICK" MC_TIMEOUT="$REMAIN" MC_OUT="$OUT" MC_PY="$PY" MC_KIT="$KIT" MC_HARD_STOP="$HARD_STOP" MC_RESUME_AFTER_STOP="$RESUME"
PASSLOG="$OUT/pass_$STAMP.log"
if [ "$DRY" = 1 ]; then
  note "dry launch: would run setsid --wait bash $VNICE bash $KIT/gpu_inner.sh > $PASSLOG"
  exit 0
fi
setsid --wait bash "$VNICE" bash "$KIT/gpu_inner.sh" > "$PASSLOG" 2>&1
CODE=$?
case "$CODE" in
  0) launch_event PASS_DONE "exit=$CODE" ;;
  2) launch_event PASS_STOPPED "exit=$CODE" "detail=see_BUDGET.json_stopped" ;;
  124) launch_event KILLED "exit=$CODE" "by=timeout_hard_stop" "action=report_not_rerun" ;;
  137|143) launch_event KILLED "exit=$CODE" "by=signal(vnice_terminator_or_operator)" "action=report_not_rerun" ;;
  *) launch_event PASS_FAILED "exit=$CODE" "action=report_not_rerun" ;;
esac
if [ "$CODE" = 124 ] || [ "$CODE" = 137 ] || [ "$CODE" = 143 ]; then
  "$PY" - "$OUT/BUDGET.json" "$CODE" <<'EOF'
import json, os, sys
p, code = sys.argv[1], sys.argv[2]
d = json.load(open(p)) if os.path.exists(p) else dict(spent_seconds=0., runs=[], dropped=[], stopped=None)
if not d.get('stopped'):
    d['stopped'] = f'KILLED (exit {code}) recorded by the launcher'
json.dump(d, open(p+'.tmp', 'w'), indent=1); os.replace(p+'.tmp', p)
EOF
fi
exit "$CODE"
