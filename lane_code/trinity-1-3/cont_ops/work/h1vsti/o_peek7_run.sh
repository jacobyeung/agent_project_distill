export TZ=UTC; J=172475; T=acb2faedd41
timeout 100 srun --overlap --jobid $J -n1 --cpus-per-task=1 --mem=2G bash -c 'B=/tmp/a_'$J'_'$T'; cd $B/sj/a'$T'/r/r6 && find . -maxdepth 5 | head -20; for g in $(find . -name "g*.jsonl" | head -3); do echo "$g $(wc -l < $g)"; done' 2>&1 | tail -25
