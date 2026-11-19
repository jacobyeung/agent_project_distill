"""Independent audit of binding fields, store membership, N keys/digests and room exclusions."""
import collections as C, hashlib, json, sqlite3, sys, tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
N=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w20/work/tree_r1')
sys.path.insert(0,str(N))
from student_pilot import r1_rooms, row_removals, p3_provenance
B=Path('/scratch/jjyeung/orch_n30/sb_d7bind'); ROW=Path('/scratch/jjyeung/orch_n30/sb_rowD7f/out')
def load(p): return json.loads(Path(p).read_text())
def sha(p): return p3_provenance.sha256(p)
cfg=load(N.parent/'build20/inputs/config.json'); seal=load(N.parents[1]/'out/TREE_SEAL.json')
record=[json.loads(l,object_pairs_hook=p3_provenance.unique) for l in open(B/'BINDING.jsonl')]
report=(B/'BINDING_REPORT.md').read_text(); claimed=load(B/'BINDING_CHECKS.json')
twins={r['qid']:r for r in map(json.loads,open(ROW/'NEW_ROWS.jsonl'))}
sm={r['qid']:r for r in map(json.loads,open(ROW/'SOURCE_MAP.jsonl'))}
DB=Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite')
dbsha=sha(DB); assert dbsha==r1_rooms.STORE=='210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443'
manifest=load(DB.parents[1]/'BUILD_MANIFEST.json'); receipt=load(cfg['streams']['vqa']['path'])
assert sha(DB.parents[1]/'BUILD_MANIFEST.json')==receipt['source']['sha256']
strict=r1_rooms.Rooms(cfg['r1_training']['room_authority']); tiered=r1_rooms.Rooms(cfg['r1_training']['room_authority'])
alias_path=Path('/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json'); amap=load(alias_path)
assert sha(alias_path)=='7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b'
tiered.aliases={k:v['canonical'] for k,v in amap['aliases'].items()}
u=Path('/scratch/jjyeung/orch_n30/sb_k1list/out/u_union.json')
allrem=row_removals.Removals(cfg['remove_files']+[{'path':str(u),'sha256':sha(u)}])
base_rem=row_removals.Removals(cfg['remove_files'])
list_paths={Path(p['path']).name:p for p in cfg['remove_files']}
list_paths={k:list_paths[k] for k in ('u.json','n.json','z.json')}; list_paths['u_union']={'path':str(u),'sha256':sha(u)}
keysets={k:row_removals.Removals([p]).keys[0] for k,p in list_paths.items()}
R=C.Counter(); bad=[]; strict_counts=C.Counter(); strict_from=C.Counter(); tier_counts=C.Counter(); seen=C.Counter(); source={}
source_needed={m['source_qid'] for m in sm.values()}
con=sqlite3.connect(DB.as_uri()+'?mode=ro&immutable=1',uri=True)
for i,raw in con.execute('select i,row from rows order by i'):
 r=json.loads(raw); seen[r['qid']]+=1
 if r['qid'] in source_needed: source[r['qid']]=(i,r,hashlib.sha256(raw.encode()).hexdigest())
 if row_removals.row_keys(r)&twins.keys(): R['twin_key_collisions_v7']+=1
 st,can,how=strict.status(r); strict_counts['rows']+=1;strict_counts[st]+=1;strict_from[how]+=1
 if st in ('r0','k1_heldout') and base_rem.keep(r): strict_counts['unremoved_hits']+=1
 ts,tc,th=tiered.status(r); tier_counts['rows']+=1;tier_counts[ts]+=1
 if ts in ('r0','k1_heldout') and allrem.keep(r): tier_counts['unremoved_hits']+=1
