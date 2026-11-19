#!/usr/bin/env bash
# Run only after the coordinator supplies every MISSING.json target on local scratch.
set -euo pipefail
if [[ $# -ne 2 ]]; then
  echo 'Usage: bash coordinator228.sh <idle-card-index-or-UUID> <fresh-local-run-directory>' >&2
  exit 2
fi
date -u
if [[ "$(hostname -s)" != trinity-2-28 ]]; then
  echo 'REFUSED: coordinator228.sh is restricted to trinity-2-28' >&2
  exit 2
fi
kit_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
export HOME=/scratch/jjyeung/orch_n30/reads228/control_home
export XDG_CACHE_HOME=/scratch/jjyeung/orch_n30/reads228/control_cache
export CUDA_CACHE_PATH="$XDG_CACHE_HOME/nv" MPLCONFIGDIR="$XDG_CACHE_HOME/mpl"
export HF_HOME="$XDG_CACHE_HOME/hf" TRITON_CACHE_DIR="$XDG_CACHE_HOME/triton"
export USER=jjyeung LOGNAME=jjyeung PATH=/usr/local/bin:/usr/bin:/bin
unset LD_LIBRARY_PATH
mkdir -p "$HOME" "$XDG_CACHE_HOME" "$CUDA_CACHE_PATH" "$MPLCONFIGDIR" "$HF_HOME" "$TRITON_CACHE_DIR"
package="$kit_dir/A10b"
# All extraction uses the target system Python 3.6.8; it imports no ML libraries.
nice -n 10 /usr/bin/python3 -I -s -B "$kit_dir/stage228.py" "$package" --extract-runtime
date -u
nice -n 10 /usr/bin/python3 -I -s -B "$kit_dir/stage228.py" "$package" --extract-inputs
date -u
nice -n 10 /usr/bin/python3 -I -s -B "$kit_dir/stage228.py" "$package" --relocate-runtime
date -u
nice -n 10 /usr/bin/python3 -I -s -B "$kit_dir/stage228.py" "$package" --install-code
date -u
# Match the wrapper's Orchard invocation flags. No /envs/p1cpu is needed on 2-28.
export READ228_CONTROL_PYTHON=/scratch/jjyeung/b01ec87a6f29b/d/v/py
nice -n 10 "$READ228_CONTROL_PYTHON" -B -I "$kit_dir/stage228.py" "$package" --prepare
date -u
nice -n 10 "$READ228_CONTROL_PYTHON" -B -I "$kit_dir/stage228.py" "$package" --out /scratch/jjyeung/orch_n30/reads228/STAGE_CHECK.json
date -u
# run228 performs stage_check(prepare=True), then the two >=300-second idle readings,
# then exactly the requested first 50 commits. A busy card exits; there is no wait/retry loop.
bash "$kit_dir/run228.sh" "$package" "$1" "$2" --items 50
date -u
bash "$kit_dir/compare228.sh" "$2/ret" --orchard "$kit_dir/reference" --out "$2/COMPARE.json"
date -u
