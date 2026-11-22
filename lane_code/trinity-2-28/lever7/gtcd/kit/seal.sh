#!/bin/bash
# Writes lever7/gtcd/SHA256SUMS_GTCD: the kit (code and tests), the b seed copies and the dense manifest (each dense PNG is checked
# against DENSE_D.json by track.py on read). REPORT_GTCD.md is not sealed.
set -eu
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
{ ls kit/*.py kit/*.sh kit/tests/*; ls out/seeds_b/*; echo dense/DENSE_D.json; } | LC_ALL=C sort | xargs sha256sum > SHA256SUMS_GTCD.tmp
mv SHA256SUMS_GTCD.tmp SHA256SUMS_GTCD; wc -l < SHA256SUMS_GTCD
