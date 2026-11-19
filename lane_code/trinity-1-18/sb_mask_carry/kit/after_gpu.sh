#!/bin/bash
# CPU, after the GPU pass: price every tracked set through the ladder, then measures, bars and decision.
#   bash kit/after_gpu.sh
# Sets the pass dropped or did not finish price with missing tracks and are left out of the bars (mc_decide).
set -eu
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$KIT")"
for d in "$ROOT"/out/track/S_*_*/; do
  s="$(basename "$d")"
  bash "$KIT/run_cpu.sh" p1cpu mc_price.py "../out/track/$s" "../out/price/$s" all
done
bash "$KIT/run_cpu.sh" p1cpu mc_decide.py ../out/price ../out
