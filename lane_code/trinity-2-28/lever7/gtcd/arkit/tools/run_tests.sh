#!/bin/bash
# Rehearse stage_arkit_apple.sh (its own launcher line, ARKIT_TEST_DIR set) and decode_arkit.py against a local range server.
# usage: run_tests.sh NAME PORT FAULTS_JSON   (FAULTS_JSON '[]' for none)
set -u
A=/scratch/jjyeung/orch_n30/lever7/gtcd/arkit; PY=/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python
N=$1; PORT=$2; FAULTS=$3
T=$A/test/$N; mkdir -p "$T"
[ -e "$T/raw" ] && { echo "refused: $T used"; exit 2; }
echo "$FAULTS" > "$T/faults.json"
$PY -B $A/tools/make_synth.py "$T" "$PORT" || exit 2
mkdir -p "$T/www_srv"
timeout 900 $PY -I $A/tools/range_server.py "$T/www" "$PORT" "$T/faults.json" > "$T/server.out" 2>&1 &
SRV=$!; sleep 2
ARKIT_TEST_DIR=$T bash $A/stage_arkit_apple.sh > "$T/stage.log" 2>&1
echo "stage exit $?" >> "$T/stage.log"
kill $SRV 2>/dev/null
$PY -B $A/tools/decode_arkit.py --raw "$T/raw" --plan "$T/plan/PLAN_ARKIT.json" --frames "$T/frames" --rejected "$T/frames_rejected" \
   --manifest "$T/DECODE_ARKIT.json" --frames-gtc "$T/FRAMES_GTC_SYNTH.json" --workers 2 > "$T/decode.log" 2>&1
echo "decode exit $?" >> "$T/decode.log"
