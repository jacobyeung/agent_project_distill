#!/usr/bin/env bash
# out/v2/KIT_MANIFEST.sha256: the kit code and the CPU-built inputs the GPU pass reads; launch_gpu.sh checks it.
#   bash kit_v2/manifest.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
sha256sum kit_v2/*.py kit_v2/*.sh kit_v2/vendor/*.sh kit_v2/tests/*.py out/v2/BARS_FROZEN.json out/v2/BARS_AMENDMENT.json \
  out/v2/POPULATION.json in/RULING_1056Z.md out/v2/GUARD.json out/v2/FRAME_SETS.json \
  out/v2/seeds/SEEDS.json out/v2/seeds/*.npz > out/v2/KIT_MANIFEST.sha256.tmp
mv out/v2/KIT_MANIFEST.sha256.tmp out/v2/KIT_MANIFEST.sha256
wc -l < out/v2/KIT_MANIFEST.sha256
