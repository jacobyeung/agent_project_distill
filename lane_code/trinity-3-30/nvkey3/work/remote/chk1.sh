K=/scratch/jjyeung/orch_n30/nvkey1/work
cd $K || exit 1
date -u +%FT%TZ; hostname -s
echo "== tmux"; tmux ls
echo "== runner.log"; tail -8 $K/runner.log
echo "== meter"; cat $K/meter/METER.json; echo
echo "== ctl"; for f in $K/ctl/*; do echo "$f: $(head -c 200 $f)"; done
echo "== out 4x 5x"; wc -l $K/out/4*.jsonl $K/out/5*.jsonl
echo "== queue"; ls -la $K/queue/ | tail -20
echo "== queue_done"; ls $K/queue_done/ | tail -30
echo "== faults"; ls -la $K/faults/ | tail -20
echo "== chain.log"; tail -5 $K/v6/chain.log
echo "== kit sha"; sha256sum $K/kit/*.py | cut -c1-12,65-
echo "== v6 dir"; ls -la $K/v6/ | head -40
echo "== scores"; ls -la $K/scores/ | tail -30
echo "== df"; df -h /scratch | tail -1
echo "== io gov state"; head -30 /data3/jjyeung/orch_n13_20261026/io_governor/STATE.md 2>/dev/null
echo "== alloc"; tail -15 /data3/jjyeung/orch_n13_20261026/nv_slots/ALLOC.md 2>/dev/null
