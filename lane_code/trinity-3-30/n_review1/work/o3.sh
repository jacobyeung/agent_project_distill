cd /tmp && nice -n 10 python3 - <<'P'
import sqlite3,json
c=sqlite3.connect('file:/project/community/jjyeung/okh7/7c9f2d84/rows.sqlite?mode=ro&immutable=1',uri=True)
print(c.execute("select sql from sqlite_master").fetchall())
print('max i',c.execute("select max(i) from rows").fetchone())
for i in (0,12345,25000):
    r=c.execute("select * from rows where i=?",(i,)).fetchone()
    if r is None: continue
    d=[x for x in r]
    for k,x in enumerate(d):
        if isinstance(x,str) and x.startswith('{'):
            o=json.loads(x)
            if isinstance(o,dict):
                si=o.get('student_input');
                if isinstance(si,dict): si.pop('frames',None); si.pop('frame_indices',None); si.pop('timestamps',None)
            d[k]=o
    print(i, json.dumps(d)[:2500])
P
