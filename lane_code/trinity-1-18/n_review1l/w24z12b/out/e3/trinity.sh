#!/bin/bash
set -euo pipefail
umask 077
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4
export PYTHONDONTWRITEBYTECODE=1
cap=$(ulimit -Hv)
if [[ "$cap" == unlimited || "$cap" -gt 15000000 ]]; then cap=15000000; fi
ulimit -v "$cap"
D=$(cd -- "$(dirname -- "$0")" && pwd)
PY=/scratch/jjyeung/envs/p1cpu/bin/python
if [[ ${1:-} == --namespace ]]; then
    [[ $# == 2 && ${E3_N:-} == "$2" ]] || exit 2
    R="$E3_N/root"
    mount --make-rprivate /
    mount -t tmpfs -o size=16m tmpfs "$R"
    for name in usr bin lib lib64 etc scratch dev proc; do
        if [[ -e /$name ]]; then
            mkdir -p "$R/$name"
            mount --rbind "/$name" "$R/$name"
        fi
    done
    mkdir -p "$R/project/community/jjyeung/okh7/x_22c714e1"
    exec chroot "$R" "$PY" -I -s -B "$D/trinity.py" --inside
fi
[[ $# == 3 && $1 =~ ^[0-9]+$ ]] || { echo "usage: trinity.sh job_id sessions_file out_dir"; exit 2; }
exec nice -n 10 "$PY" -I -s -B "$D/trinity.py" "$@"
