#!/bin/bash
set -euo pipefail
if [[ $# != 3 ]]; then echo 'Usage: run_card.sh <card> <zero-based i/n> <out>' >&2; exit 2; fi
card=$1
shard=$2
out=$3
[[ $card =~ ^[0-9]+$ ]] || { echo 'Card must be a numeric physical GPU index' >&2; exit 2; }
# Refuse failed, empty, or ambiguous GPU queries as well as busy cards.
if ! used=$(nvidia-smi -i "$card" --query-gpu=memory.used --format=csv,noheader,nounits); then
  echo "Cannot check card $card; refusing launch" >&2; exit 2
fi
[[ $used =~ ^[[:space:]]*([0-9]+)[[:space:]]*$ ]] || { echo "Invalid memory reading for card $card; refusing launch" >&2; exit 2; }
used=${BASH_REMATCH[1]}
if (( used > 1024 )); then echo "Card $card is busy: $used MiB used exceeds 1 GiB; refusing launch" >&2; exit 3; fi
: "${H10_EXPORT:?Set H10_EXPORT to the step-544 export}"
: "${H10_ARTIFACT_MANIFEST:?Set H10_ARTIFACT_MANIFEST}"
: "${H10_READER_ROOT:?Set H10_READER_ROOT to the published b04 reader}"
kit=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
export H10_ITEMS=${H10_ITEMS:-$kit/items/devs1_routed.json}
export H10_ARMS=${H10_ARMS:-own,tower}
export H10_MODES=${H10_MODES:-scale_translation:0.5,scale_translation:2,rotate_translation:180,negate_turn,scale_scene:0.5,scale_scene:2}
export H10_SHARD=$shard H10_OUT=$out H10_KIT=$kit
export CUDA_VISIBLE_DEVICES=$card OMP_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 MKL_NUM_THREADS=16 NUMEXPR_NUM_THREADS=16
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false
export TMPDIR=$out/tmp XDG_CACHE_HOME=$out/cache HF_HOME=$out/hf TRITON_CACHE_DIR=$out/triton
export TORCH_HOME=$out/torch TORCHINDUCTOR_CACHE_DIR=$out/inductor
export PYTHONPATH=$kit/tree:$kit${PYTHONPATH:+:$PYTHONPATH}
mkdir -p "$out" "$TMPDIR" "$XDG_CACHE_HOME" "$HF_HOME" "$TRITON_CACHE_DIR" "$TORCH_HOME" "$TORCHINDUCTOR_CACHE_DIR"
# vnice uses bash -c "$*". Pass a fixed script path; data travels in environment variables.
[[ $kit != *[[:space:]]* ]] || { echo 'vnice requires a kit path without whitespace' >&2; exit 2; }
# CUDA reserves a large virtual address range; CPU tests apply the 32 GiB cap in cpu.sh.
exec /data3/shared/scripts/vnice/vnice.sh nice -n 10 bash "$kit/h1eval/h10/card_entry.sh" >> "$out/log" 2>&1
