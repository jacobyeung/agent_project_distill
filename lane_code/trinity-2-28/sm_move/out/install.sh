#!/bin/bash
set -euo pipefail
: "${B:?Set B to the orch_n30 directory}" "${S:?Set S to the sync state directory}"
P=$(cd -- "$(dirname -- "$0")" && pwd)
exec nice -n 10 "${LCS_PYTHON:-python3}" -I -s -B "$P/install_tools.py" install "$P" "$B" "$S"
