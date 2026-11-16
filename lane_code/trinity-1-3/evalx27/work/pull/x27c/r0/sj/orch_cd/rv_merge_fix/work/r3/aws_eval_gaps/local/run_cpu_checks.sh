#!/bin/bash
set -euo pipefail
ulimit -f 204800
cd "$(dirname "$0")/.."
export TMPDIR=${TMPDIR:-$PWD/../tmp}
mkdir -p "$TMPDIR" checks
exec bash local/cpu.sh -m unittest discover -s tests -p 'test_*.py'
