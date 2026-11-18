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
packet() { printf '%s  %s\n' 'c60b901594843989b909cb785a5fdc9ad544ea0fdec8d78c63bf173e4f6e136c' "$BUN/p.tar" | sha256sum -c --quiet; }
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
python3 -B - <<'PYCODE'
import stat
from pathlib import Path
k=Path('/project/community/jjyeung/okh7/x_7f1589c1')
assert (k/'b').is_dir() and not (k/'b').is_symlink(), 'sealed code directory missing'
for p in [k/'b', *(k/'b').rglob('*')]:
 assert not p.is_symlink() and p.name!='__pycache__', 'linked code or bytecode'
 if p.is_dir():assert stat.S_IMODE(p.stat().st_mode)==0o500, 'code directory must be 0500'
print('PASS b/ and code subdirectories 0500; no __pycache__')
PYCODE