# Validate each supplied binding, using source key lookup rather than trusting source_i.
qids=[x['twin_key'] for x in record]
if len(qids)!=len(set(qids)) or set(qids)!=set(twins): bad.append('binding_population_not_bijective')
if qids!=sorted(qids): bad.append('binding_not_sorted')
hits={k:{'source':0,'twin':0} for k in keysets}; authorities=C.Counter()
for b in record:
 t=twins[b['twin_key']]; m=sm[b['twin_key']]
 if set(b)!={'twin_key','source_key','source_room','twin_sha256','room_authority'}: bad.append(['fields',t['qid']])
 if b['source_key'] not in source or seen[b['source_key']]!=1: bad.append(['source_missing_or_duplicate',t['qid']]); continue
 i,s,rawsha=source[b['source_key']]
 sk=row_removals.row_keys(s); tk=row_removals.row_keys(t)
 checks={
 'source_key':sk=={b['source_key']} and b['source_key']==m['source_qid'],
 'twin_keys':tk=={b['twin_key'],b['source_key']},
 'source_index':i==m['source_i']==t['provenance']['sb_rowD7']['source_store_i'],
 'source_raw_sha':rawsha==m['source_row_sha256']==t['provenance']['sb_rowD7']['source_row_sha256'],
 'twin_digest':p3_provenance.digest(t)==b['twin_sha256'],
 'dataset_scene_equal':(s['dataset'],s['scene'])==(t['dataset'],t['scene']),
 'frames_equal':s['student_input']['frame_indices']==t['student_input']['frame_indices'],
 }
 st,sc,how=strict.status(s); chosen=strict if st!='unresolved' else tiered
 sc,sh=chosen.canonical(s); tc,th=chosen.canonical(t)
 sr=chosen.room(sc); tr=chosen.room(tc)
 checks['room_equal']=sr==tr==b['source_room']==m['room']
 checks['room_allowed']=sr not in chosen.k1|chosen.r0
 if st=='unresolved':
  tok={'scannet':'d1','scannetpp':'d2','scannetppv2':'d2','arkitscenes':'d3'}.get(s['dataset'],s['dataset'])+'/'+s['scene']
  tag='tiered_alias_map_7f50287b_tier_'+amap['aliases'][tok]['tier']+':strict_unresolved_in_dd60517b'
 else: tag='strict_rooms_dd60517b_authority:'+how
 checks['authority_tag']=tag==b['room_authority'];authorities[tag]+=1
 for name,ok in checks.items():
  R[name+'_pass' if ok else name+'_fail']+=1
  if not ok: bad.append([name,t['qid']])
 for name,keys in keysets.items(): hits[name]['source']+=bool(sk&keys);hits[name]['twin']+=bool(tk&keys)
 R['all_removal_hits']+=bool(allrem.match(t))
 R['twins_unremoved_hits']+=bool(sr in chosen.k1|chosen.r0 and allrem.keep(t))
audit=load(cfg['r1_training']['room_audit']['path'])
for k in ('rows','ok','r0','k1_heldout','unresolved','unremoved_hits'):
 if strict_counts[k]!=audit['store'][k]: bad.append(['strict_census',k])
if dict(strict_from)!=audit['store']['canonical_from']: bad.append('strict_hows')
# Recompute exact archive hashes and every current out/ member, without extracting.
archive=ROW/'sb_rowD7f.tar'; arcsha=sha(archive); advertised=(ROW/'sb_rowD7f.tar.sha256').read_text().split()[0]
if arcsha!=advertised: bad.append('archive_sha')
member_checks={}
with tarfile.open(archive) as tf:
 for m in tf.getmembers():
  if not m.isfile() or not m.name.startswith('out/'): continue
  local=ROW/m.name.removeprefix('out/')
  if not local.is_file(): continue
  h=hashlib.sha256()
  with tf.extractfile(m) as f:
   for block in iter(lambda:f.read(4<<20),b''): h.update(block)
  member_checks[m.name]=h.hexdigest()==sha(local)
  if not member_checks[m.name]: bad.append(['archive_member_mismatch',m.name])
module_checks={}
for mod in list(sys.modules.values()):
 p=getattr(mod,'__file__',None)
 if p and p.startswith(str(N)):
  rel=str(Path(p).relative_to(N));module_checks[rel]=sha(p)==seal['files'].get(rel)
if not all(module_checks.values()): bad.append('sealed_module_mismatch')
# Check producer input pins, including the stable artifacts used by its report.
pin_bad=[]
for p,h in claimed['inputs'].items():
 if not p.startswith('/scratch/'): pin_bad.append([p,'outside_local_scope']);continue
 if not Path(p).is_file(): pin_bad.append([p,'MISSING']);continue
 if sha(p)!=h: pin_bad.append([p,'sha_mismatch'])
R['bindings']=len(record); R['sources_unique']=len(source)
out={'results':dict(R),'failures':bad,'source_store_sha256':dbsha,'binding_sha256':sha(B/'BINDING.jsonl'),'archive_sha256':arcsha,'removal_hits':hits,'list_sizes':{k:len(v) for k,v in keysets.items()},'strict_census':dict(strict_counts),'strict_canonical_from':dict(strict_from),'tiered_census':dict(tier_counts),'authority_counts':dict(authorities),'archive_out_member_checks':member_checks,'sealed_module_checks':module_checks,'producer_input_pin_failures':pin_bad,'scope':'Binding artifact sufficiency for path (b); no augmented database or build-22 admission code is certified by this review.'}
(ROOT/'work/BINDING_REVIEW.json').write_text(json.dumps(out))
print(json.dumps({k:v for k,v in out.items() if k not in ('archive_out_member_checks','sealed_module_checks')},indent=1))
