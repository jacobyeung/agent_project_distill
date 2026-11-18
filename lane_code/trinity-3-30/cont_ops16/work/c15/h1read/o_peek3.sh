export TZ=UTC
timeout 100 srun --overlap --jobid 171112 -n1 --cpus-per-task=1 --mem=2G bash -c 'tail -n 2 /tmp/a_171112_a5f07824bb3/staging.log; ls -la /tmp/a_171112_a5f07824bb3/sj/aa5f07824bb3/r/a7/a0/results/0/ 2>&1 | tail -3; G=/tmp/a_171112_a5f07824bb3/sj/aa5f07824bb3/r/a7/a0/results/0/g0.jsonl; python3 - $G <<"PY"
import json,sys,collections
rows=[]
for l in open(sys.argv[1]):
    try: rows.append(json.loads(l))
    except Exception: pass
ids=collections.defaultdict(list)
for r in rows: ids[r["id"]].append(r)
done={i:v for i,v in ids.items() if any(x.get("status")=="complete" for x in v)}
t=collections.Counter(); s=collections.Counter(); n=collections.Counter()
for i,v in ids.items():
    q=v[0].get("question_type"); n[q]+=1; s[q]+=sum(float(x.get("seconds") or 0) for x in v)
    if i in done: t[q]+=1
print("LINES",len(rows),"IDS",len(ids),"ANSWERED",len(done),"FRAC %.3f"%(len(done)/1781), "statuses",collections.Counter(x.get("status") for x in rows))
for q in sorted(n): print("TYPE %-28s ids %4d done %4d sec_per_id %.1f"%(q,n[q],t[q],s[q]/max(n[q],1)))
PY' 2>&1 | tail -20
