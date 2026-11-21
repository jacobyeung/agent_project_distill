export TZ=UTC; date -u +%TZ
timeout 50 srun --overlap --jobid 174134 -N1 -n1 bash -c 'cd /tmp/a15_dbg_174134; echo "== f.json"; ls -la n2/p/q/f.json; python3 -I -B -c "
import json
d=json.load(open(\"n2/p/q/f.json\"))
print({k:(v if k!=\"records\" else len(v)) for k,v in d.items()})
for r in d[\"records\"]: print({k:r.get(k) for k in (\"step\",\"microstep\",\"rank\",\"stream\",\"index\",\"loss\",\"finite\",\"effective_tokens\")})
"; echo "== evb"; tail -n 2 n2/evb.jsonl | cut -c1-1500; echo "== c4b log tail"; tail -c 600 log/c4b.log | grep -v "^EV" | tail -5; echo "== post2"; grep "^EV" log/post2.log | tail -2 | cut -c1-600; ls -la live | cut -c1-90; echo "== eva"; tail -n 1 n2/eva.jsonl | cut -c1-200; ls -la n2/p/q/p/frames_4608*/r | tail -2 | cut -c1-100; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | tr "\n" ";"; echo; ps -u $(id -un) -o pid,etime,pcpu,rss,nlwp,comm,args --width 250 | grep -E "c4.py|post2" | grep -v grep | cut -c1-60,130-200'
squeue -j 174134 -h -o "%i %T %M %N"
