import sqlite3,sys,glob,json,os
Q='/tmp/q_22c714e1_173626/s/aws/u/ap'
fs=[f for f in sorted(glob.glob(Q+'/**/rows.sqlite',recursive=True)) if os.path.getsize(f)>=50e6]
seen=set()
for f in fs:
  c=sqlite3.connect('file:'+f+'?mode=ro&immutable=1',uri=True)
  try:
    n=c.execute('select max(i) from rows').fetchone()[0]
    g=c.execute("select json_extract(row,'$.dataset'),json_extract(row,'$.category'),count(*) from (select row from rows limit 3000) group by 1,2").fetchall()
  except Exception as e: print(f[len(Q):],'ERR',e); continue
  print(f[len(Q):],os.path.getsize(f)//10**6,'MB maxi',n,g[:12])
  for (r,) in c.execute('select row from rows limit 3000'):
    d=json.loads(r); k=(d.get('dataset'),d.get('category'))
    if k in seen: continue
    cat=str(k[1]).lower()
    if any(w in cat for w in ('dist','count','rout')):
      seen.add(k); si=d.get('student_input'); s=json.dumps(si)[:500] if not isinstance(si,str) else si[:500]
      print('SAMPLE',k,type(si).__name__,s.replace('\n',' '))
