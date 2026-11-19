#!/bin/bash
set -eu
: "${B:?Set B to the orch_n30 directory}"
: "${S:?Set S to the sync state directory}"
P=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export CUDA_VISIBLE_DEVICES=""
exec nice -n 10 /usr/bin/python3 -I -s -B "$P/install_tools.py" install "$P" "$B" "$S"
