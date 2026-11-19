F=/scratch/jjyeung/orch_n30/fb_pack/point/out; head -40 $F/REPORT.md | cut -c1-600; echo ==PIN; head -c 2500 $F/PIN_CHANGE.md; echo
/scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
import sqlite3,random,json
c=sqlite3.connect('file:/scratch/jjyeung/orch_n30/fb_pack/point/out/rows_pointing_locate.sqlite?mode=ro',uri=True)
t=[r[0] for r in c.execute("select name from sqlite_master where type='table'")]; print(t)
tab=t[0]; cols=[r[1] for r in c.execute(f"pragma table_info({tab})")]; print(cols)
n=c.execute(f"select count(*) from {tab}").fetchone()[0]; print('rows',n)
random.seed(11); ids=sorted(random.sample(range(n),40))
for i in ids:
    r=dict(zip(cols,c.execute(f"select * from {tab} limit 1 offset {i}").fetchone()))
    s=json.dumps(r)[:2000]
    # try to find question/target
    q=None;tg=None
    for k,v in r.items():
        if isinstance(v,str) and 'Point to' in v: q=v
        if isinstance(v,str) and '<think>' in v: tg=v
        if isinstance(v,str) and v.startswith('{') and ('Point to' in v or '<think>' in v):
            try:
                d=json.loads(v); q=q or d.get('question'); tg=tg or d.get('target')
            except Exception: pass
    import re
    qq=re.search(r'Point to the (.*?) in frame (\d+)', s); 
    tt=re.search(r'<think>\\\\n(.*?)\\\\n</think>\\\\n\\\\n(.{0,40})', s) or re.search(r'<think>(.*?)</think>(.{0,40})', s)
    print(i,'|Q:',qq.group(0) if qq else None,'|T:',tt.group(1)[:120] if tt else None,'|A:',tt.group(2)[:40] if tt else None)
PY
