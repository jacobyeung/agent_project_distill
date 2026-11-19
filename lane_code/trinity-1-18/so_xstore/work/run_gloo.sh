#!/bin/bash
# Optional existing native baseline only. This is NOT prepare/adopt equivalence.
set -euo pipefail
cd /scratch/jjyeung/orch_n30/so_xstore
date -u
source work/env.sh
exec nice -n 10 "$XSTORE_PYTHON" -I -s -B work/run_gloo.py
