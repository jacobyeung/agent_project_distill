import sqlite3,json,collections
db=sqlite3.connect('file:/scratch/jjyeung/orch_n30/rows_a2/vsti/out/vsti_rel_v3/rows.sqlite?mode=ro',uri=True)
rows=[json.loads(t) for (t,) in db.execute('select row from rows order by i')]
print(len(rows))
c=collections.Counter()
for r in rows:
    p=r['provenance'];a=p['geometry_audit']
    import os
    c[(r['dataset'],os.path.dirname(p['raster']).replace('/scratch/jjyeung/orch_n30/',''),a['box_half_factor'])]+=1
for k,v in sorted(c.items()):print(k,v)
r=rows[0];print(json.dumps(r,indent=1)[:4000])
