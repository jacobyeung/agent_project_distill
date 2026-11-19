from common import *
import tarfile
shutil.copytree(W/'w19/work/tree_r1',TREE,dirs_exist_ok=True)
origins=[]; byhash={}
def add(p,origin=None):
 p=Path(p);q=snapshot(p);h=sha(q);byhash[h]=str(q)
 origins.append(dict(source=origin or str(p),sha256=h,copy=str(q.relative_to(KIT))))
 return q
for p in sorted(A.iterdir()):
 if p.is_file():add(p)
for p in sorted(N.glob('*')):
 if p.is_file():add(p)
for p in [B/'out/SURVEY.json',B/'out/PIN_RESOLUTION.json',B/'out/INTERSECTIONS.json',B/'out/BENCHMARK_SCENES.json',B/'work/json_index_full.json',B/'work/benchmark_scene_exclusions.json',W/'w19/work/build19/inputs/component_rows.json',Path('/scratch/jjyeung/orch_n30/sb_evrev/REVIEW_VERDICT.md'),Path('/scratch/jjyeung/orch_n30/sb_alias2/out/TIERED_ALIAS_MAP.json'),Path('/scratch/jjyeung/orch_n30/sb_alrev/token_rooms.json'),Path('/scratch/jjyeung/orch_n30/sb_alrev/review.py')]:add(p)
for folder in ['inventories','drafts']:
 for p in sorted((Path('/scratch/jjyeung/orch_n30/sb_inventory')/folder).glob('*')):
  if p.is_file():add(p)
cr=read(W/'w19/work/build19/inputs/component_rows.json')
for v in cr['proven']['authority'].values():
 q=add(v['path']);assert sha(q)==v['sha256']
for v in cr['proven']['store']['removals']:
 q=add(v['path']);assert sha(q)==v['sha256']
# Use tar's seekable reader: skip large payloads; copy only genuine kit metadata.
tars=[(Path('/scratch/jjyeung/n30_mirror/cont_ops/h1pkt_fix5_2252Z.tar'),'h1/chain_r1/build/fx/k/'),(Path('/scratch/jjyeung/n30_mirror/old_lanes_3_30/old_lanes_3_30_a.tar'),None)]
for archive,prefix in tars:
 with tarfile.open(archive,'r:') as t:
  for m in t:
   take=m.isfile() and ((prefix and m.name.startswith(prefix) and m.size<40<<20) or (not prefix and m.name.endswith('/ap/e84d901c/arm/frozen/6f27ae81/model.json')))
   if not take:continue
   raw=t.extractfile(m).read();h=hashlib.sha256(raw).hexdigest();q=KIT/'inputs'/(h+'_'+Path(m.name).name)
   q.write_bytes(raw);byhash[h]=str(q)
   origins.append(dict(source=str(archive),member=m.name,sha256=h,hash_scope='uncompressed member bytes',copy=str(q.relative_to(KIT))))
# Resolve metadata pins through the bounded existing survey index and genuine local kit.
index=read(B/'work/json_index_full.json');idx={}
for x in index:idx.setdefault(x['sha256'],[]).append(x['path'])
for p in (W/'w12/fixtures/work/kit07ca49df_meta/m/k').iterdir():
 if p.is_file() and p.stat().st_size<40<<20 and p.suffix in ('.json','.jsonl','.tsv'):add(p)
front=list(byhash.values());seen=set()
while front:
 p=Path(front.pop())
 if str(p) in seen or p.suffix!='.json':continue
 seen.add(str(p))
 try:d=read(p)
 except (ValueError,UnicodeError):continue
 for v in pins(d):
  h=v['sha256']
  if h in byhash:continue
  for candidate in idx.get(h,[]):
   c=Path(candidate)
   if not str(c).startswith('/scratch/') or not c.is_file() or c.stat().st_size>40<<20:continue
   q=add(c);assert sha(q)==h;front.append(str(q));break
save(OUT/'SOURCE_INDEX.json',dict(schema='sb-records-source-index-v1',inputs=[pin(__file__),pin(ROOT/'work/common.py')],sources=origins,byhash=byhash))
status('Stage 1 complete. The workspace holds immutable source copies, the unchanged N policy tree, genuine LEG-S1 kit members and the pinned base-model manifest. Parent receipt traversal identifies missing ancestry; no component record has been issued.')
print('snapshots',len(origins),'unique hashes',len(byhash))
