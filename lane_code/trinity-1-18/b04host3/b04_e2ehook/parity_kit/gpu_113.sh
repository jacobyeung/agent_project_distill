#!/bin/bash
# GPU parity read on trinity-1-13 inside a bwrap view that shows /dev/shm/jjyeung at /scratch/jjyeung/b04shm
# (the sealed SAM 3 tower accepts only /scratch paths). Usage: bash gpu_113.sh CARD ARM RUN_NAME [KEYS_FILE]
set -u
CARD=$1; ARM=$2; NAME=$3; KEYS=${4:-}
mkdir -p /scratch/jjyeung/b04shm
bwrap --dev-bind / / --bind /dev/shm/jjyeung /scratch/jjyeung/b04shm \
  bash /scratch/jjyeung/b04shm/b04/host2/b04_e2ehook/parity_kit/gpu_inner.sh "$CARD" "$ARM" "$NAME" "$KEYS"
echo "gpu_113 exit $?"
