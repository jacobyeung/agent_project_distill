#!/bin/bash
# Streamed, rate-limited copy of the files named in LIST (absolute /data* paths) into DEST, keeping their full paths:
#   tar cf - -T LIST | pv -L RATE | tar xf - -C DEST
# A monitor drops pv to 1 kB/s while the IO meter (first 20 lines, TOTAL row, read + 2x write) reads above 6 MB/s and
# restores RATE once it reads under 5 MB/s.
# usage: stream_copy.sh LIST DEST RATE   (RATE in pv units, e.g. 200k)
set -uo pipefail
list=$1 dest=$2 rate=$3
meter=/data3/jjyeung/orch_n13_20261026/io_meter/IO_USAGE.md
pidfile=$(mktemp /tmp/jjyeung_rung1_pv.XXXXXX)
mkdir -p "$dest"
( tar cf - -T "$list" | pv -q -L "$rate" -P "$pidfile" | tar xf - -C "$dest" ) &
pipe=$!
state=run
while kill -0 $pipe 2>/dev/null; do
  total=$(head -20 $meter 2>/dev/null | grep '^| TOTAL' | awk -F'|' '{print $5}' | tr -d ' ')
  pid=$(cat "$pidfile" 2>/dev/null)
  if [ -n "$pid" ] && [ -n "$total" ]; then
    if [ $state = run ] && awk -v t="$total" 'BEGIN{exit !(t>6)}'; then
      pv -R "$pid" -L 1k 2>/dev/null && state=paused && echo "$(date +%T) pause meter=$total"
    elif [ $state = paused ] && awk -v t="$total" 'BEGIN{exit !(t<5)}'; then
      pv -R "$pid" -L "$rate" 2>/dev/null && state=run && echo "$(date +%T) resume meter=$total"
    fi
  fi
  sleep 30
done
wait $pipe
rc=$?
echo "$(date +%T) stream_copy rc=$rc files=$(wc -l < "$list")"
exit $rc
