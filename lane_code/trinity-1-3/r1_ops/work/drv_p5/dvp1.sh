#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
O=/project/community/jjyeung/okh7
BUN=$O/i_69d2930d
H=$O/x_3fdda0fb
OLD=$O/i_1be16f28
KH=$O/x_69d2930d
private() { [[ -d "$1" && ! -L "$1" && $(stat -c %a "$1") == 700 ]] || { echo "REFUSED: private directory required: $1" >&2; exit 3; }; }
fresh() { [[ ! -e "$1" && ! -L "$1" ]] || { echo "REFUSED: already exists: $1" >&2; exit 3; }; }
packet() { printf '%s  %s\n' '9dd2fbb77503ecee875d538ebaed933cc95ff286f76e5955fc2591f63e3f0192' "$BUN/p.tar" | sha256sum -c --quiet; }
private "$O"
private "$BUN"
packet
test -f "$BUN/d0/pid"
if [[ ! -f "$BUN/d0/rc" ]]; then
  if kill -0 "$(cat "$BUN/d0/pid")" 2>/dev/null; then echo 'RUNNING d0'; else echo 'STOPPED without rc; do not relaunch'; fi
  tail -n 12 "$BUN/d0/o.log"
  exit 0
fi
rc=$(cat "$BUN/d0/rc")
tail -n 30 "$BUN/d0/o.log"
echo "d0 rc=$rc"
[[ "$rc" == 0 ]] || exit 4
cat "$BUN/compare.json"
