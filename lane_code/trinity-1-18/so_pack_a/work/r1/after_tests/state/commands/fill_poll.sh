#!/bin/bash
set -euo pipefail
umask 077
export PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung CUDA_VISIBLE_DEVICES=
trap 'rc=$?; if [ "$rc" != 0 ]; then printf "phase exit %s line %s\n" "$rc" "$LINENO" >&2; fi' EXIT
cd /project/community/jjyeung/okh7/a15_cot_apb635a315de01e
if test -f a/1.txt; then test "$(cat a/1.txt)" = 0; printf "complete\n"; elif test -f a/f.exit; then tail -c 8192 a/f.log >&2; exit 1; else printf "wait\n"; tail -c 8192 a/f.log >&2; fi
