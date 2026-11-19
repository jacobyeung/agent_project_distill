#!/bin/bash
set -euo pipefail
[[ $# == 5 ]] || { echo 'Usage: host_run.sh CARD|cpu SET own i/n OUT' >&2; exit 2; }
card=$1; set_name=$2; arms=$3; partition=$4; out=$5
[[ $set_name == devs1_routed || $set_name == revsi999 ]] || { echo 'Unknown item set' >&2; exit 2; }
[[ $arms == own ]] || { echo 'Host wrapper requires ARMS=own' >&2; exit 2; }
kit=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
export H10_KIT=$kit H10_ITEMS=$kit/items/$set_name.json H10_ARMS=$arms H10_SHARD=$partition H10_OUT=$out
export H10_READER_ROOT=${H10_READER_ROOT:-/scratch/jjyeung/b04shm/b04/host2/b04_e2ehook}
export H10_SETTINGS=${H10_SETTINGS:-$H10_READER_ROOT/parity_kit/settings_bw.json}
export H10_PY=${H10_PY:-/scratch/jjyeung/envs/vllm/bin/python}
export H10_OVERLAY=${H10_OVERLAY:-/scratch/jjyeung/b04shm/b04/pyoverlay}
export PYTHONPATH=$H10_OVERLAY:$kit/tree:$kit:$H10_READER_ROOT
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 MKL_NUM_THREADS=16 NUMEXPR_NUM_THREADS=16
export TMPDIR=$out/tmp XDG_CACHE_HOME=$out/cache HF_HOME=$out/hf TORCH_HOME=$out/torch
export TRITON_CACHE_DIR=$out/triton TORCHINDUCTOR_CACHE_DIR=$out/inductor
if [[ $card == cpu ]]; then
  [[ $set_name == devs1_routed && $partition == 0/1 ]] || { echo 'CPU first batch requires devs1_routed 0/1' >&2; exit 2; }
  export CUDA_VISIBLE_DEVICES='' H10_CPU_FIRST=1
  mkdir -p "$out" "$TMPDIR" "$XDG_CACHE_HOME" "$HF_HOME" "$TORCH_HOME" "$TRITON_CACHE_DIR" "$TORCHINDUCTOR_CACHE_DIR"
  cd "$kit"
  exec nice -n 10 "$H10_PY" -B -m h1eval.h10.host_entry >> "$out/log" 2>&1
fi
export H10_CPU_FIRST=0
# run_card reads settings in host_entry; placeholders are not model paths.
export H10_EXPORT=${H10_EXPORT:-from-settings} H10_ARTIFACT_MANIFEST=${H10_ARTIFACT_MANIFEST:-from-settings}
exec bash "$kit/h1eval/h10/run_card.sh" "$card" "$partition" "$out"
