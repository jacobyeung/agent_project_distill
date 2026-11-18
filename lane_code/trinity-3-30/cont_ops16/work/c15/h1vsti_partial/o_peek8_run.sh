export TZ=UTC; J=172475; T=acb2faedd41
timeout 100 srun --overlap --jobid $J -n1 --cpus-per-task=1 --mem=2G bash -c 'B=/tmp/a_'$J'_'$T'; cd $B/sj/a'$T'/r/r6 && ls; for g in $(find . -path ./f0 -prune -o -name "*.jsonl" -print | head -5); do echo "$g $(wc -l < $g)"; done; tail -n 3 $B/staging.log 2>/dev/null; ls $B | head' 2>&1 | tail -25
