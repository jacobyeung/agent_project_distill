K=/scratch/jjyeung/orch_n30/nvkey1/work
date -u +%FT%TZ
tmux ls 2>&1 | grep -E 'nvk|codex' 
tail -5 $K/runner.log
cat $K/meter/METER.json; echo
wc -l $K/out/*.jsonl
ls $K/queue $K/ctl $K/faults 2>&1
for f in $K/ctl/*; do echo "$f=$(cat $f 2>/dev/null | head -c 100)"; done
ls $K/c2 $K/scores 2>&1
df -h /scratch | tail -1
uptime
