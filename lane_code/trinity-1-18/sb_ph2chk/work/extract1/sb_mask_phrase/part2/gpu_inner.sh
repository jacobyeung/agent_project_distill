#!/usr/bin/env bash
set -euo pipefail
cd "$PART2_KIT"
exec "$PART2_PYTHON" -B part2/sam3_pass.py "$PART2_MODE" ${PART2_ALL_ALIASES:+--all-aliases}
