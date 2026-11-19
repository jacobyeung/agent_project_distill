cd /tmp && nice -n 10 python3 - <<'P'
import sqlite3,json,random,re
c=sqlite3.connect('file:/project/community/jjyeung/okh7/7c9f2d84/rows.sqlite?mode=ro&immutable=1',uri=True)
ids=sorted(random.Random(20261119).sample(range(25020),40))
pat=re.compile(r'^<think>\s*</think>\s*\{"point_2d": (null|\[\d+, \d+\])\}$')
n=0
for i in ids:
    row,target=c.execute("select row,target from rows where i=?",(i,)).fetchone(); r=json.loads(row)
    t=r.get('target',''); m=bool(pat.match(t)); n+=m
    print(i, r.get('qid'), r.get('question_type'), r['pointing'].get('kind'), 'EMPTY_THINK_JSON' if m else 'OTHER', repr(t[:80]), repr(target[:60]))
print('ids',ids); print('empty_think_json',n,'of',len(ids))
P
