import os, sys, json, hashlib, re, gzip, copy, time, traceback
from pathlib import Path
from collections import Counter, defaultdict
ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/scratch/jjyeung/orch_n30')
TREE=BASE/'tree_rebuild10_w/w24/work/tree_r1'
INV=BASE/'sb_fullinv'
NAMES=['recovery','absolute_distance','units','coverage_distance','coverage_units','camera_wording']
PYTHON='/scratch/jjyeung/envs/p1cpu/bin/python'
PREFIX='nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 '+PYTHON+' -B '
sys.path.insert(0,str(TREE))
INPUTS={}
MAPS={}
def pin(path, expected=None):
 p=Path(path).absolute()
 if str(p) not in INPUTS:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
  INPUTS[str(p)]={'sha256':h.hexdigest(),'bytes':p.stat().st_size}
 h=INPUTS[str(p)]['sha256']
 if expected is not None:assert h==expected,(p,h,expected)
 return dict(path=str(p),sha256=h)
def load(path):
 pin(path);return json.loads(Path(path).read_text())
def imported():
 for m in list(sys.modules.values()):
  f=getattr(m,'__file__',None)
  if f and Path(f).is_relative_to(TREE) and Path(f).is_file():pin(f)
 # These readers use adjacent immutable data, outside Python's module loader.
 for f in ['student_pilot/r0_scenes.json','student_pilot/r2_withheld.json','student_pilot/r2_dev_merged.json']:
  p=TREE/f
  if p.is_file():pin(p)
def write(rel,data):
 imported();p=ROOT/rel;p.parent.mkdir(parents=True,exist_ok=True)
 data=dict(data,inputs=dict(INPUTS),command=COMMAND)
 p.write_text(json.dumps(data,sort_keys=True,indent=2)+'\n');INPUTS.pop(str(p),None)
 return pin(p)
def status(stage, text):
 msg=f'Stage {stage}: {text}\n'
 (ROOT/'STATUS.md').write_text(msg)
 p=ROOT/f'out/STATUS_{stage}.md';p.write_text(msg)
 print(msg,flush=True)
def staged(p):
 q=pin(p['path'],p['sha256']);dst=ROOT/'u'/q['sha256']
 if not dst.exists():dst.symlink_to(q['path'])
 MAPS[q['sha256']]=str(dst)
 return dict(path='u/'+q['sha256'],sha256=q['sha256'])
def resolve(p):
 return ROOT/p['path'] if not Path(p['path']).is_absolute() else Path(p['path'])
def drafts():
 return {n:load(INV/f'work/envelopes/{n}.json') for n in NAMES}
def rows(path):
 with Path(path).open() as f:
  for line in f:
   if line.strip():yield json.loads(line)
def lines(path):
 with Path(path).open() as f:
  for line in f:
   if line.strip():yield line,json.loads(line)
def framepins():
 inv=load(INV/'out/FULL_INVENTORY.json')
 ans={}
 for k,filename in [('frame_map','frame_map.jsonl.gz'),('frame_plan','frame_plan.json.gz')]:
  p=inv['frame_host']['metadata'][k]['expected']
  ans[k]=pin(BASE/'fb_pack/in/pk'/filename,p['sha256'])
 ans['fps_authority']=pin(inv['frame_host']['metadata']['fps_authority']['local_matches'][0]['path'],inv['frame_host']['metadata']['fps_authority']['expected']['sha256'])
 return ans
CALL=re.compile(r'<ground\b[^>\n]*>')
OBJ=re.compile(r'(\bobj\s*=\s*)([\"\x27])heater\2|(?<=obj=)heater(?=\s|>)')
def rewrite(v):
 if isinstance(v,str):
  return CALL.sub(lambda m:OBJ.sub(lambda x: (x[1]+x[2]+'radiator'+x[2]) if x[1] else 'radiator',m[0]),v)
 if isinstance(v,list):return [rewrite(x) for x in v]
 if isinstance(v,dict):return {k:rewrite(x) for k,x in v.items()}
 return v

