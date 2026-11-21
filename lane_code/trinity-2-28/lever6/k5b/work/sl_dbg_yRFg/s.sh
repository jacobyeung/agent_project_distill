#!/bin/bash
set -euo pipefail
umask 077
P=/scratch/jjyeung/orch_n30/lever6/k5b/work/sl_dbg_yRFg
test ! -e "$P/71.txt"
first=$(cat "$P/70.txt"); [[ "$first" =~ ^[0-9]+$ ]]
q=$(squeue -j "$first" -h -o '%i' 2>&1 | sed -n '/^[0-9]/p' || true)
test -z "$q"
st=$(TZ=UTC sacct -j "$first" -X -n -P -o State,NodeList | sed -n 1p)
if [[ "${st%%|*}" != COMPLETED ]]; then echo E51 >&2; exit 1; fi
node=${st#*|}
[[ "$node" =~ ^[A-Za-z0-9-]+$ ]]
echo REACHED
