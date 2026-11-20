K=/scratch/jjyeung/orch_n30/nvkey1/work
date -u +%T; tail -2 $K/runner.log; cat $K/meter/METER.json; wc -l $K/out/*.jsonl | tail -6
grep -v '"status": 200' $K/meter/CALLS.jsonl | tail -3 | cut -c1-300
