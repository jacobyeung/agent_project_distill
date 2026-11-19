#!/usr/bin/env bash
# CPU runner: nice 10, 8 threads, under 40 GB virtual memory, no CUDA device visible.
# Usage: bash kit_v2/run_cpu.sh <p1cpu|sam3> <script.py> [args...]
set -euo pipefail
cd "$(dirname "$0")"
case "$1" in
  p1cpu) PY=/scratch/jjyeung/envs/p1cpu/bin/python ;;
  sam3) PY=/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python ;;
  *) echo "unknown interpreter $1" >&2; exit 2 ;;
esac
shift
ROOT="$(cd .. && pwd)"
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD"
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export XDG_CACHE_HOME="$ROOT/work/v2/cache" HF_HOME="$ROOT/work/v2/hf" TRITON_CACHE_DIR="$ROOT/work/v2/triton"
export MPLCONFIGDIR="$ROOT/work/v2/mpl" TMPDIR="$ROOT/work/v2/tmp" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
# Validate scoring destinations before creating the runner's temporary directory.
"$PY" -B -S - "$PWD" "$ROOT/out/v2" "$@" <<'GUARD'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from mc_score_guard import check
root, script, args = Path(sys.argv[2]), Path(sys.argv[3]).name, sys.argv[4:]
if script == 'mc_price.py':
    check(root, [args[1]], capture_scores=True)
elif script == 'mc_summary.py':
    check(root, [root/'dry' if args[0] == 'dry' else Path(args[2]) if len(args) > 2 else root])
elif script in ('mc_step0.py', 'mc_stubs.py'):
    check(root, [root/'dry'])
elif script == 'mc_seeds.py':
    check(root, [root/'seeds'])
elif script == 'mc_dryrun_report.py':
    check(root, [root])
elif script == 'mc_track_pass.py':
    dest = Path(args[args.index('--out')+1]) if '--out' in args else root/'track'
    check(root, [root, dest])
GUARD
mkdir -p "$TMPDIR"
ulimit -v 39000000
exec nice -n 10 "$PY" -B "$@"
