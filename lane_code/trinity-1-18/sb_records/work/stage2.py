from common import *
import gzip,re,collections,multiprocessing as mp,sqlite3
sys.path.insert(0,str(TREE))
from student_pilot.r1_rooms import Rooms
from student_pilot.row_removals import Removals
SCOPE=('VSI-Bench','VSTI','ReVSI');NATIVE={'d1':'scannet','d2':'scannetppv2','d3':'arkitscenes'}
IDX=read(OUT/'SOURCE_INDEX.json')['byhash']
def get(pre):
 hits=[Path(v) for k,v in IDX.items() if k.startswith(pre)];assert len(hits)==1,(pre,hits);return hits[0]
def mint(c):
 ds,s=c.split('/',1);ds='scannetppv2' if ds=='scannetpp' else ds
 return {'scannet':'d1','scannetppv2':'d2','arkitscenes':'d3'}[ds]+'/v'+hashlib.sha256(('rung1 scene '+ds+'/'+s).encode()).hexdigest()[:12]
def ark_worker(args):
 lo,hi,targets=args;h=hashlib.sha256(b'rung1 scene arkitscenes/');out=[]
 for i in range(lo,hi):
  q=h.copy();q.update(str(i).encode());t='d3/v'+q.hexdigest()[:12]
  if t in targets:out.append((t,'arkitscenes/'+str(i)))
 return out