def stage1():
 from student_pilot.p3_provenance import digest
 from student_pilot.extent_receipt import Extents, content, required
 from student_pilot.r2_adapters import normalize
 from student_pilot.s1_routing import Frames
 ds=drafts();fps=framepins();fm=Frames(fps['frame_map'],fps['frame_plan'],fps_authority=fps['fps_authority'])
 ex=Extents(ds['recovery']['extent_receipt']);pin(ds['recovery']['extent_receipt']['path'],ds['recovery']['extent_receipt']['sha256'])
 out={}
 for name,e in ds.items():
  source=pin(e['rows']['path'],e['rows']['sha256']);dest=ROOT/f'out/variant_R/{name}.jsonl';dest.parent.mkdir(parents=True,exist_ok=True)
  changed=[];total=0;checks=Counter();examples=[]
  with dest.open('w') as f:
   for line,r in lines(source['path']):
    total+=1;v=rewrite(r)
    if v!=r:
     q=r['qid'];changed.append(q)
     assert digest(r)==e['row_bindings'][q]
     assert digest(v)!=e['row_bindings'][q]
     # Compare the sealed normalized content; no geometry, receipt or identity is fabricated.
     n=normalize(r,fm);ex.check(n,'routing');checks['original_extent_pass']+=1
     vn=rewrite(n);assert digest(content(n))!=digest(content(vn))
     try:ex.check(vn,'routing')
     except ValueError as err:checks[str(err)]+=1
     else:raise AssertionError('rewritten extent unexpectedly passed')
     if len(examples)<2:examples.append(dict(qid=q,old_raw_sha256=digest(r),new_raw_sha256=digest(v),old_extent_content_sha256=digest(content(n)),new_extent_content_sha256=digest(content(vn)),bound_entry=ex.receipt['rows'][q]))
     for k in ('question','answer','gt_answer'):
      assert r.get(k)==v.get(k)
    f.write(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n' if v!=r else line)
  out[name]=dict(source=source,rows=total,changed=len(changed),changed_qids=changed,checks=dict(checks),examples=examples,variant_R=pin(dest),production_selection='original call text; variant R is NOT production-admissible')
  print(name,total,len(changed),dict(checks),flush=True)
  if name=='camera_wording':
   # Zero changes; retaining the tiny pointer is enough, but this file remains an audited variant.
   pass
 write('out/PHRASE_DECISION.json',dict(decision='PIN_BREAKS_USE_ORIGINALS',slices=out,extent_pin=ds['recovery']['extent_receipt'],regeneration_owner='tree_rebuild and the independent extent-audit owner',required_regeneration=['Independent extent audit for every changed normalized row; replace c072905b receipt only with witnessed audit', 'raw row_bindings and source row/file pins, scene coverage rows_sha256, upstream receipts and envelopes', 'coverage-family fixed hashes in r1_coverage.PINS; parent/derivation validation and catalog membership', 'printed-call span offsets must be repacked before authenticating variant R'],scope='Only strings within ground obj=heater calls change. Questions, answers and all other text stay byte-identical as string values. Variant R is diagnostic and keeps original structural offsets; no extent receipt was invented.'))
 status(1,'The radiator rewrite invalidates extent and raw membership pins. Production keeps original call text; variant R files and exact changed QIDs are recorded in PHRASE_DECISION.json.')

def stage2():
 ds=drafts();e=ds['camera_wording'];source=pin(e['rows']['path'],e['rows']['sha256']);cov=load(e['scene_coverage']['path']);fps=framepins()
 fm={}
 with gzip.open(fps['frame_map']['path'],'rt') as f:
  for line in f:
   r=json.loads(line);fm[r['d'],r['s'],r['i']]=dict(path=r['path'],sha256=r['sha256'])
 camera=list(rows(source['path']));diff={};missing=[]
 for r in camera:
  for i,p in zip(r['student_input']['frame_indices'],r['student_input']['frames']):
   key=(r['dataset'],r['scene'],i);other=fm.get(key)
   if other and p['sha256']!=other['sha256']:
    v=diff.setdefault(key,dict(dataset=key[0],scene=key[1],ordinal=i,kr9c=p,k6tk=other,qids=[]));v['qids'].append(r['qid'])
  if cov['rows'][r['qid']].get('status')!='known':missing.append(r['qid'])
 assert len(missing)==21
 assert {(r['dataset'],r['scene']) for r in camera if r['qid'] in missing}=={('d2','vfc2c241f2978')}
 affected={q for v in diff.values() for q in v['qids']}
 report=dict(source=source,frame_map=fps['frame_map'],unique_references=len(diff),unique_kr9c_sha256=sorted({v['kr9c']['sha256'] for v in diff.values()}),unique_k6tk_sha256=sorted({v['k6tk']['sha256'] for v in diff.values()}),citing_rows=len(affected),citing_qids=sorted(affected),references=list(diff.values()),scope='Metadata pin comparison only. PNG bytes were not read. Different roots are preserved; no k6tk substitution for kr9c.')
 write('out/CAMERA_KR9C_DIFF.json',report)
 variants={}
 for name,drop in [('camera_wording',set(missing)),('camera_B',set(missing)|affected)]:
  dest=ROOT/f'out/rows/{name}.jsonl';dest.parent.mkdir(parents=True,exist_ok=True)
  keep=[]
  with dest.open('w') as f:
   for line,r in lines(source['path']):
    if r['qid'] not in drop:f.write(line);keep.append(r['qid'])
  rp=pin(dest)
  cp=write(f'out/coverage/{name}.json',dict(rows_sha256=rp['sha256'],exclusions=e['exclusions'],rows={q:cov['rows'][q] for q in keep},source_coverage=e['scene_coverage'],scope='Subset of independently evidenced source coverage; no invented scene mapping.'))
  rem=write(f'out/REMOVE_{name}.json',dict(source=source,rows=[dict(row_key=q,reason='independent_scene_evidence_MISSING' if q in missing else 'kr9c_k6tk_hash_mismatch') for q in sorted(drop)],semantics='Remove these QIDs from this exact source version only.'))
  variants[name]=dict(rows=rp,row_count=len(keep),coverage=cp,remove=rem)
 write('out/CAMERA_SELECTION.json',dict(variants=variants,missing_scene='d2/vfc2c241f2978',removed_without_evidence=missing,diff=pin(ROOT/'out/CAMERA_KR9C_DIFF.json')))
 status(2,f'Camera A retains {variants["camera_wording"]["row_count"]} rows. Camera B retains {variants["camera_B"]["row_count"]}. {len(diff)} frame references differ between kr9c and k6tk pins, affecting {len(affected)} source rows.')

def stage3():
 from student_pilot.r2_exclusions import Exclusions,upstream
 from student_pilot.r2_withheld import Withheld
 from student_pilot.s1_exclusions import Exclusions as NativeExclusions
 from student_pilot.r2_scene_bindings import require_merged
 from student_pilot.row_removals import Removals
 from student_pilot.r2_adapters import normalize
 from student_pilot.s1_routing import Frames
 from student_pilot.r1_persisted import scope
 ds=drafts();camera=load(ROOT/'out/CAMERA_SELECTION.json');load(ROOT/'out/PHRASE_DECISION.json')
 cfg=load(BASE/'tree_rebuild10_w/w24/out/N_LAUNCH_CONFIG.json')
 for p in cfg['remove_files']:pin(p['path'],p['sha256'])
 removals=Removals(cfg['remove_files'])
 fps=framepins();fm=Frames(fps['frame_map'],fps['frame_plan'],fps_authority=fps['fps_authority'])
 e=ds['recovery'];exclusions={k:staged(v) for k,v in e['exclusions'].items()}
 withheld_pin=staged(e['withheld_rooms']);merged_pin=staged(e['dev_scene_exclusions'])
 manifest={}
 with scope(MAPS):
  rule=Exclusions(exclusions);withheld=Withheld(withheld_pin);require_merged(merged_pin)
  merged=NativeExclusions(merged_pin,exclusions['benchmark'])
  def assess(raw,coverage):
   row=normalize(raw,fm);reasons=rule.check(row,coverage)
   if withheld.touches(row,coverage):reasons.append('withheld_room')
   if merged.excluded(row):reasons.append('merged_dev_or_benchmark')
   # The actual tree removal predicate, including the K1 union and defect restrictions.
   hits=removals.match(raw)
   if hits:reasons.append('remove_files')
   return row,reasons,hits
  for name in NAMES+['camera_B']:
   e=ds['camera_wording' if name=='camera_B' else name]
   selection=camera['variants'].get(name)
   src=selection['rows'] if selection else e['rows'];pin(src['path'],src['sha256'])
   source_cov=selection['coverage'] if selection else e['scene_coverage'];cov=load(source_cov['path'])
   original_counts={};drop=[];kept=[];matches={}
   for r in rows(src['path']):
    q=r['qid'];row,reasons,hits=assess(r,cov['rows'][q]);kind=row.get('question_type',row.get('type','routing'))
    c=original_counts.setdefault(kind,dict(seen=0,admitted=0,refused=0,reasons=Counter()));c['seen']+=1
    if reasons:
     c['refused']+=1;c['reasons'][','.join(reasons)]+=1;drop.append(dict(row_key=q,reasons=reasons,matched_remove_files=[cfg['remove_files'][i] for i in hits]));matches[q]=hits
    else:c['admitted']+=1;kept.append(q)
   keep=set(kept)
   if drop:
    dest=ROOT/f'out/rows/{name}_retained.jsonl';dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('w') as f:
     for line,r in lines(src['path']):
      if r['qid'] in keep:f.write(line)
    final=pin(dest)
   else:final=src
   rem=write(f'out/REMOVE_{name}_exclusions.json',dict(source=src,rows=drop,row_count=len(drop),prior_camera_remove=selection['remove'] if selection else None,semantics='QID removals only from the exact source pin; no radiator replacement removals are active.'))
   cp=write(f'out/coverage/{name}_final.json',dict(rows_sha256=final['sha256'],exclusions=exclusions,rows={q:cov['rows'][q] for q in kept},source_coverage=source_cov,scope='Exact QID subset of independently witnessed coverage.'))
   # Rerun all predicates on every row of the final file. Receipt counts attest this file only.
   counts={};checked=0
   for r in rows(final['path']):
    row,reasons,hits=assess(r,cov['rows'][r['qid']]);kind=row.get('question_type',row.get('type','routing'))
    c=counts.setdefault(kind,dict(seen=0,admitted=0,refused=0,reasons=Counter()));c['seen']+=1;checked+=1
    if reasons:c['refused']+=1;c['reasons'][','.join(reasons)]+=1
    else:c['admitted']+=1
   assert checked==len(kept)
   rp=write(f'out/upstream/{name}.json',dict(schema='fbp-exclusion-accounting-v1',exclusions=exclusions,counts=counts,source_file=final,source_file_sha256=final['sha256'],coverage=cp,withheld_rooms=withheld_pin,dev_scene_exclusions=merged_pin,remove_files=cfg['remove_files'],attests='All rows of source_file were checked using the unmodified tree Exclusions.check, Withheld.touches, merged-dev exclusion and Removals.match. Counts describe exclusion eligibility, not geometry, raster bytes or full intake. Prior selection accounting is separate.',selection=dict(source=src,counts=original_counts,removed=len(drop),remove_list=rem),prefiltered=bool(drop or selection)))
   up=staged(rp);MAPS[up['sha256']]=str(ROOT/up['path'])
   # Enter a refreshed scope because this receipt was staged after the outer scope began.
   with scope(MAPS):assert upstream([up],exclusions)
   manifest[name]=dict(rows=final,row_count=len(kept),coverage=cp,upstream_receipt=rp,remove=rem,camera_remove=selection['remove'] if selection else None,prefiltered=bool(drop or selection),removed=len(drop),selection_counts=original_counts)
   print(name,len(kept),'removed',len(drop),flush=True)
 write('out/EXCLUSION_ACCOUNTING.json',dict(slices=manifest,exclusions=exclusions,withheld_rooms=withheld_pin,dev_scene_exclusions=merged_pin))
 status(3,'Every selected row has been checked by the native exclusion predicates. Matching rows are removed before final receipts; each final receipt reruns every check and binds exact file and tree hashes.')

def stage4():
 from student_pilot.p3_provenance import digest
 ds=drafts();acc=load(ROOT/'out/EXCLUSION_ACCOUNTING.json');fps=framepins();out={}
 for name,s in acc['slices'].items():
  base=ds['camera_wording' if name=='camera_B' else name]
  family='camera_wording' if name=='camera_B' else name
  bindings={r['qid']:digest(r) for r in rows(s['rows']['path'])}
  # Raw membership must be inherited, never synthesized for unrecognized source rows.
  assert all(base['row_bindings'][q]==h for q,h in bindings.items())
  e={k:base[k] for k in ['schema','stream','trace_contract','validator_sha256']}
  e.update(family=family,count=s['row_count'],rows=staged(s['rows']),row_bindings=bindings,scene_coverage=staged(s['coverage']),upstream_receipts=[staged(s['upstream_receipt'])],prefiltered=s['prefiltered'],exclusions=acc['exclusions'],withheld_rooms=acc['withheld_rooms'],dev_scene_exclusions=acc['dev_scene_exclusions'],extent_receipt=staged(base['extent_receipt']),required_exclusion_pins={k:staged(v) for k,v in base['required_exclusion_pins'].items()})
  for p in [*base['exclusions'].values(),base['withheld_rooms'],base['dev_scene_exclusions']]:staged(p)
  if name not in ['camera_wording','camera_B']:e.update({k:staged(v) for k,v in fps.items()})
  else:e['frame_metadata_mode']='Embedded kr9c pins, indices, timestamps, fps and total_num_frames; no RGB substitution.'
  if base.get('mix_cells'):e['mix_cells']={q:v for q,v in base['mix_cells'].items() if q in bindings}
  e['source_draft']=pin(INV/f'work/envelopes/{family}.json')
  out[name]=dict(envelope=write(f'out/envelopes/{name}.json',e),row_count=s['row_count'])
 write('out/ENVELOPE_INDEX.json',dict(slices=out,resolution='Active pins carry u/<sha256>. Dry intake runs with cwd at this workspace and r1_persisted.scope mapping each hash to the absolute workspace/u/<sha256>. Withheld.touches reader uses its u/<sha256> path directly relative to cwd. Production must stage identical bytes under its own u/ directory, establish the same hash-to-absolute-path scope and use that staging root as cwd, or fully localize all active nested pins and regenerate coverage/receipt/envelope hashes together. PNG paths stay /data2/k6tk and /data2/kr9c and require Q_E4.'))
 write('out/STAGED_INPUTS.json',dict(paths=MAPS,files=[dict(staged_name='u/'+h,path=p,source_path=str(Path(p).resolve()),sha256=h,bytes=Path(p).stat().st_size) for h,p in sorted(MAPS.items())],production='Copy the referent bytes once to staging_root/u/<sha256>; these local symlinks are not production byte-staging proof.'))
 status(4,'Six final envelopes and camera B are complete. Active metadata pins use u/<sha256>; the resolver and direct withheld-room path requirements are recorded in ENVELOPE_INDEX.json.')


if __name__=='__main__':
 COMMAND=PREFIX+'work/route.py '+sys.argv[1]
 pin(__file__);pin(BASE/'tree_rebuild10_w/w24/out/TREE_SEAL.json');pin(INV/'out/FULL_INVENTORY.json');pin(INV/'out/FULL_INVENTORY.md')
 globals()['stage'+sys.argv[1]]()
