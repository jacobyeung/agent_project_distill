#!/bin/bash
set -eu
export CUDA_VISIBLE_DEVICES=""
P=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
for PYTHON in /usr/bin/python3 python3.12 python3.11; do
    if command -v "$PYTHON" >/dev/null 2>&1; then
        nice -n 10 "$PYTHON" -I -s -B "$P/tests/test_filter.py"
        nice -n 10 "$PYTHON" -I -s -B "$P/tests/test_round1.py"
        nice -n 10 "$PYTHON" -I -s -B "$P/tests/test_install.py"
        nice -n 10 "$PYTHON" -I -s -B "$P/tests/test_package.py"
    else
        echo "SKIP $PYTHON: unavailable on PATH"
    fi
done
nice -n 10 bash -n "$P/install.sh" "$P/rollback.sh" "$P/tests/run_all.sh"
echo 'PASS shell syntax'
