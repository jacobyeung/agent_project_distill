export TZ=UTC
K=/project/community/jjyeung/okh7/x_07ca49df
echo "## runs"; ls -la --time-style=+%FT%TZ $K/runs; ls -la --time-style=+%FT%TZ $K/runs/469ddece | head -40
/usr/bin/python3 -I - <<'PY'
import json, os, statistics as st
K='/project/community/jjyeung/okh7/x_07ca49df'
s=json.load(open(K+'/sess.json'))
print('## sess keys', len(s))
for k in sorted(s):
    v=s[k]; f=sorted(v.keys()) if isinstance(v,dict) else type(v).__name__
    extra={x:v[x] for x in (v if isinstance(v,dict) else {}) if any(t in x.lower() for t in ('creat','expir','time','minted','size','bytes'))}
    print(k, f, extra)
p=K+'/runs/469ddece/metrics_169097.jsonl'
if os.path.exists(p):
    sz=os.path.getsize(p); print('## metrics bytes', sz)
    with open(p,'rb') as h:
        first=h.readline()
        h.seek(max(0,sz-6_000_000)); h.readline(); tail=h.read().splitlines()
    r1=json.loads(first); print('row1 keys', sorted(r1.keys())[:40]); print('rank0 keys', sorted(r1['ranks'][0].keys())[:60])
    rows=[json.loads(x) for x in tail if x.strip()]
    out=[]
    for r in rows:
        if r['step']<520: continue
        sm={}
        for st_ in r['ranks'][0].get('stream_means',{}):
            vals=[rk['stream_means'][st_] for rk in r['ranks'] if rk.get('stream_means',{}).get(st_) is not None]
            sm[st_]=round(sum(vals)/len(vals),5) if vals else None
        o={'step':r['step'],'sm':sm}
        for key in ('wall_seconds','data_seconds','lr','loss','grad_norm','time','utc'):
            if key in r: o[key]=r[key]
            elif key in r['ranks'][0]: o[key]=r['ranks'][0][key]
        out.append(o)
    print('## tail rows'); [print(json.dumps(o)) for o in out]
    print('## r1 sample', json.dumps({k:r1[k] for k in r1 if k!='ranks'})[:600])
    print('## rank0 sample', json.dumps({k:v for k,v in r1['ranks'][0].items() if not isinstance(v,(dict,list))})[:800])
PY
echo "## end"
