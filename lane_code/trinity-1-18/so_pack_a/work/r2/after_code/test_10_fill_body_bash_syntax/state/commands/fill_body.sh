#!/bin/bash
set -euo pipefail
umask 077
export PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung CUDA_VISIBLE_DEVICES=
trap 'rc=$?; if [ "$rc" != 0 ]; then printf "phase exit %s line %s\n" "$rc" "$LINENO" >&2; fi' EXIT
cd /project/community/jjyeung/okh7/a15_cot_apb635a315de01e
trap 'rc=$?; if [ "$rc" != 0 ]; then printf "%s\n" "$rc" >a/f.exit; fi' EXIT
if then
/usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 02:30:00
printf "0\n" > a/1.txt
