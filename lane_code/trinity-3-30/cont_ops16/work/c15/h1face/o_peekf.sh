export TZ=UTC
timeout 100 srun --overlap --jobid ${J:?} -n1 --cpus-per-task=1 --mem=2G bash -c 'B=/tmp/a_'$J'_'$T'; tail -n 2 $B/staging.log 2>&1; for f in away forward; do G=$B/sj/a'$T'/r/$f/a0/results/0/g0.jsonl; test -e $G && python3 - $G $f <<"PY"
import json,sys,collections
rows=[]
for l in open(sys.argv[1]):
    try: rows.append(json.loads(l))
    except Exception: pass
ids=collections.defaultdict(list)
for r in rows: ids[r["id"]].append(r)
done=sum(1 for v in ids.values() if any(x.get("status")=="complete" for x in v))
print(sys.argv[2],"LINES",len(rows),"IDS",len(ids),"ANSWERED",done,"statuses",dict(collections.Counter(x.get("status") for x in rows)))
PY
done; ls $B/sj/a'$T'/r/ 2>&1' 2>&1 | tail -12
