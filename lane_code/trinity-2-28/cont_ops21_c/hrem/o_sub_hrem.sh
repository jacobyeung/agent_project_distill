#!/bin/bash
set -euo pipefail
umask 077
: "${PARENT:?Set the full parent package path}"
: "${STAGE:?Set 813f42db/c21h544r, c21h200r or c21h400r}"
: "${STEP:?Set 200, 400 or 544}"
KROOT=/project/community/jjyeung/okh7
case "$STEP" in 200|400|544) ;; *) exit 1;; esac
[[ "$PARENT" =~ ^/project/community/jjyeung/okh7/a15_cot_ap[0-9a-f]+$ ]]
case "$STAGE" in 813f42db/*) STAGE="$KROOT/$STAGE";; esac
[[ "$STAGE" =~ ^/project/community/jjyeung/okh7/813f42db/[a-zA-Z0-9_-]+$ ]]
KIT="${STAGE}-kit"
export KROOT OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
/usr/bin/python3 -B -c "import os,sys;s=os.statvfs('$KROOT');f=s.f_bavail*s.f_frsize;print('FREE_GIB %.1f'%(f/1024**3));sys.exit(0 if f>=300*1024**3 else 3)" || { echo "REFUSE: project filesystem under 300 GiB free"; exit 3; }
mapfile -t SEALED < <(/usr/bin/python3 -B "$KIT/orchard_hrem.py" resolve --parent "$PARENT" --stage "$STAGE" --step "$STEP")
test "${#SEALED[@]}" = 2
export P="${SEALED[0]}" T="${SEALED[1]}"
exec bash "$KIT/sub_guard_hrem.sh"
