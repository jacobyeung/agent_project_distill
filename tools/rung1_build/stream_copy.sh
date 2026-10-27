#!/bin/bash
# Streamed, rate-limited, governor-registered copy of the files named in LIST (absolute /data* paths) into DEST:
#   tar_reader.py LIST | pv -L RATE | tar xf - -C DEST
# The reader stops itself before opening any source file; this script registers the stopped pipeline with the central
# IO governor (tier 3, kind copy) under lane name NAME, then resumes it. A monitor drops pv to 1 kB/s while the IO meter
# (first 20 lines, TOTAL row, read + 2x write) reads above 6 MB/s and restores RATE once it reads under 5 MB/s.
# usage: stream_copy.sh LIST DEST RATE NAME NOMINAL_MBPS   (RATE in pv units, e.g. 200k)
set -uo pipefail
list=$1 dest=$2 rate=$3 name=$4 nominal=$5
code=$(dirname "$(readlink -f "$0")")
meter=/data3/jjyeung/orch_n13_20261026/io_meter/IO_USAGE.md
tmp=$(mktemp -d /tmp/jjyeung_rung1_sc.XXXXXX)
mkdir -p "$dest"
( /usr/bin/python3 "$code/tar_reader.py" "$list" "$tmp/reader.pid" | pv -q -L "$rate" -P "$tmp/pv.pid" | tar xf - -C "$dest" ) &
pipe=$!
for i in $(seq 1 60); do
  [ -s "$tmp/reader.pid" ] && [ -s "$tmp/pv.pid" ] && grep -q '^State:.*T' /proc/$(cat "$tmp/reader.pid")/status 2>/dev/null && break
  sleep 1
done
reader=$(cat "$tmp/reader.pid"); pvpid=$(cat "$tmp/pv.pid")
sink=$(pgrep -u "$(id -u)" -P "$pipe" -x tar | head -1)
/usr/bin/python3 "$code/gov_register.py" "$name" 3 copy "$nominal" "$reader" "$pvpid" "$sink" || { echo "REGISTER_FAILED"; kill -TERM "$reader"; kill -CONT "$reader"; exit 5; }
kill -CONT "$reader"
state=run
while kill -0 $pipe 2>/dev/null; do
  total=$(head -20 $meter 2>/dev/null | grep '^| TOTAL' | awk -F'|' '{print $5}' | tr -d ' ')
  if [ -n "$total" ]; then
    if [ $state = run ] && awk -v t="$total" 'BEGIN{exit !(t>6)}'; then
      pv -R "$pvpid" -L 1k 2>/dev/null && state=paused && echo "$(date +%T) pause meter=$total"
    elif [ $state = paused ] && awk -v t="$total" 'BEGIN{exit !(t<5)}'; then
      pv -R "$pvpid" -L "$rate" 2>/dev/null && state=run && echo "$(date +%T) resume meter=$total"
    fi
  fi
  sleep 30
done
wait $pipe
rc=$?
echo "$(date +%T) stream_copy rc=$rc files=$(wc -l < "$list")"
exit $rc
