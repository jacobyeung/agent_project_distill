/usr/bin/python3 -I - <<'PY'
import hashlib, json, statistics as st
p='/project/community/jjyeung/okh7/x_07ca49df/runs/469ddece/metrics_169097.jsonl'
h=hashlib.sha256(); rows={}; n=0; size=0
with open(p,'rb') as f:
    for line in f:
        h.update(line); size+=len(line); n+=1
        if b'"step": 5' in line[:40] or True:
            try: r=json.loads(line)
            except ValueError: continue
            if 530<=r.get('step',0)<=544:
                ranks=r['ranks']; assert sorted(k['rank'] for k in ranks)==[0,1,2,3] and all(k['step']==r['step'] for k in ranks)
                rows[r['step']]={s: sum(k['stream_means'][s] for k in ranks)/4 for s in ('pose','vqa','routing','pointing')}
                rows[r['step']]['skipped']=sum(len(k.get('skipped_microsteps') or []) for k in ranks)
out={'bytes':size,'lines':n,'sha256':h.hexdigest(),'steps':sorted(rows)}
base={}
for s in ('pose','vqa','routing','pointing'):
    x=[rows[k][s] for k in sorted(rows)]; m=st.median(x); d=st.median([abs(v-m) for v in x]); base[s]=[m,d]
out['baseline']=base; out['skipped']=sum(rows[k]['skipped'] for k in rows)
print(json.dumps(out))
PY
