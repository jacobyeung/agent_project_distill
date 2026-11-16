#!/usr/bin/env bash
# Set FRAMES, OUTPUT and CARD to node-local locations and one free GPU.
set -euo pipefail
ulimit -f 204800
KIT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
: "${FRAMES:?k6tk root}" "${OUTPUT:?output directory}" "${CARD:?one GPU index}"
NATIVE=${NATIVE:-/scratch/jjyeung/envs/sam3_capretry_native_v1}
CPU_ENV=${CPU_ENV:-/scratch/jjyeung/envs/p1cpu}
FLA=${FLA:-/scratch/jjyeung/orch_cd/mdg_build/work/fla/site}
BUNDLE=${BUNDLE:-/scratch/jjyeung/orch_cd/mdg_build/work/t0bundle/BUNDLE.json}
CONFIG=${CONFIG:-/scratch/jjyeung/orch_cd/mdg_build/work/t0bundle/config.json}
ARTIFACT=${ARTIFACT:-/scratch/jjyeung/orch_cd/mdg_build/work/data/t0mind/ap/244cdf20/runs/e59f7158/m800/artifact.json@5e160dd8e6ebbdd0eb9170e9b6844bde7deeb394be28c4e4167293e4af7e686c}
MDG=${MDG:-/scratch/jjyeung/orch_cd/mdg_next/work/out/fb/stub_t0m800}
G3T=${G3T:-/dev/shm/jjyeung_mdg_next/g3t}
export TOWER_PYTHON="$NATIVE/bin/python"
export PYTHONPATH="$FLA:$NATIVE/lib/python3.12/site-packages:$CPU_ENV/lib/python3.12/site-packages"
exec bash "$KIT/devs1_tower.sh" --frame-root "$FRAMES" --out "$OUTPUT" --card "$CARD" --bundle "$BUNDLE" --t0-config "$CONFIG" --artifact "$ARTIFACT" --g3t-weights "$G3T" --mdg "$MDG" --mdg-root "$KIT/mdg_source" --vnice "$KIT/vnice/vnice.sh" "$@"
