#!/usr/bin/env bash
# Run a command with work/<copy> bound at the kit root and the extracted payload read-only.
# Everything outside work/ is read-only, /tmp is private, /dev has no GPU nodes, nvidia-smi is the fake.
set -euo pipefail
W=/scratch/jjyeung/orch_n30/sb_ph2chk/work
K=/scratch/jjyeung/orch_n30/sb_ph2fix
copy=$1; shift
mkdir -p "$W/tmp"
exec nice -n 10 bwrap --ro-bind / / --dev /dev --tmpfs /dev/shm --tmpfs /tmp \
  --bind "$W" "$W" --bind "$W/$copy" "$K" --ro-bind "$W/extract/payload" "$K/payload" \
  --ro-bind "$W/fakebin/nvidia-smi" /usr/bin/nvidia-smi --chdir "$K" \
  --setenv OMP_NUM_THREADS 8 --setenv MKL_NUM_THREADS 8 --setenv OPENBLAS_NUM_THREADS 8 \
  --setenv TMPDIR "$W/tmp" --setenv FAKE_SMI_LOG "$W/logs/fake_smi_calls.txt" "$@"
