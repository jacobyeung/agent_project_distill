#!/bin/bash
# wait for the next watcher cycle (<=150 s), then print a compact reading
M=/scratch/jjyeung/orch_n30/n_ops1/work/mon; t0=$(stat -c %Y $M/hist.txt); for i in $(seq 1 30); do [ $(stat -c %Y $M/hist.txt) -gt $t0 ] && break; sleep 5; done
h=$(tail -1 $M/hist.txt); echo "$(echo "$h"|cut -c1-10) $(echo "$h" | grep -o '"state":"[^"]*"\|"stage":"[^"]*"\|"step":[^,]*\|"gpu_util":[^]]*]\|"gpu_mem_G":[^]]*]\|"ck":[^]]*]\|"gcs_done":[^]]*]' | tr '\n' ' ') $(echo "$h" | grep -o 'FLAG.*\|WARN.*')"
sed -n '/^@@LOG t.log/p;/^@@ERRS/p;/^@@TRAIN/,/^@@CK/p;/^@@CK/,/^@@CG/p' $M/last.raw | grep -v '^@@CG' | cut -c1-300 | tail -${1:-12}
