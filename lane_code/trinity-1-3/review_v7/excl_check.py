import json,random,re,collections
K='/scratch/jjyeung/orch_n30/rows_rebuild/work/s0/pull/m/k/'
B=json.load(open(K+'benchmark_scene_exclusions.json'));D=json.load(open(K+'dev_scene_exclusions.json'))
W=json.load(open('/scratch/jjyeung/orch_n30/rows_rebuild/work/withheld/WITHHELD_ROOMS_80.json'))
A=json.load(open('/scratch/jjyeung/orch_n30/b12_cntapp/work/auth/K1SPLIT_R0.json'))
amap=json.load(open('/scratch/jjyeung/orch_n30/rows_a2/work/alias_map.json'));amap.update(json.load(open('/scratch/jjyeung/orch_n30/b12_cntapp/work/d3_token_map.json')))
bt={f"{d}/{t}" for d,t in B['rung1_tokens']}|set(B['scenes']);bg=set(B['physical_groups'])
da={x for v in D['aliases'].values() for x in v}|set(D['natives']);dg=set(D['physical_groups'])|set(D['rooms'])
for v in D['canonical'].values(): da|=set(v)
wa={x for v in W['aliases'].values() for x in v};wg=set(W['rooms'])
caps=A['teacher_k1']['captures'];croom={c['canonical']:c['room'] for c in caps}
kh={c['canonical'] for c in caps if c['k1_split']=='heldout'}|{c['room'] for c in caps if c['k1_split']=='heldout'}
r0=A['r0_scenes']
r0set=set()
for k in ('captures','dev_room_list'):
  v=r0.get(k)
  if isinstance(v,list): r0set|={x if isinstance(x,str) else x.get('canonical','') for x in v}|{x.get('room','') for x in v if isinstance(x,dict)}
  elif isinstance(v,dict): r0set|=set(v)
def room_of(c):
  if c in croom: return croom[c]
  m=re.match(r'scannet/(scene\d{4})_\d\d',c)
  if m: return 'scannet/'+m.group(1)
  return c
new=[json.loads(l)["row"] for l in open("new_rows.jsonl")]
random.seed(4242);S=random.sample(new,200)
hits=collections.Counter();unres=0;ds=collections.Counter();arkit_room_unknown=0
for r in S:
  al=r['dataset']+'/'+r['scene'];c=amap.get(al) or r['provenance'].get('canonical')
  if not c: unres+=1;continue
  g=room_of(c);ds[c.split('/')[0]]+=1
  if c.startswith('arkitscenes/') and c not in croom: arkit_room_unknown+=1
  if al in bt or g in bg or c in bg: hits['bench']+=1
  if al in da or c in da or g in dg: hits['dev']+=1
  if al in wa or g in wg: hits['withheld']+=1
  if c in kh or g in kh: hits['k1h']+=1
  if c in r0set or g in r0set: hits['r0']+=1
print("r0set",len(r0set),"unresolved",unres,"hits",dict(hits),ds,"arkit room unknown",arkit_room_unknown)
# positive controls
print("ctrl bench token hits", ('d1/'+B['rung1_tokens'][0][1]) in bt, "kh size",len(kh),"dev rooms",len(dg))
# full-set check of all 8942 too
allh=collections.Counter()
for r in new:
  al=r['dataset']+'/'+r['scene'];c=amap.get(al) or r['provenance'].get('canonical') or ''
  g=room_of(c)
  if al in bt or g in bg or c in bg: allh['bench']+=1
  if al in da or c in da or g in dg: allh['dev']+=1
  if al in wa or g in wg: allh['withheld']+=1
  if c in kh or g in kh: allh['k1h']+=1
  if c in r0set or g in r0set: allh['r0']+=1
  if not c: allh['unres']+=1
print("all 8942 hits",dict(allh))
