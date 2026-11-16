#!/bin/bash
# Usage: bash code/run_gpu.sh <card>   (run inside tmux b11gpu on trinity-1-18; under vnice since 1-18 != 0-13)
# Stages (each resumable; a stage that exits non-zero stops the chain):
#  1 determinism: scorer on the first 10 held-out captures, twice (det_a, det_b), compare
#  2 full scorer, all arms, all 296 captures -> out/journals
#  3 direct read of step 544 on held-out K1 items -> out/direct
set -euo pipefail
CARD=$1
L=/scratch/jjyeung/orch_n30/b11_presence
PY="/scratch/jjyeung/envs/vllm/bin/python -I"
VN=/data3/shared/scripts/vnice/vnice.sh
C=${CACHE_ROOT:-/scratch/jjyeung}
export CUDA_VISIBLE_DEVICES=$CARD XDG_CACHE_HOME=$C/.cache HF_HOME=$C/hf \
       TRITON_CACHE_DIR=$C/.triton VLLM_CACHE_ROOT=$C/.cache/vllm HF_HUB_OFFLINE=1
cd $L
mkdir -p work/logs out/det
log(){ echo "$(date -u +%FT%TZ) $*" | tee -a work/logs/run_gpu.log; }
log "start card=$CARD host=$(hostname -s)"
if [ ! -f out/det/DETERMINISM.json ]; then
  for r in a b; do
    log "det $r"; $VN $PY code/scorer.py --split heldout --limit 10 --out out/det/det_$r --batch 32 >> work/logs/det_$r.log 2>&1
  done
  $PY code/det_compare.py out/det/det_a out/det/det_b out/det/DETERMINISM.json | tee -a work/logs/run_gpu.log
  python3 -c "import json,sys;sys.exit(0 if json.load(open('out/det/DETERMINISM.json'))['pass'] else 1)" || { log "DET FAIL"; exit 3; }
fi
log "full scorer"; $VN $PY code/scorer.py --out out/journals --batch 32 >> work/logs/scorer_full.log 2>&1
n=$(ls out/journals/V | wc -l); m=$(ls out/journals/IY | wc -l); log "journals V=$n IY=$m"
[ "$n" = 296 ] && [ "$m" = 296 ] || { log "SCORER INCOMPLETE"; exit 4; }
log "direct"; $VN $PY code/direct.py read --out out/direct >> work/logs/direct.log 2>&1
log "direct rows $(wc -l < out/direct/journal.jsonl)"
log "DONE"
