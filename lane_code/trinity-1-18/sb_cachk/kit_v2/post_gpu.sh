#!/usr/bin/env bash
# After the GPU pass (CPU, on the node that holds out/v2/track): price every carried set, then the summary and report.
#   bash kit_v2/post_gpu.sh
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$KIT")"
# Validate every output before any arm is priced, so a rerun cannot partially write.
PY=/scratch/jjyeung/envs/p1cpu/bin/python
PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 "$PY" -B -S - "$KIT" "$ROOT/out/v2" <<'GUARD'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from mc_score_guard import check
root = Path(sys.argv[2])
check(root, [root])
for track in (root/'track').glob('S_*_*'):
    if track.is_dir():
        check(root, [root/'price'/track.name], capture_scores=True)
GUARD
for d in "$ROOT"/out/v2/track/S_*_*/; do
  d="${d%/}"
  [ -n "$(ls "$d"/*.json.gz 2>/dev/null | head -1)" ] || continue
  bash "$KIT/run_cpu.sh" p1cpu mc_price.py "$d" "$ROOT/out/v2/price/$(basename "$d")" all
done
bash "$KIT/run_cpu.sh" p1cpu mc_summary.py final
