#!/bin/bash
# Freezes the kit: sha256 of every kit and test file and every kit output the GPU pass reads. launch_gpu.sh refuses on any difference.
set -eu
cd "$(dirname "${BASH_SOURCE[0]}")/.."
sha256sum kit/*.py kit/*.sh tests/*.py out/FRAME_SETS.json out/STAGING.json out/STAGING_FRAMES.txt out/seeds/SEEDS.json out/seeds/*.npz \
  > out/KIT_MANIFEST.sha256
wc -l < out/KIT_MANIFEST.sha256
