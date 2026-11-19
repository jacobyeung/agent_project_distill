"""S1b local equivalent: stored predictions, identical converter, kernel and train-only variants."""
from adapter import *
import random
K=Path('/scratch/jjyeung/orch_n30/geo_k1'); ins=input_code();stored={}
ins[str(W/'evidence/k1_rule_variants.py')]=sha(W/'evidence/k1_rule_variants.py')
for p in sorted((K/'harness/out_merged_mdp').glob('*.json')):
 ins[str(p)]=sha(p)
 for it in read(p)['items']:
  if it['type']=='room_size_estimation' and it['arm']=='da3_native+R0':stored.setdefault(it['capture'],[]).append(it)
refp=W/'evidence/K1_RULE_VARIANTS.json';ref=read(refp);ins[str(refp)]=sha(refp)
manifest=read(K1);ins[str(K1)]=sha(K1);caps={c['canonical']:c for c in manifest['captures']}
variants=('R0','T05','T10','T20','C4','C5','C6','C8');rows={}
for cap,items in sorted(stored.items()):
 key=digest(caps[cap]);p=K/'pred_gpu/da3'/key[:16]/'pred.npz';done=p.parent/'DONE.json'
 if not p.is_file() or not done.is_file():raise FileNotFoundError('MISSING '+str(p))
 ins[str(p)]=sha(p);ins[str(done)]=sha(done);assert read(done)['pred_sha256']==ins[str(p)]
 result={}
 try:
  geo=convert(p,W/'out/reproduction_geom.npz');sample=room.sample(geo,'predicted')
  def area(s):
   try:return float(room.parse_response(room.format_result(room.from_points(**s)))['area_m2'])
   except (ValueError,KeyError,FloatingPointError,np.linalg.LinAlgError):return None
  result['R0']=price(geo)['area_m2']
  if items[0]['split']=='train':
   for pct,name in [(95,'T05'),(90,'T10'),(80,'T20')]:result[name]=area(trim(sample,geo,pct))
   for metres in [4,5,6,8]:
    points=[P[np.linalg.norm(P-np.asarray(geo.cam(k)[1],float),axis=1)<=metres] for k,P in zip(sample['frames'],sample['points'])]
    result['C'+str(metres)]=area(dict(sample,points=points))
 except ValueError as e:
  if str(e)!='reference_camera_up_opposes_gravity':raise
  result={'R0':None,'refused':str(e)}
 for it in items:
  rows[it['row_id']]=dict(row_id=it['row_id'],capture=cap,room=it['room'],split=it['split'],dataset=it['dataset'],gt=it['gt'],stored_R0=it['pred'],**{v:result.get(v) for v in variants},refused=result.get('refused'))
 print('reproduced',cap,flush=True)
assert set(rows)=={r['row_id'] for r in ref['rows']}
ordered=[rows[r['row_id']] for r in ref['rows']]
for expected,r in zip(ref['rows'],ordered):
 for v in variants:assert r[v]==expected[v],(r['capture'],v,r[v],expected[v])
 assert r['R0']==r['stored_R0'],r
# Original seeded bootstrap, preserving reference room insertion order.
nodes=[n for n in ast.parse((W/'evidence/k1_rule_variants.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ('mra','boot')]
ns={'random':random};exec(compile(ast.Module(body=nodes,type_ignores=[]),'reference_statistics','exec'),ns)
train=[r for r in ordered if r['split']=='train'];summary={}
for ds in ['all','scannetpp','scannet']:
 s=[r for r in train if ds in ('all',r['dataset'])]
 for v in variants:
  m=ns['boot']([(r['room'],ns['mra'](r[v],r['gt'])) for r in s]);d=ns['boot']([(r['room'],ns['mra'](r[v],r['gt'])-ns['mra'](r['R0'],r['gt'])) for r in s]);rel=[(r[v]-r['gt'])/r['gt'] for r in s if r[v] is not None]
  rec=dict(mra=m,minus_R0=d,median_rel=float(np.median(rel)),n=len(s));assert rec==ref['summary']['train'][ds+'/'+v],(ds,v)
  summary[ds+'/'+v]=rec
write(W/'out/K1_REPRODUCTION.json',dict(verdict='PASS',mode='local stored-prediction equivalent; remote inputs UNREACHABLE HERE',rebuilt_equals_stored=[len(ordered),len(ordered)],train=summary,rows=ordered),ins)
(W/'out/K1_REPRODUCTION.txt').write_text(f'PASS: {len(ordered)}/{len(ordered)} stored areas; all 24 train table entries match. Held-out variants remain null. Remote trinity-3-30 inputs UNREACHABLE HERE.\n')
status('S1b PASS: local stored predictions reproduce all 134 room rows and all 24 train table entries. This validates the legacy reference kernel. S1k supplies the deployed constants; GPU execution requires orchestrator authorization.')
