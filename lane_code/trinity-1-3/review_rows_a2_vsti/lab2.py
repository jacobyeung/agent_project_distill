import json,sqlite3,collections,re
db=sqlite3.connect('file:/scratch/jjyeung/orch_n30/rows_a2/vsti/out/vsti_rel_v3/rows.sqlite?mode=ro',uri=True)
rows=[json.loads(t) for (t,) in db.execute('select row from rows order by i')]
L=json.load(open('labels.json'))
def rel(a,b):
    if a==b:return None
    if b.startswith(a+' ') or a.startswith(b+' '):return 'prefix'
    if b in (a+'frame',a+'sill',a+'way') or a in (b+'frame',b+'sill',b+'way'):return 'compound'
    ha,hb=a.split()[-1],b.split()[-1]
    if ha!=hb and (ha+'s'==hb or hb+'s'==ha or ha+'es'==hb or hb+'es'==ha):return 'plural-head'
    return None
STRUCT=re.compile(r'^(doorframe|door frame|windowsill|window sill|window frame|pillar|column|shower walls?|stairs?|stair rail|railing|wall .*|.* wall|ceiling .*|beam)$')
scene=collections.Counter();within=collections.Counter();struct=collections.Counter();ex=collections.Counter();plural=collections.Counter();pl=collections.Counter()
PL_OK={'glass','bus','dress','grass','mattress','canvas','lens','glasses','scissors','pants','jeans','shorts','headphones','blinds','stairs','clothes','shoes'}
for r in rows:
    t=r['question_type'];labs=set(L[r['provenance']['raster']]);own=[o['label'] for o in r['provenance']['instances']]
    k=[(a,b,rel(a,b)) for a in own for b in labs if rel(a,b)]
    if k:scene[t]+=1;ex.update((a,b) for a,b,_ in k)
    if any(rel(a,b) for i,a in enumerate(own) for b in own[i+1:]):within[t]+=1
    if any(STRUCT.match(a) for a in own):struct[t]+=1
    if any(a.endswith('s') and not a.endswith('ss') for a in own):plural[t]+=1;pl.update(a for a in own if a.endswith('s') and not a.endswith('ss'))
print('rows with a part/whole, compound or plural-head sibling label in scene',dict(scene),sum(scene.values()))
print('top',ex.most_common(30))
print('rows with such a pair among own candidates',dict(within),sum(within.values()))
print('rows with a structural-part label',dict(struct),sum(struct.values()))
print('rows with plural-form label',dict(plural),sum(plural.values()),pl.most_common(25))
