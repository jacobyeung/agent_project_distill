#!/bin/bash
set -euo pipefail
umask 077
[[ $# -ge 4 ]] || { echo 'usage: run_tgcs.sh job sessions kit out [full]'; exit 2; }
export TG_JOB="$1" TG_SESS="$(realpath "$2")" TG_KIT="$(realpath "$3")"
mkdir -p "$4"
export TG_OUT="$(realpath "$4")" TG_FULL="${5:-}" TG_DIR="$(cd "$(dirname "$0")" && pwd)"
export TG_PY=/scratch/jjyeung/envs/p1cpu/bin/python
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
if [[ "$TG_FULL" == full ]]; then
  exec nice -n 10 unshare -Urm "$TG_PY" -I -s -B "$TG_DIR/driver.py"
fi
exec nice -n 10 "$TG_PY" -I -s -B "$TG_DIR/driver.py"
