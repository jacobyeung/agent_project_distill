#!/bin/bash
# Streamed, governor-registered copy of the files named in LIST (absolute /data* paths) into DEST:
#   tar_reader.py LIST | pv -L RATE | tar xf - -C DEST
# The reader stops itself before opening any source file; this script registers the stopped pipeline with the central
# IO governor (tier 3, kind copy, with pv_pid, expected_bytes and io weights) and leaves it stopped: the governor
# admits it (CONT) and sets the pv rate live (pv -R) up to the tier headroom; RATE is only the starting rate.
# usage: stream_copy.sh LIST DEST RATE NAME NOMINAL_MBPS   (RATE in pv units, e.g. 200k)
set -uo pipefail
list=$1 dest=$2 rate=$3 name=$4 nominal=$5
code=$(dirname "$(readlink -f "$0")")
tmp=$(mktemp -d /tmp/jjyeung_rung1_sc.XXXXXX)
expected=$(/usr/bin/python3 -c 'import os, sys; print(sum(os.path.getsize(l.strip()) for l in open(sys.argv[1]) if l.strip() and os.path.exists(l.strip())))' "$list")
mkdir -p "$dest"
( /usr/bin/python3 "$code/tar_reader.py" "$list" "$tmp/reader.pid" | pv -q -L "$rate" -P "$tmp/pv.pid" | tar xf - -C "$dest" ) &
pipe=$!
for i in $(seq 1 60); do
  [ -s "$tmp/reader.pid" ] && [ -s "$tmp/pv.pid" ] && grep -q '^State:.*T' /proc/$(cat "$tmp/reader.pid")/status 2>/dev/null && break
  sleep 1
done
reader=$(cat "$tmp/reader.pid"); pvpid=$(cat "$tmp/pv.pid")
sink=$(pgrep -u "$(id -u)" -P "$pipe" -x tar | head -1)
/usr/bin/python3 "$code/gov_register.py" "$name" 3 copy "$nominal" "$expected" "$pvpid" "$reader" "$pvpid" "$sink" || { echo "REGISTER_FAILED"; kill -TERM "$reader"; kill -CONT "$reader"; exit 5; }
echo "$(date +%T) registered $name reader=$reader pv=$pvpid expected_bytes=$expected; waiting for the governor to admit it"
wait $pipe
rc=$?
echo "$(date +%T) stream_copy rc=$rc files=$(wc -l < "$list")"
exit $rc
