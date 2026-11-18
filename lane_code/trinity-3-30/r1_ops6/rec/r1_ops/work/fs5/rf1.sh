#!/bin/bash
export TZ=UTC
K=/project/community/jjyeung/okh7/x_7f1589c1/o
date -u +%FT%TZ
sacct -j 172467 -X -n -P -o JobID,State,ExitCode,Start,End,NodeList,Reason
ls -la --time-style=+%H:%M:%S $K | grep 172467
for f in $K/172467.rehearsal.out $K/172467.rehearsal.err; do echo "== $f"; [ -f $f ] && tail -c 4000 $f | sed -E 's#(https?://)[^ "]*#\1REDACTED#g'; done
[ -f $K/172467.rehearsal.json ] && { echo "== json"; head -c 6000 $K/172467.rehearsal.json; }
