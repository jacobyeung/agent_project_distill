export TZ=UTC; date -u +%FT%TZ
J=172456
timeout 100 srun --jobid=$J --overlap -n1 -c1 --mem=1G bash -c '
P=$(pgrep -f "boot.py -B -I 5.py 40.json" | head -1); echo PID $P
E=/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/19252904/e/bin
ls $E | grep -i spy; which py-spy 2>/dev/null
R=$(ls -d /tmp/a'$J'*/sj/b01ec87a6f29b/r); J4=$R/metadata/reads/0/metadata/journals/4/0
wc -l $J4/items.jsonl; ls -la --time-style=+%T $J4/items.jsonl
python3 -c "
import json
m=json.load(open(\"$J4/item_mapping.json\")); print(list(m)); it=m[\"items\"]; print(len(it)); 
done=set(json.loads(l)[\"id\"] for l in open(\"$J4/items.jsonl\"))
nxt=[x for x in it if x.get(\"id\",x.get(\"item_id\")) not in done][:2]
print([{k:(str(v)[:80]) for k,v in x.items() if k!=\"anchor_indices\"} for x in nxt])
"
cat /proc/$P/io 2>/dev/null
' 2>&1 | tail -40
