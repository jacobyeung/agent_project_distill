#!/bin/bash
set -euo pipefail
umask 077
export PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung CUDA_VISIBLE_DEVICES=
trap 'rc=$?; if [ "$rc" != 0 ]; then printf "phase exit %s line %s\n" "$rc" "$LINENO" >&2; fi' EXIT
P=/project/community/jjyeung/okh7/a15_cot_apb635a315de01e
J=$(cat "$P/a/4.txt")
[[ "$J" =~ ^[0-9]+$ ]]
if ! S=$(sacct -n -X -j "$J" -o State --parsable2); then printf "accounting unavailable for %s\n" "$J" >&2; exit 75; fi
printf "%s\n" "$S"
case "${S%%|*}" in COMPLETED|PENDING|RUNNING|CONFIGURING|COMPLETING|'') ;; *) tail -c 8192 "$P/a/4.err" "$P/a/4.log" >&2 || true ;; esac
