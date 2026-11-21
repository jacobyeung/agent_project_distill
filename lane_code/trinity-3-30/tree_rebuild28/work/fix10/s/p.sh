export TZ=UTC; date -u +%TZ
timeout 90 srun --overlap --jobid 174134 -N1 -n1 bash -c 'D=/tmp/a15_f10_174134; cat $D/run.out | cut -c1-300; for f in $D/ev_*.jsonl; do echo "== $f"; cut -c1-1500 $f | tail -25; done; for f in $D/log_*.txt; do echo "== $f"; grep -v "^EV " $f | tail -8 | cut -c1-600; done'
