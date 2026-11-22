#!/bin/bash
# Writes lever7/gtcd/SHA256SUMS_GTCD_ARK: kit_ark (code and tests), the b seed copies and the ScanNet dense manifest (each dense
# PNG is checked against its manifest by track.py on read). The ARKit manifest is not sealed here: dense.py writes
# dense_ark/DENSE_D_ARK.json.sha256 beside it, and launch_gpu.sh checks that file. REPORT_GTCD*.md are not sealed.
set -eu
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
{ ls kit_ark/*.py kit_ark/*.sh kit_ark/tests/*; ls out/seeds_b/*; echo dense/DENSE_D.json; } | LC_ALL=C sort | xargs sha256sum > SHA256SUMS_GTCD_ARK.tmp
mv SHA256SUMS_GTCD_ARK.tmp SHA256SUMS_GTCD_ARK; wc -l < SHA256SUMS_GTCD_ARK
