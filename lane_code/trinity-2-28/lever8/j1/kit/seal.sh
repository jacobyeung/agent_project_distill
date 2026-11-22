#!/bin/bash
# Writes j1/SHA256SUMS_J1: the kit (code and tests), the served source copies, the scipy overlay, the frame and prompt indexes and
# every anchor PNG copy. REPORT_J1.md, work/ and the outputs under out/detect are not sealed. NUL-separated (scipy has file names
# with spaces).
set -eu
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
{ printf '%s\0' kit/*.py kit/*.sh kit/tests/*; find served pyextra frames -type f -print0; printf '%s\0' out/FRAMES_J1.json out/PROMPTS_J1.json; } \
  | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS_J1.tmp
mv SHA256SUMS_J1.tmp SHA256SUMS_J1; wc -l < SHA256SUMS_J1
