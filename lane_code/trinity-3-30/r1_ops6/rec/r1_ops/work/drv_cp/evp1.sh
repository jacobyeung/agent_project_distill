#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
O=/project/community/jjyeung/okh7
BUN=$O/i_ee227714
H=$O/x_3fdda0fb
OLD=$O/i_1be16f28
KH=$O/x_ee227714
private() { [[ -d "$1" && ! -L "$1" && $(stat -c %a "$1") == 700 ]] || { echo "REFUSED: private directory required: $1" >&2; exit 3; }; }
fresh() { [[ ! -e "$1" && ! -L "$1" ]] || { echo "REFUSED: already exists: $1" >&2; exit 3; }; }
packet() { printf '%s  %s\n' '3233765535fc95eb34b876b2e96895b5f684bd8b4e6c5c93f9e23123d320317b' "$BUN/p.tar" | sha256sum -c --quiet; }
private "$O"
private "$BUN"
packet
test -f "$BUN/e0/pid"
if [[ ! -f "$BUN/e0/rc" ]]; then
  if kill -0 "$(cat "$BUN/e0/pid")" 2>/dev/null; then echo 'RUNNING e0'; else echo 'STOPPED without rc; do not relaunch'; fi
  tail -n 12 "$BUN/e0/o.log"
  exit 0
fi
rc=$(cat "$BUN/e0/rc")
tail -n 30 "$BUN/e0/o.log"
echo "e0 rc=$rc"
[[ "$rc" == 0 ]] || exit 4
