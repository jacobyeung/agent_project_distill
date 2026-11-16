import json,collections,sqlite3
sg=json.load(open('/scratch/jjyeung/orch_n30/rows_a2/vsti/out/vsti_rel_v3/SOURCE_GEOMETRY.json'))
db=sqlite3.connect('file:/scratch/jjyeung/orch_n30/rows_a2/vsti/out/vsti_rel_v3/rows.sqlite?mode=ro',uri=True)
used=collections.Counter(json.loads(t)['provenance']['raster'] for (t,) in db.execute('select row from rows'))
print(len(sg),len(used))
for ds in ['scannet/','scannetpp','arkit']:
  for f in [0.5,1.0]:
    xs=[(k,v) for k,v in sg.items() if v['canonical'].startswith(ds) and v.get('passed') and v.get('box_half_factor')==f and k in used]
    if not xs: continue
    r=sorted(v['relative_extent_p98_median']['False'] for k,v in xs)
    c5=sorted(v['box_containment']['rows:0.5'] for k,v in xs)
    c1=sorted(v['box_containment']['rows:1.0'] for k,v in xs)
    q=lambda a:[round(a[int(i*(len(a)-1))],3) for i in (0,.1,.5,.9,1)]
    print(ds,f,len(xs),'ratio',q(r),'c0.5',q(c5),'c1',q(c1))
# examples d1 factor1
xs=[(k,v) for k,v in sg.items() if v['canonical'].startswith('scannet/') and v.get('passed') and v.get('box_half_factor')==1.0 and k in used]
for k,v in xs[:8]: print(k,v['canonical'],v['relative_extent_p98_median'],v['box_containment'])
# geometry failures by reason
print(collections.Counter((v['canonical'].split('/')[0],v.get('reason')) for v in sg.values()))
