#!/bin/bash
# usage: start_stream.sh NAME EXPECTED_BYTES DEST -- reader command...   (one governed stream; root is stopped before any payload IO)
set -u
NAME=$1; BYTES=$2; DEST=$3; shift 4
D=/scratch/jjyeung/orch_n30/b12_cntapp/work/streams
RL=/scratch/jjyeung/io_governor/ratelimit.py
mkdir -p "$DEST"; : > $D/$NAME.root; : > $D/$NAME.rlpid
( echo $BASHPID > $D/$NAME.root; kill -STOP $BASHPID; "$@" 2>>$D/$NAME.reader.err; echo "reader_exit $?" >> $D/$NAME.reader.err ) \
  | ( echo $BASHPID > $D/$NAME.rlpid; exec /usr/bin/python3 -s $RL -q -L 1000 -B 65536 2>>$D/$NAME.rl.err ) \
  | ( cd "$DEST" && tar xif - ) > $D/$NAME.writer.out 2>&1 &
for i in $(seq 50); do RLPID=$(cat $D/$NAME.rlpid 2>/dev/null); [ -s $D/$NAME.root ] && [ -n "$RLPID" ] && [ "$(cat /proc/$RLPID/comm 2>/dev/null)" = ratelimit ] && [ "$(awk '{print $3}' /proc/$(cat $D/$NAME.root)/stat 2>/dev/null)" = T ] && break; sleep 0.2; done
ROOT=$(cat $D/$NAME.root)
echo "root $ROOT state $(awk '{print $3}' /proc/$ROOT/stat) rl $RLPID comm $(cat /proc/$RLPID/comm)"
/usr/bin/python3 -s /scratch/jjyeung/io_governor/register.py --lane b12_cntapp_$NAME --pid $ROOT --member-pid $RLPID --rl-pid $RLPID --expected-bytes $BYTES --tier 3 --kind copy --nominal-mbps 8 --allow-resume --priority 15
wait
echo "exit $?" > $D/$NAME.done
