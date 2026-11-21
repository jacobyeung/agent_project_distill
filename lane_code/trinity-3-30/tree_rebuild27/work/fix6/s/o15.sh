export TZ=UTC; date -u +%TZ
timeout 100 srun --overlap --jobid 174134 -N1 -n1 bash -c '
Q=/tmp/q_22c714e1_174134; F=$Q/p/q/f
echo "== p/q/f"; ls -la $F | head; for d in $F/*; do echo "-- $d: type $(stat -c %F $d) link $(readlink $d)"; ls -la $d | head -8; echo "   entries: $(ls $d | wc -l)"; done
echo "== data2root on the node (bound at the frame map target inside the sandbox)"; D2=$Q/s/c7d31ddd/data2root; stat -c "%F %N" $D2; ls -la $D2 | head -30
P=$D2/k6tk/f2/f25faedce4622416aed654d13ed347ed2a3b1ea0928a5674a80169324c6888cc.png
echo "== the frame"; ls -la $D2/k6tk 2>&1 | head -5; stat -c "%F %s %N" $P 2>&1; readlink -f $P 2>&1
for r in $F/*; do for sub in k6tk/f2 f2 k6tk; do [ -e $r/$sub ] && echo "   $r/$sub exists: $(ls $r/$sub | head -3 | tr "\n" " ")"; done; ls -la $r/k6tk/f2/f25faedce4622416aed654d13ed347ed2a3b1ea0928a5674a80169324c6888cc.png 2>&1 | head -2; done
echo "== u/4d66fc2a"; ls -la $Q/x/u 2>&1 | head -5; ls -la $Q/s/aws/u/ap/8865619b/u/4d66fc2a 2>&1 | head -8
echo "== old request"; cat $Q/p/q/p/request.json | head -c 900; echo
echo "== steps mentioning frames"; grep -i -E "frames|f3|f14|shard" $Q/174134.steps | head -20
cd /tmp/a15_dbg_174134; echo "== new request"; cat n2/p/q/p/request.json | head -c 700; echo; ls n2/p/q/p/; ls n2/p/q/p/prepare_*/prepared | head -20
'
