#!/bin/bash
D=/scratch/jjyeung/orch_n30/native_r2/work/streams; S=/data3/jjyeung/orch_n13_20261026/io_governor/streams
left="masks geometry numpy frames"
while [ -n "$left" ]; do n=""; for x in $left; do if [ -f $D/$x.done ]; then mv $S/native_r2_$x.json $S/native_r2_$x.done.$(date +%s); echo "$(date -u +%FT%TZ) $x $(cat $D/$x.done)" >> $D/chain.log; else n="$n $x"; fi; done; left=$n; sleep 30; done
echo "$(date -u +%FT%TZ) ALL DONE" >> $D/chain.log
