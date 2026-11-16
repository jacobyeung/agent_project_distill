import json,sqlite3,collections,csv,hashlib,re
db=sqlite3.connect('file:/scratch/jjyeung/orch_n30/rows_a2/vsti/out/vsti_rel_v3/rows.sqlite?mode=ro',uri=True)
rows=[json.loads(t) for (t,) in db.execute('select row from rows order by i')]
K='/scratch/jjyeung/orch_n30/rows_rebuild/work/s0/pull/m/k/'
B='/scratch/jjyeung/orch_n30/b12_cntapp/work/'
FAM={'d1':'scannet','scannet':'scannet','d2':'scannetpp','scannetpp':'scannetpp','scannetppv2':'scannetpp','d3':'arkit','arkitscenes':'arkit'}
def nk(s):
    ds,i=s.split('/',1); return (FAM.get(ds,ds),i)
bad=collections.defaultdict(set)
b=json.load(open(K+'benchmark_scene_exclusions.json'))
for s in b['scenes']:bad[nk(s)].add('bench')
for s in b['physical_groups']:bad[nk(s)].add('bench_room')
for ds,t in b['rung1_tokens']:bad[nk(ds+'/'+t)].add('bench_tok')
for s,m in b['members'].items():bad[nk(m['group'])].add('bench_room')
d=json.load(open(K+'dev_scene_exclusions.json'))
for key in ['natives','rooms','physical_groups']:
    for s in d[key]:bad[nk(s)].add('dev')
for key in ['canonical','aliases']:
    for s,v in d[key].items():
        for x in [s]+v:bad[nk(x)].add('dev')
w=json.load(open('/scratch/jjyeung/orch_n30/rows_rebuild/work/withheld/WITHHELD_ROOMS_80.json'))
for s in w['rooms']:bad[nk(s)].add('wh')
for s,v in w['aliases'].items():
    for x in v:bad[nk(x)].add('wh')
for l in open('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/b10_reserve/R0_ROOMS.txt'):
    if l.strip():bad[nk(l.strip())].add('r0')
k1=json.load(open(B+'auth/K1SPLIT_R0.json'))
for c,v in k1['r0_scenes']['captures'].items():bad[nk(c)].add('r0');bad[nk(v['room'])].add('r0')
for x in k1['r0_scenes'].get('rooms',[]):
    if isinstance(x,str):bad[nk(x)].add('r0')
for c in k1['teacher_k1']['captures']:
    if c['k1_split']=='heldout':
        bad[nk(c['canonical'])].add('k1h');bad[nk(c['room'])].add('k1h')
        for a in c['aliases']:bad[nk(a)].add('k1h')
print('r0 rooms list type',type(k1['r0_scenes'].get('rooms')).__name__, str(k1['r0_scenes'].get('rooms'))[:200])
meta={r['video_id']:r for r in csv.DictReader(open(B+'auth/arkit_3dod_metadata.csv'))}
ts={}
for n in ['ARK_PIN_TS_CHECK.json','ARK_PIN_TS_CHECK_K1.json']:
    for a,s in json.load(open(B+n)).items():ts.setdefault(a,set()).add(s)
def tok(native_ds,scene): return 'v'+hashlib.sha256(('rung1 scene '+native_ds+'/'+scene).encode()).hexdigest()[:12]
hits=collections.Counter();tokmis=collections.Counter();scen=set();fails=[]
for r in rows:
    c=r['provenance']['canonical'];ds,i=c.split('/',1);alias=r['dataset']+'/'+r['scene']
    names={nk(c),nk(alias)}
    if ds=='scannet':names.add(('scannet',re.match(r'scene\d+',i).group(0)))
    if ds=='arkitscenes':
        m=meta.get(i)
        if not m or m['fold']!='Training':fails.append((r['qid'],'fold',m and m['fold']))
        if m and m['visit_id']!='NA':names.add(('arkit','venue'+m['visit_id']))
        if ts.get(alias)!={'ok'}:fails.append((r['qid'],'ts',ts.get(alias)))
    nat={'scannet':'scannet','scannetppv2':'scannetppv2','scannetpp':'scannetppv2','arkitscenes':'arkitscenes'}[ds]
    t=tok(nat,i);names.add(nk(r['dataset']+'/'+t))
    tokmis[(r['dataset'],r['scene']==t, r['scene']==i)]+=1
    for n_ in names:
        if n_ in bad:hits[tuple(sorted(bad[n_]))]+=1;fails.append((r['qid'],c,n_,sorted(bad[n_])))
    scen.add(c)
print('rows',len(rows),'scenes',len(scen))
print('alias==rung1token(canonical) / alias==native:',tokmis)
print('exclusion hits',hits)
print('fails',len(fails),fails[:10])
# ARKit venue overlap between rows and any bench ARKit capture venue
bv=set()
for s in b['scenes']:
    f,i=nk(s)
    if f=='arkit' and i in meta and meta[i]['visit_id']!='NA':bv.add(meta[i]['visit_id'])
rv={meta[r['provenance']['canonical'].split('/')[1]]['visit_id'] for r in rows if r['dataset']=='d3'}
print('bench arkit venues',len(bv),'row venues',len(rv),'overlap',len(bv&rv - {'NA'}))
print('canonical datasets',collections.Counter(r['provenance']['canonical'].split('/')[0] for r in rows))
