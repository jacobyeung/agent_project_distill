#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
: "${CUDA_VISIBLE_DEVICES:?Set the single GPU assigned by the orchestrator}"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export XDG_CACHE_HOME="$PWD/runtime/cache" HF_HOME="$PWD/runtime/hf" TRITON_CACHE_DIR="$PWD/runtime/triton" MPLCONFIGDIR="$PWD/runtime/mpl" TMPDIR="$PWD/runtime/tmp"
export TORCH_HOME="$PWD/runtime/torch" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export GEO_BAKEOFF_ROOT="$PWD" GEO_BAKEOFF_OUTPUT_ROOT="$PWD/out" GEO_BAKEOFF_ASSETS=/scratch/jjyeung/geo_bakeoff_kit/assets
export PYTHONPATH=/scratch/jjyeung/geo_bakeoff_kit/runtime/site:/scratch/jjyeung/geo_bakeoff_kit/assets/da3-src/Depth-Anything-3-3d835ec1a5802d64a8b8b15f817a1ab54809bfe4/src
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_CACHE_PATH="$PWD/runtime/nv"
mkdir -p "$TMPDIR" "$CUDA_CACHE_PATH"
case "${1:-}" in A|B|C) ;; *) echo 'REFUSE: expected part A, B or C' >&2; exit 1;; esac
[[ "$CUDA_VISIBLE_DEVICES" != *,* ]] || { echo 'REFUSE: exactly one visible card required' >&2; exit 1; }
part="$1"
smi=nvidia-smi
wait_command=/usr/bin/sleep
log_root="$PWD/out/tower_frames"
fixture=0
# Fixture mode uses fake commands and always exits before the GPU runner.
if [[ "${2:-}" == --test-fixture ]]; then
 [[ $# == 3 ]] || exit 1
 fixture_root="$(realpath -- "$3")"
 [[ "$fixture_root" == "$PWD/runtime/"* && -x "$fixture_root/nvidia-smi" && -x "$fixture_root/sleep" ]] || exit 1
 smi="$fixture_root/nvidia-smi"
 wait_command="$fixture_root/sleep"
 log_root="$fixture_root/out/tower_frames"
 fixture=1
else
 for arg in "$@"; do
  [[ "$arg" != --test-fixture ]] || exit 1
 done
fi
mkdir -p "$log_root"
log="$log_root/NVIDIA_SMI_${part}.log"
busy=0
for reading in 1 2; do
 if [[ "$reading" == 2 ]]; then "$wait_command" 300; fi
 printf 'Reading %s UTC %s card %s\n' "$reading" "$(date -u +%FT%TZ)" "$CUDA_VISIBLE_DEVICES" >> "$log"
 if ! gpu="$("$smi" -i "$CUDA_VISIBLE_DEVICES" --query-gpu=memory.used,utilization.gpu --format=csv,noheader,nounits 2>> "$log")"; then
  echo 'REFUSE: nvidia-smi GPU query failed' >&2; exit 1
 fi
 printf 'memory.used MiB, utilization.gpu %%\n%s\n' "$gpu" >> "$log"
 if ! apps="$("$smi" -i "$CUDA_VISIBLE_DEVICES" --query-compute-apps=pid --format=csv,noheader,nounits 2>> "$log")"; then
  echo 'REFUSE: nvidia-smi process query failed' >&2; exit 1
 fi
 printf 'compute-apps pid\n%s\n' "$apps" >> "$log"
 # Refuse malformed or multiple-card output as well as more than 1 GiB used.
 if ! awk -F, 'NF != 2 {exit 1} {gsub(/ /,"",$1); gsub(/ /,"",$2); if ($1 !~ /^[0-9]+([.][0-9]+)?$/ || $2 !~ /^[0-9]+([.][0-9]+)?$/ || $1 > 1024) exit 1} END {if (NR != 1) exit 1}' <<< "$gpu"; then busy=1; fi
 if [[ -n "${apps//[[:space:]]/}" ]]; then busy=1; fi
done
if [[ "$busy" == 1 ]]; then echo 'REFUSE: visible card has a compute process, more than 1 GiB used, or invalid readings' >&2; exit 1; fi
if [[ "$fixture" == 1 ]]; then exit 0; fi
ulimit -d 39062500
exec nice -n 10 /scratch/jjyeung/envs/sam3_scipy_ovl/bin/python -B code/runner.py "$@"
