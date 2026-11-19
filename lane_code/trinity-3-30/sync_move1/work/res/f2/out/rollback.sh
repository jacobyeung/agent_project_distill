#!/bin/bash
set -eu
: "${B:?Set B to the orch_n30 directory}"
: "${S:?Set S to the sync state directory}"
if [ "$#" -ne 1 ]; then
    echo 'Usage: B=<orch_n30 dir> S=<sync state dir> bash -eu rollback.sh <backup dir>' >&2
    exit 2
fi
P=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export CUDA_VISIBLE_DEVICES=""
exec nice -n 10 /usr/bin/python3 -I -s -B "$P/install_tools.py" rollback "$P" "$B" "$S" "$1"
