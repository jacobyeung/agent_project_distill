#!/bin/bash
# Usage: run_focused.sh <tree> <proof_name> <log> [test names...]; defaults to the build-18 focused list plus frame tests.
set -u
W=/scratch/jjyeung/orch_n30/sb_f64
TREE=$1; NAME=$2; LOG=$3; shift 3
TESTS=("$@")
if [ ${#TESTS[@]} -eq 0 ]; then
  TESTS=(tests.test_r1_build18 tests.test_r1_build17 tests.test_r1_export17 tests.test_r1_build16 tests.test_r1_build15
    tests.test_r1_build14 tests.test_r2_build_n1 tests.test_r2_n1fix tests.test_r2_n1fix3 tests.test_r2_build12
    tests.test_r1_build13 tests.test_r2_build3.Build3.test_opener_export_keep_and_reset
    export_mutation17.HashTwin.test_same_size_shard_refuses tests.test_r2_build8_frames tests.test_carrier_c1_cp2)
fi
cd "$W/pkg"
R2_TREE="$TREE" B18_PROOF="$NAME" bash work/build18/run.sh work/build18/test18.py "${TESTS[@]}" > "$LOG" 2>&1
echo "EXIT $?" >> "$LOG"
