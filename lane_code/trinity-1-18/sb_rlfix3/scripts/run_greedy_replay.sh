#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ $# -lt 1 ]]; then echo 'Usage: run_greedy_replay.sh <card> --export-dir ... --config ... --artifact-binding ... --artifact-binding-sha256 ...' >&2; exit 2; fi
card=$1; shift
[[ $card =~ ^[0-9]+$ ]] || { echo 'Card must be a numeric physical GPU index' >&2; exit 2; }
# Refuse failed, empty, or ambiguous GPU queries as well as busy cards.
if ! used=$(nvidia-smi -i "$card" --query-gpu=memory.used --format=csv,noheader,nounits); then
  echo "Cannot check card $card; refusing launch" >&2; exit 2
fi
[[ $used =~ ^[[:space:]]*([0-9]+)[[:space:]]*$ ]] || { echo "Invalid memory reading for card $card; refusing launch" >&2; exit 2; }
used=${BASH_REMATCH[1]}
if (( used > 1024 )); then echo "Card $card is busy: $used MiB used exceeds 1 GiB; refusing launch" >&2; exit 3; fi
: "${RL_PYTHON:?Set RL_PYTHON to the assigned GPU environment interpreter}"
[[ $RL_PYTHON == /scratch/* && $PWD == /scratch/* ]] || { echo 'RL_PYTHON and the kit must be under /scratch' >&2; exit 2; }
export CUDA_VISIBLE_DEVICES=$card REPLAY_CARD=$card
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export XDG_CACHE_HOME="$PWD/out/cache" HF_HOME="$PWD/out/hf" TORCH_HOME="$PWD/out/torch"
export TRITON_CACHE_DIR="$PWD/out/triton" TORCHINDUCTOR_CACHE_DIR="$PWD/out/inductor" TMPDIR="$PWD/out/tmp"
mkdir -p "$TMPDIR"
export PYTHONPATH="$PWD/overlay${PYTHONPATH:+:$PYTHONPATH}"
command=(nice -n 10 "$RL_PYTHON" -B scripts/greedy_replay.py "$@")
case $(hostname -s) in
  trinity-*)
    # vnice runs bash -c "$*", so every argument must survive word splitting unchanged.
    for arg in "${command[@]}"; do
      [[ $arg =~ ^[A-Za-z0-9_./=:,+-]+$ ]] || { echo "vnice requires plain arguments: $arg" >&2; exit 2; }
    done
    exec timeout 2h "${RL_VNICE:-/data3/shared/scripts/vnice/vnice.sh}" "${command[@]}";;
  *) exec timeout 2h "${command[@]}";;
esac
