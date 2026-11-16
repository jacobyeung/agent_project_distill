#!/usr/bin/env bash
set -euo pipefail
EA_GPU=${1:?Usage: bash out/run_EA_phase.sh GPU PHASE}
EA_PHASE=${2:?Usage: bash out/run_EA_phase.sh GPU PHASE}
if [[ $(hostname -s) != trinity-1-18 || $EA_GPU != 7 ]]; then
  echo 'This run is assigned to trinity-1-18 GPU 7.' >&2
  exit 2
fi
EA_LANE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
export EA_ROOT=${EA_ROOT:-/scratch/jjyeung/ownenc_EA_r3}
export EA_RESULTS=${EA_RESULTS:-$EA_ROOT/results}
export EA_FEATURES=${EA_FEATURES:-/dev/shm/jjyeung_probe_r3/feats}
export EA_WEIGHTS=${EA_WEIGHTS:-$EA_LANE/out/WEIGHTS.gpu.json}
export EA_LEDGER=${EA_LEDGER:-$EA_ROOT/GPU_TIME.json}
export CUDA_VISIBLE_DEVICES=$EA_GPU
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
export PYTHONPATH=$EA_LANE/work:$EA_LANE/out
export XDG_CACHE_HOME=$EA_ROOT/cache HF_HOME=$EA_ROOT/hf TRITON_CACHE_DIR=$EA_ROOT/triton
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
cd "$EA_LANE"
if [[ $EA_PHASE == 1 ]]; then
  EA_ARMS=(A1 A7 A2)
elif [[ $EA_PHASE == 2 ]]; then
  if [[ ! -f $EA_ROOT/PHASE1_COMPLETE.json ]]; then
    echo 'Phase 2 requires the completed phase-1 card.' >&2
    exit 2
  fi
  nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python work/phase_complete.py --verify "$EA_ROOT/PHASE1_COMPLETE.json"
  EA_ARMS=(A3 A5 A6 A4 A8)
else
  echo 'Phase must be 1 or 2.' >&2
  exit 2
fi
for EA_ARM in "${EA_ARMS[@]}"; do
  if [[ $EA_ARM == A8 ]]; then EA_PHASES=T1,T4; else EA_PHASES=smoke,extract,T1,T4; fi
  bash out/run_EA_arm.sh "$EA_GPU" "$EA_ARM" --phases "$EA_PHASES"
  if [[ ! -f $EA_RESULTS/$EA_ARM/T1.done.json || ! -f $EA_RESULTS/$EA_ARM/T4.done.json ]]; then
    if [[ -f $EA_RESULTS/$EA_ARM/SKIPPED.json ]]; then continue; fi
    break
  fi
  for EA_READOUT in final unstandardized; do
    bash out/run_EA_arm.sh "$EA_GPU" "$EA_ARM" --readout "$EA_READOUT" --phases T1,T4
    if [[ ! -f $EA_RESULTS/$EA_ARM/$EA_READOUT/T1.done.json || ! -f $EA_RESULTS/$EA_ARM/$EA_READOUT/T4.done.json ]]; then break 2; fi
  done
done
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python work/card.py --results "$EA_RESULTS" --out "$EA_ROOT/card"
if [[ $EA_PHASE == 1 ]]; then
  nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python work/phase_complete.py --results "$EA_RESULTS" --out "$EA_ROOT/PHASE1_COMPLETE.json"
fi
