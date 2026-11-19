#!/bin/bash
# Saved owner script. Invoke with: bash -eu /path/to/so_syncfix/install.sh
date -u
export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
B=${B:-/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30}
S=${S:-/scratch/jjyeung/distill_sync}
PYTHON=${LCS_OWNER_PYTHON:-/usr/bin/python3}
PKG=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
[ "$(hostname -s)" = trinity-3-30 ] || { echo 'INSTALL REFUSED: wrong host' >&2; exit 2; }
cd "$PKG"
nice -n 10 sha256sum -c SHA256SUMS
# PREIMAGE requires the installed uncapped scanfix, including its exact scanner hash.
(cd "$B" && nice -n 10 sha256sum -c "$PKG/PREIMAGE.sha256")
nice -n 10 "$PYTHON" -I -s -B "$PKG/install_tools.py" "$PKG" "$B" "$S"
(cd "$B" && nice -n 10 sha256sum -c "$PKG/POSTIMAGE.sha256")
date -u
