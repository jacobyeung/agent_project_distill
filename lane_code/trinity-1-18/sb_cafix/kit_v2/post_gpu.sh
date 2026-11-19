#!/usr/bin/env bash
# After the GPU pass (CPU, on the node that holds out/v2/track): price every carried set, then the summary and report.
#   bash kit_v2/post_gpu.sh
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$KIT")"
for d in "$ROOT"/out/v2/track/S_*_*/; do
  d="${d%/}"
  [ -n "$(ls "$d"/*.json.gz 2>/dev/null | head -1)" ] || continue
  bash "$KIT/run_cpu.sh" p1cpu mc_price.py "$d" "$ROOT/out/v2/price/$(basename "$d")" all
done
bash "$KIT/run_cpu.sh" p1cpu mc_summary.py final
