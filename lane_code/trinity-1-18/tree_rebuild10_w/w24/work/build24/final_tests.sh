#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
date -u
R2_TREE="$PWD/work/tree24" nice -n 10 bash work/build21/run.sh work/build22/new_tests.py > work/build24/new22_complete.log 2>&1
R2_TREE="$PWD/work/tree24" nice -n 10 bash work/build21/run.sh work/build24/kit_tests.py > work/build24/kit_tests_complete.log 2>&1
nice -n 10 bash work/build21/run.sh work/build24/uploads.py > work/build24/uploads.log 2>&1
