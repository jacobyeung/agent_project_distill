#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
O=/project/community/jjyeung/okh7
BUN=$O/i_7f1589c1
H=$O/x_3fdda0fb
OLD=$O/i_1be16f28
KH=$O/x_7f1589c1
private() { [[ -d "$1" && ! -L "$1" && $(stat -c %a "$1") == 700 ]] || { echo "REFUSED: private directory required: $1" >&2; exit 3; }; }
fresh() { [[ ! -e "$1" && ! -L "$1" ]] || { echo "REFUSED: already exists: $1" >&2; exit 3; }; }
packet() { printf '%s  %s\n' '08f3a7b2ef2e1923ba77b464afcedbbe668a77a1915b4c32c0a815044ff7d9fd' "$BUN/p.tar" | sha256sum -c --quiet; }
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