def main():
 used={}
 def use(p):p=Path(p);used[str(p)]=pin(p);return p
 def rd(p):return read(use(p))
 cr=rd(get('d3d3')) if False else rd(snapshot(W/'w19/work/build19/inputs/component_rows.json'))
 auth={k:dict(path=str(get(v['sha256'])),sha256=v['sha256']) for k,v in cr['proven']['authority'].items()}
 for v in auth.values():use(v['path'])
 R=Rooms(auth)
 alias=rd(snapshot('/scratch/jjyeung/orch_n30/sb_alias2/out/TIERED_ALIAS_MAP.json'))['aliases']
 rows={};rowpaths={};targets=set()
 for p in sorted(A.glob('*rows.scenes.jsonl.gz')):
  label=next(x for x in ['pointing','routing','vqa','a2v3','a3v2','r16'] if '__'+x+'__' in p.name)
  p=use(snapshot(p));rowpaths[label]=p
  with gzip.open(p,'rt') as f:rows[label]=[json.loads(l) for l in f]
  assert len({r['i'] for r in rows[label]})==len(rows[label])
  targets|={r['dataset']+'/'+r['scene'] for r in rows[label]}
  print('loaded',label,len(rows[label]),flush=True)
 fm=use(get('17aa3e9e'));framecounts=collections.Counter()
 with gzip.open(fm,'rt') as f:
  for l in f:
   d=json.loads(l);framecounts[d['d']+'/'+d['s']]+=1
 targets|=set(framecounts)
 ro=rd(get('edaecb6c'));targets|={'/'.join(x) for x in ro['scenes']}
 # Check only candidate preimages that reproduce the precise token; no guessed aliases.
 mapping={};methods=collections.defaultdict(set);conflicts=[]
 def candidate(t,c,method):
  c=c.replace('scannetppv2/','scannetpp/')
  if mint(c)!=t:return
  if t in mapping and mapping[t]!=c:conflicts.append([t,mapping[t],c])
  else:mapping[t]=c;methods[t].add(method)
 for t,x in alias.items():
  if re.fullmatch(r'd[123]/v[0-9a-f]{12}',t):candidate(t,x['canonical'],'tiered_alias_remint')
 fp=use(get('7cc01f36'));plan=json.load(gzip.open(fp,'rt'))
 for t,x in plan['v'].items():candidate(x['g']+'/'+t,x['n'].removesuffix('.mp4'),'pinned_frame_plan_remint')
 for t,x in plan['a'].items():
  match=re.search(r'/(?:Training|Validation)/(\d+)/',x['u']);assert match
  candidate('d3/'+t,'arkitscenes/'+match.group(1),'pinned_frame_plan_remint')
 bench=rd(get('3119aa4a'));banks={b:dict(captures=set(),rooms=set()) for b in SCOPE}
 for token,fact in bench['members'].items():
  ds,scene=token.split('/',1);c=NATIVE[ds]+'/'+scene;c=c.replace('scannetppv2/','scannetpp/')
  candidate(mint(c),c,'BENCH_v2_remint')
  room=R.room(c)
  # All list groups are normalised through Rooms.room where applicable.
  grp=fact['group'];ng=grp if grp.startswith('arkitscenes/') else R.room(grp)
  assert room==ng
  for b in set(fact['benchmarks'])&set(SCOPE):banks[b]['captures'].add(c);banks[b]['rooms'].add(room)
 for corpus,scenes in bench['other_corpora'].items():
  owners=[b for b,v in bench['by_benchmark'].items() if corpus in v]
  if len(owners)==1 and owners[0] in banks:
   banks[owners[0]]['captures'].update(corpus+'/'+s for s in scenes);banks[owners[0]]['rooms'].update(corpus+'/'+s for s in scenes)
 # Exhaustive ScanNet labels and eight-digit ARKit IDs for recovered non-v7 targets.
 extra=targets-set(mapping);d1={t for t in extra if t.startswith('d1/')};d3={t for t in extra if t.startswith('d3/')}
 for i in range(10000):
  for j in range(100):
   c=f'scannet/scene{i:04d}_{j:02d}';t=mint(c)
   if t in d1:candidate(t,c,'exhaustive_scannet_0000_9999_00_99')
 # Use exhaustive enumeration even when known visit IDs would resolve the same target.
 if d3:
  with mp.Pool(8) as pool:
   for hits in pool.imap_unordered(ark_worker,[(i*1000000,(i+1)*1000000,d3) for i in range(100)]):
    for t,c in hits:candidate(t,c,'exhaustive_arkit_0_99999999')
 assert not conflicts,conflicts
 unresolved=sorted(targets-set(mapping));print('resolved',len(targets)-len(unresolved),'/',len(targets),'unresolved',unresolved[:20],flush=True)
 for p in [TREE/'student_pilot/r1_rooms.py',TREE/'student_pilot/carrier_c1_routing.py',Path(__file__),ROOT/'work/common.py']:use(p)
 common=list(used.values())
 def audit(label,rr,inputs,scope):
  count=collections.Counter();tc=collections.Counter();over={b:{} for b in SCOPE};un=collections.Counter();sc=set();rs=set()
  for r in rr:
   count['rows']+=1;t=str(r.get('dataset') or '')+'/'+str(r.get('scene') or '');tc[t]+=1
   c=mapping.get(t)
   if not c:
    c0,_=R.canonical(r)
    if c0 and not re.search(r'/v[0-9a-f]{12}$',c0):c=c0
   if not c:count['unresolved']+=1;un[t]+=1;continue
   room=R.room(c);sc.add(c);rs.add(room);count['resolved']+=1
   for b in SCOPE:
    if c in banks[b]['captures'] or room in banks[b]['rooms']:
     count[b]+=1
     x=over[b].setdefault(c,dict(bank=b,canonical=c,room=room,venue=room.split('venue')[1] if room.startswith('arkitscenes/venue') else None,rows=0,example_qids=[]))
     x['rows']+=1
     if len(x['example_qids'])<3:x['example_qids'].append(r.get('qid',r.get('i')))
  return dict(label=label,scope=scope,inputs=[pin(p) for p in inputs],counts={k:count[k] for k in ['rows','resolved','unresolved',*SCOPE]},scenes=sorted(sc),rooms=sorted(rs),scene_count=len(sc),room_count=len(rs),token_counts=dict(sorted(tc.items())),unresolved_tokens=dict(un),overlaps={b:list(v.values()) for b,v in over.items()},complete_parent_membership=False)
 results=[]
 for label,rr in rows.items():results.append(audit('raw_'+label,rr,[rowpaths[label]],'Recovered database projection; raw rows are not proof of checkpoint consumption.'))
 prep=rd(get('0664bb17'));selected={}
 for name in ['pointing','routing','vqa']:
  p=use(get(prep['streams'][name]['indices']['sha256']));ids=rd(p);lookup={r['i']:r for r in rows[name]}
  selected[name]=[lookup[i] for i in ids];assert len(ids)==prep['streams'][name]['count']
  results.append(audit('m544_admitted_'+name,selected[name],[rowpaths[name],p,get('0664bb17')],'Pinned prepared stream index; admitted population, not actual sampled step history.'))
 for name,key in [('pose','order'),('pose_before_scene_filter','scene_source')]:
  spec=prep['streams']['pose'] if key=='order' else prep['streams']['pose']['scene_source'];p=use(get(spec['order']['sha256']));order=rd(p)
  lookup=[{r['i']:r for r in rows[n]} for n in ['a2v3','a3v2']];rr=[lookup[a][i] for a,i in order];assert len(rr)==spec['count']
  selected[name]=rr;results.append(audit('m544_admitted_'+name,rr,[p,rowpaths['a2v3'],rowpaths['a3v2'],get('0664bb17')],'Pinned pose order; stores mapped by the preparation sources list.'))
 results.append(audit('m544_admitted_union',(r for n in ['pointing','routing','vqa','pose'] for r in selected[n]),[get('0664bb17')]+list(rowpaths.values()),'Union of four admitted streams; excludes inherited ancestry and does not claim exact sampling.'))
 frame_rows=(dict(dataset=t.split('/')[0],scene=t.split('/')[1],qid='frame-pool') for t,n in framecounts.items() for _ in range(n))
 results.append(audit('m544_frame_universe',frame_rows,[fm,fp],'Frame inventory only, not proof those captures were trained.'))
 results.append(audit('readout_training_scenes',(dict(dataset=d,scene=s) for d,s in ro['scenes']),[get('edaecb6c')],'Readout scene universe from the pinned training_scenes list.'))
 # Full v7 scan retains only compact rows in memory; independently verifies the database bytes.
 db=Path(cr['proven']['store']['database']['path']);assert sha(db)==cr['proven']['store']['database']['sha256'];use(db)
 remspec=[]
 for v in cr['proven']['store']['removals']:
  q=use(get(v['sha256']));remspec.append({**v,'path':str(q)})
 rem=Removals(remspec);nzupre={'02315a74','caba6a56','43853165'}
 nzu=Removals([v for v in remspec if v['sha256'][:8] in nzupre]);raw=[];kept=[];kept_nzu=[];own_bad=[]
 projection=KIT/'inputs/v7_membership.jsonl.gz'
 with sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True) as con,gzip.open(projection,'wt') as out:
  for i,s in con.execute('select i,row from rows order by i'):
   r=json.loads(s);t=r['dataset']+'/'+r['scene'];x={k:r.get(k) for k in ('qid','dataset','scene','question_type')};x['i']=i
   canonical=mapping.get(t);assert canonical,(i,t)
   for obj in (r,r.get('provenance') or {},r.get('ground_record') or {},r.get('gt_authority') or {}):
    if obj.get('canonical') and obj['canonical'].replace('scannetppv2/','scannetpp/')!=canonical:own_bad.append([i,obj['canonical'],canonical])
   x['canonical']=canonical;x['keep_all_lists']=rem.keep(r);x['keep_nzu']=nzu.keep(r);out.write(json.dumps(x,sort_keys=True)+'\n');raw.append(x)
   if x['keep_all_lists']:kept.append(x)
   if x['keep_nzu']:kept_nzu.append(x)
 assert len(raw)==204413 and not own_bad
 for label,rr in [('v7_raw',raw),('v7_minus_nzu',kept_nzu),('v7_minus_component_rows_bound_lists',kept)]:
  results.append(audit(label,rr,[db,projection,*[v['path'] for v in remspec]],'Complete v7 scene audit; removals use N row_keys and defect rules on full source rows.'))
 for name,spec in cr['proven']['routing_slices'].items():
  p=Path(spec['source']['path']);assert sha(p)==spec['source']['sha256'];use(p);rr=[]
  with p.open() as f:
   for l in f:
    r=json.loads(l);rr.append({**{k:r.get(k) for k in ('qid','dataset','scene')},'canonical':R.canonical(r)[0]})
  results.append(audit('N_routing_'+name,rr,[p],'Surviving routing slice before removals; bindings may differ from n1fix2 registry config.'))
 save(OUT/'TOKEN_INVERSION.json',dict(schema='sb-records-token-inversion-v1',inputs=list(used.values()),mint_rule="v + sha256('rung1 scene ' + native_dataset + '/' + scene)[:12]",scannetpp_native='scannetppv2',recovered_target_count=len(targets),unresolved=unresolved,conflicts=conflicts,aliases={t:dict(canonical=mapping[t],room=R.room(mapping[t]),methods=sorted(methods[t])) for t in sorted(set(mapping)&(targets|{r['dataset']+'/'+r['scene'] for r in raw}))}))
 save(OUT/'POPULATIONS.json',dict(schema='sb-records-populations-v1',inputs=[pin(OUT/'TOKEN_INVERSION.json'),*list(used.values()),pin(projection)],banks={b:{k:sorted(v) for k,v in x.items()} for b,x in banks.items()},populations=results,removal_counts=dict(all_lists=dict(removed=rem.removed,matches=rem.matches,source_counts=rem.source_counts),nzu=dict(removed=nzu.removed,matches=nzu.matches,source_counts=nzu.source_counts)),projection_provenance='The six recovered gzip files are projections of remotely verified databases, as attested in SOURCES_13.tsv. Their gzip hashes are distinct from the original SQLite hashes. v7 database hash and projection were produced locally.'))
 for r in results:print(r['label'],r['counts'],flush=True)
 status('Stage 2 complete. The audit recomputes canonical scenes, physical rooms and all three benchmark intersections for recovered raw stores, step-544 admitted indices, the frame universe, readout scene list, v7 and routing slices. Overlaps and unresolved tokens remain explicit; no complete ancestry is inferred from these populations.')
if __name__=='__main__':main()
