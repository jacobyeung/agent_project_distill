export TZ=UTC; date -u +%FT%TZ
J=172456
timeout 90 srun --jobid=$J --overlap -n1 -c1 --mem=1G bash -c '
R=$(ls -d /tmp/a'$J'*/sj/b01ec87a6f29b/r); cd $R/metadata/reads/0/metadata/journals/4/0
ls -la --time-style=+%T . | head -20
tail -2 STEPS.jsonl | cut -c1-400
python3 -c "
import json
ids=[json.loads(l)[\"id\"] for l in open(\"items.jsonl\")]
m=json.load(open(\"item_mapping.json\")); print(type(m).__name__, len(m)); 
print(str(m)[:300])
print(len(ids), ids[-1])
"
P=$(pgrep -f "boot.py -B -I 5.py 40.json" | head -1); echo PID $P
cat /proc/$P/status | grep -E "State|Threads|VmRSS"
for t in $(ls /proc/$P/task | head -60); do echo "$(cat /proc/$P/task/$t/stat | cut -d" " -f3) $(cat /proc/$P/task/$t/comm) $(cat /proc/$P/task/$t/wchan 2>/dev/null)"; done | sort | uniq -c | sort -rn | head -12
ls -l /proc/$P/fd 2>/dev/null | awk "{print \$NF}" | grep -v "^/dev\|socket\|pipe\|anon" | tail -15
' 2>&1 | tail -60
