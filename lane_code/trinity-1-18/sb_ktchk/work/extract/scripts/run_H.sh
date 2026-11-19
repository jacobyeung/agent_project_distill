#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
bash scripts/cpu.sh code/process_guard.py freeze H
exec bash scripts/cpu.sh code/evaluate_v2.py heldout
