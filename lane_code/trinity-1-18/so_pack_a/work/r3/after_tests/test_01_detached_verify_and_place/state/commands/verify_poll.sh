#!/bin/bash
set -euo pipefail
umask 077
export PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung CUDA_VISIBLE_DEVICES=
trap 'rc=$?; if [ "$rc" != 0 ]; then printf "phase exit %s line %s\n" "$rc" "$LINENO" >&2; fi' EXIT
cd /project/community/jjyeung/okh7/a15_cot_apb635a315de01e
if test -f v/0.txt; then test "$(cat v/0.txt)" = 0; printf "complete\n"; elif test -f v/0.exit; then tail -c 8192 v/0.log >&2; exit 1; else printf "wait\n"; tail -c 8192 v/0.log >&2; fi
