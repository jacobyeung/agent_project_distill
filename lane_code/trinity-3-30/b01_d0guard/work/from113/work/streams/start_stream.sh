#!/bin/bash
# usage: start_stream.sh NAME EXPECTED_BYTES OUTFILE -- reader command...
set -u
NAME=$1; BYTES=$2; OUT=$3; shift 4
D=/scratch/jjyeung/orch_n30/native_r2/work/streams
RL=/scratch/jjyeung/io_governor/ratelimit.py
( echo $BASHPID > $D/$NAME.root; kill -STOP $BASHPID; exec "$@" ) 2>>$D/$NAME.reader.err | /usr/bin/python3 -s $RL -q -L 1000 -B 65536 > "$OUT" 2>>$D/$NAME.rl.err &
RLPID=$!
echo $RLPID > $D/$NAME.rlpid
for i in $(seq 50); do [ -s $D/$NAME.root ] && [ "$(cat /proc/$RLPID/comm 2>/dev/null)" = ratelimit ] && [ "$(awk '{print $3}' /proc/$(cat $D/$NAME.root)/stat 2>/dev/null)" = T ] && break; sleep 0.2; done
ROOT=$(cat $D/$NAME.root)
echo "root $ROOT state $(awk '{print $3}' /proc/$ROOT/stat) rl $RLPID comm $(cat /proc/$RLPID/comm)"
/usr/bin/python3 -s /scratch/jjyeung/io_governor/register.py --lane native_r2_$NAME --pid $ROOT --member-pid $RLPID --rl-pid $RLPID --expected-bytes $BYTES --tier 3 --kind pull --nominal-mbps 8 --io-weight 1 --allow-resume --priority 20
wait
echo "exit $?" > $D/$NAME.done
