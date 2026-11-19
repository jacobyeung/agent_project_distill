cd /lab_data/tarrlab/jacoby/agent_project/aws_evac/_direct || exit 1
P='97a6a3eb|f2ad01ad|8865619b|5e1d07a4|1742c666|f02f16ad'
head -c 600 map/0229bad09af8.json; echo
python3 - <<'PY'
import json,glob,re
P=re.compile(r'(97a6a3eb|f2ad01ad|8865619b|5e1d07a4|1742c666|f02f16ad)')
for f in sorted(glob.glob('map/*.json')):
    s=open(f).read()
    if not P.search(s): continue
    d=json.loads(s)
    tok=f[4:-5]
    ok='ok' if glob.glob('ok/'+tok+'.json') else ('bad' if glob.glob('bad/*/'+tok+'*') or glob.glob('bad/'+tok+'*') else 'none')
    keys=list(d) if isinstance(d,dict) else type(d).__name__
    dest=d.get('dest') if isinstance(d,dict) else None
    srcs=[]
    def walk(x):
        if isinstance(x,str):
            if P.search(x): srcs.append(x)
        elif isinstance(x,dict):
            for v in x.values(): walk(v)
        elif isinstance(x,list):
            for v in x: walk(v)
    walk(d)
    print(tok,ok,'dest=',dest,'keys=',keys[:8] if isinstance(keys,list) else keys,'n=',len(srcs))
    for x in srcs[:4]: print('   ',x[:220])
PY
