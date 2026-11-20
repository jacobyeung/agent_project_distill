export TZ=UTC; J=/project/community/jjyeung/4f5e45fe5d74c
squeue -u jjyeung -o '%i %j %P %T %M %R'
for f in $J/log/*.out; do echo "== $f"; tail -20 $f; done
tail -5 $J/runner.log 2>/dev/null; wc -l $J/out/*.jsonl $J/meter/CALLS.jsonl 2>/dev/null; cat $J/meter/METER.json 2>/dev/null; ls $J/ev $J/faults
