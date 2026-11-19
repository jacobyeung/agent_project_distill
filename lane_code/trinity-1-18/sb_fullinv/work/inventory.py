"""Read pinned metadata and produce an inventory; never access RGB or remote roots."""
import os, sys, json, hashlib, time, collections, tarfile, traceback, resource
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w')
W=BASE/'w21/work'; TREE=W/'tree_r1'; CHECK=Path('/scratch/jjyeung/orch_n30/sb_auditfix2')
resource.setrlimit(resource.RLIMIT_AS,(36*1024**3,36*1024**3))
sys.dont_write_bytecode=True
sys.path.insert(0,str(TREE))
from student_pilot.p3_provenance import digest
from student_pilot.carrier_c1_routing import alias_of
from student_pilot.r2_intake import intake
from student_pilot.r2_contract import CONTRACT
from student_pilot.r2_grammar import SHARED_SHA256
from student_pilot.r1_coverage import rewording
inputs={}
def pin(path):
 p=Path(path)
 if str(p) not in inputs:
  if not str(p).startswith(('/scratch/','/tmp/')): raise ValueError('Forbidden read '+str(p))
  if not p.is_file(): inputs[str(p)]={'status':'MISSING','sha256':'MISSING'}
  else:
   h=hashlib.sha256()
   with p.open('rb') as f:
    for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
   inputs[str(p)]={'sha256':h.hexdigest(),'bytes':p.stat().st_size}
 return {'path':str(p),'sha256':inputs[str(p)]['sha256']}
def load(path):
 pin(path);return json.loads(Path(path).read_text())
def write(path,obj,deps=None):
 p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
 if isinstance(obj,dict):obj['inputs']=deps if deps is not None else dict(inputs)
 p.write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n');return pin(p)
def norm(s):return s.replace('scannetppv2/','scannetpp/')
specs=load(W/'build21/inputs/row_sources.json');cfg=load(W/'build21/inputs/config.json')
extent=load(W/'build21/inputs/extent.json');deriv=load(W/'build21/proofs/v2h/DERIVATIONS.json')
catalog=load(W/'build21/inputs/source_membership.json')
for p in [BASE/'w21/out/BUILD21H_REPORT.md',W/'build21h/HOST_FLAG_BLOCKER.json',W/'build21/bind21.py',BASE/'ext/pwrap/b/c.sh',BASE/'inputs/p_runtime/A_runtime_673bc60f.json',Path(__file__)]:pin(p)
for name in ('r1_routing','r1_coverage','r2_intake','r2_frames','s1_routing','s1_admission','job_env','p3_provenance','r2_exclusions','r2_withheld','r2_scene_bindings','r0_exclusion','r2_contract','r2_grammar','r2_adapters','extent_receipt','r1_rooms'):
 pin(TREE/'student_pilot'/f'{name}.py')
pin(TREE/'launch_r1/entry.py')
fixture=load(W/'build21/proofs/capacity/absolute_distance/MANIFEST.json')
exclusions=fixture['exclusions']
for p in exclusions.values(): assert pin(p['path'])==p
lists=load(CHECK/'inputs/lists/manifest.json')
five={name:pin(CHECK/'inputs/lists'/p['path']) for name,p in lists['lists'].items()}
authority=load(CHECK/'inputs/lists/authority_aliases.raw')
tiered=load(CHECK/'inputs/lists/TIERED_ALIAS_MAP.raw')
archive=Path('/scratch/jjyeung/n30_mirror/b08_headrows/b08_partB_kit.tar');archive_pin=pin(archive)
with tarfile.open(archive) as t:raw=t.extractfile('work/auth/alias_map.json').read()
assert hashlib.sha256(raw).hexdigest()=='488480ab4b7f352eba9c81e99313c8bfcc247e9cc463a11620be087a42f579cf'
archived=json.loads(raw)
(ROOT/'work/archived_alias_map.raw').write_bytes(raw)
archive_member=pin(ROOT/'work/archived_alias_map.raw')
write('work/archived_alias_map.json',{'archive':archive_pin,'member':'work/auth/alias_map.json','member_pin':archive_member}, {archive_pin['path']:inputs[archive_pin['path']]})
runtime=load(BASE/'ext/m400real/r.json');remote_root=BASE/'ext/m400real/files'
pcfgpath=remote_root/runtime['config']['path'].lstrip('/');pcfg=load(pcfgpath)
base_original=pcfg['streams']['routing'];base_local=remote_root/base_original['path'].lstrip('/');receipt=load(base_local)
metadata={}
for key in ('frame_map','frame_plan','fps_authority'):
 p=cfg['s1_routing'][key];candidates=[Path(p['path']),remote_root/p['path'].lstrip('/'),BASE/'w21/fixtures/work/kit07ca49df_meta/m/k'/Path(p['path']).name]
 found=[]
 for q in candidates:
  if q.is_file() and pin(q)['sha256']==p['sha256']:found.append(pin(q))
 metadata[key]={'expected':p,'local_matches':found,'probed_paths':[str(q) for q in candidates],'status':'EXISTS' if found else 'MISSING','bytes':inputs[found[0]['path']]['bytes'] if found else 'MISSING'}
fps=load(metadata['fps_authority']['local_matches'][0]['path']) if metadata['fps_authority']['local_matches'] else {}
scene_ref=remote_root/pcfg['scene_coverage']['reference']['path'].lstrip('/');ref=load(scene_ref)
kit=load(BASE/'ext/pwrap/k/0.json')
frame_audits=[]
for p in remote_root.glob('scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/6ed2c7aa/inputs/frames_*/frames.json'):
 d=load(p);frame_audits.append({'pin':pin(p),'report':d,'scope':'P retained population, not proof of current N slices or current remote presence'})
allrows={};slices={};frame_union=set()
for name in ('recovery','absolute_distance','units','coverage_distance','coverage_units'):
 start=time.monotonic();sp=specs[name]['source'];actual=pin(sp['path']);assert actual==sp,(name,actual,sp)
 with Path(sp['path']).open() as f:rows=[json.loads(x) for x in f if x.strip()]
 allrows[name]={r.get('row',r)['qid']:r for r in rows}
 binds={};scenes=collections.Counter();tokens=collections.Counter();keys=set();refs=0;cov={};evidence=collections.Counter();uncovered=[];bad_claims=[];requests=[]
 for rawrow in rows:
  r=rawrow.get('row',rawrow);q=r['qid'];assert q not in binds;binds[q]=digest(rawrow)
  claim=r.get('canonical') or r.get('provenance',{}).get('canonical')
  if r.get('dataset'):
   token=r['dataset']+'/'+r['scene']
  else:
   matches=[k for k in archived if k.split('/',1)[1]==r['scene']]
   assert len(matches)==1,(q,'External alias-map token ambiguous or absent',matches)
   token=matches[0]
   assert token==alias_of(claim),(q,'Native normalization differs from external map token')
  tokens[token]+=1
  if claim:scenes[norm(claim)]+=1
  independent=archived.get(token)
  if independent:evidence['archived_original_alias_map_rows']+=1
  elif token in authority:independent=authority[token];evidence['authority_aliases_rows']+=1
  if independent and claim and norm(independent)!=norm(claim):bad_claims.append(q);independent=None
  if independent:
   cov[q]={'status':'known','names':sorted({token,independent}),'evidence':archive_member if token in archived else pin(CHECK/'inputs/lists/authority_aliases.raw')}
  else:uncovered.append(q);cov[q]={'status':'MISSING','names':'MISSING','evidence':'MISSING'}
  inds=r.get('frame_indices') or r.get('student_input',{}).get('frame_indices') or r.get('provenance',{}).get('frame_indices')
  refs+=len(inds or []);keys.update((token,i) for i in inds or [])
  requests.append({'qid':q,'scene_token':token,'indices':inds if inds is not None else 'MISSING','physical_paths':'MISSING','frame_hashes':'MISSING'})
 deps={str(Path(sp['path'])):inputs[sp['path']],str(TREE/'student_pilot/p3_provenance.py'):inputs[str(TREE/'student_pilot/p3_provenance.py')]}
 bp=write(f'work/bindings/{name}.json',{'source':sp,'count':len(binds),'row_bindings':binds},deps)
 cp=write(f'work/coverage/{name}.json',{'rows_sha256':sp['sha256'],'exclusions':exclusions,'rows':cov,'complete':not uncovered,'missing_qids':uncovered,'scope':'Independent archived alias-map membership, not a raster identity proof.'})
 fp=write(f'work/frames/{name}.json',{'source':sp,'rows':requests,'frame_references':refs,'unique_scene_ordinal_requests':len(keys),'unique_physical_frames':'MISSING','total_rgb_bytes':'MISSING','reason':'Pinned frame_map and frame_plan bytes absent at probed local paths; no raster paths or hashes inferred.'},deps)
 auditpath=ROOT/'work/audits_native'/name/'audit.json';audit=load(auditpath)
 pins_for_draft={'scene_coverage':cp,'frame_map':metadata['frame_map']['local_matches'][0] if metadata['frame_map']['local_matches'] else 'MISSING','frame_plan':metadata['frame_plan']['local_matches'][0] if metadata['frame_plan']['local_matches'] else 'MISSING','fps_authority':metadata['fps_authority']['local_matches'][0] if metadata['fps_authority']['local_matches'] else 'MISSING'}
 env={'schema':'r2-family-manifest-v1','family':name,'stream':'routing','count':len(rows),'rows':sp,'trace_contract':CONTRACT,'validator_sha256':SHARED_SHA256,'row_bindings':binds,'exclusions':exclusions,'dev_scene_exclusions':cfg['dev_scene_exclusions'],'withheld_rooms':five['withheld-80'],'extent_receipt':cfg['extent_receipt'],'prefiltered':'MISSING','upstream_receipts':'MISSING','required_exclusion_pins':five,'exclusion_audit':pin(auditpath),'draft_status':'NOT_ADMISSIBLE','missing_notes':{'prefiltered':'No authenticated full-population upstream exclusion accounting identified. This string is a draft placeholder, not a boolean.','upstream_receipts':'MISSING: authentic r2_exclusions.upstream-compatible receipt list.','scene_coverage':'Complete independently pinned map coverage' if not uncovered else 'MISSING for listed QIDs','frame_host_stage_receipt':'MISSING; not an intake field','K1':'Required task rule; not a direct r2_intake envelope predicate'},**pins_for_draft}
 ep=write(f'work/envelopes/{name}.json',env)
 dry=[]
 for limit in (None,2000):
  try:
   items,report=intake(ep['path'],limit=limit);dry.append({'limit':limit,'status':'RETURNED','admitted':len(items),'report':report})
  except Exception as e:
   tb=traceback.extract_tb(e.__traceback__);dry.append({'limit':limit,'status':'REFUSED','exception':type(e).__name__,'message':str(e),'location':{'file':tb[-1].filename,'line':tb[-1].lineno},'stack':[{'file':x.filename,'line':x.lineno,'function':x.name} for x in tb]})
 result={'source':sp,'source_bytes':inputs[sp['path']]['bytes'],'rows':len(rows),'row_bindings_count':len(binds),'row_bindings':bp,'duplicate_qids':len(rows)-len(binds),'catalog_missing_qids':sorted(set(binds)-set(catalog['sources'][name]['qids'])),'scenes_claimed':dict(sorted(scenes.items())),'scene_tokens':dict(sorted(tokens.items())),'scene_count':len(scenes),'independent_coverage':{'receipt':cp,'complete':not uncovered,'missing_qids':uncovered,'conflicting_qids':bad_claims,'counts':dict(evidence)},'frames':{'request_inventory':fp,'references':refs,'unique_scene_ordinals':len(keys),'physical_count':'MISSING','bytes':'MISSING','remote_staged_count':'MISSING','remote_stage_receipt':'MISSING','logical_store':'/data2/k6tk','metadata':metadata},'exclusions':{'audit':pin(auditpath),'status':audit['status'],'complete':audit['complete'],'hits':audit['hits'],'all_five_zero':audit['complete'] and not any(audit['hits'].values())},'extent':{'pin':cfg['extent_receipt'],'qid_entries':sum(q in extent['rows'] for q in binds),'missing_qids':sorted(set(binds)-set(extent['rows'])),'normalized_content_validation':'MISSING: no real RGB metadata join; no synthetic frames supplied','derivation_entries':sum(q in deriv['rows'] for q in binds)},'draft_envelope':ep,'dry_validation':dry,'seconds':time.monotonic()-start}
 slices[name]=result;frame_union.update(keys)
 print(name,json.dumps({k:result[k] for k in ('rows','scene_count','seconds')}),dict(evidence),'missing',len(uncovered),'frames',len(keys),flush=True)
camera={'schema':'r2-family-manifest-v1','family':'MISSING','stream':'routing','trace_contract':CONTRACT,'validator_sha256':SHARED_SHA256,'exclusions':exclusions,'required_exclusion_pins':five,'dev_scene_exclusions':cfg['dev_scene_exclusions'],'withheld_rooms':five['withheld-80'],'extent_receipt':cfg['extent_receipt'],'draft_status':'MISSING_SOURCE','rows':'MISSING','count':'MISSING','row_bindings':'MISSING','scene_coverage':'MISSING','frame_map':'MISSING','frame_plan':'MISSING','fps_authority':'MISSING','upstream_receipts':'MISSING','prefiltered':'MISSING','missing_notes':{'source':'/scratch/jjyeung/orch_n30/sb_rowA2/out/ report and its named row file do not exist locally','family':'camera_wording is only the inventory filename; its native family binding is MISSING. Camera is not a sixth source_names entry. Tree owner must specify integration; do not add it silently.'}}
ep=write('work/envelopes/camera_wording.json',camera);dry=[]
for limit in (None,2000):
 try:intake(ep['path'],limit=limit)
 except Exception as e:
  tb=traceback.extract_tb(e.__traceback__);dry.append({'limit':limit,'exception':type(e).__name__,'message':str(e),'location':{'file':tb[-1].filename,'line':tb[-1].lineno}})
slices['camera_wording']={'status':'MISSING','expected_directory':'/scratch/jjyeung/orch_n30/sb_rowA2','directory_exists':Path('/scratch/jjyeung/orch_n30/sb_rowA2').exists(),'source':'MISSING','rows':'MISSING','source_pin':'MISSING','exclusion_audit':'MISSING','scene_coverage':'MISSING','frames':'MISSING','extent_binding':'MISSING: config receipt known; camera row membership cannot be assessed','draft_envelope':ep,'dry_validation':dry}
for name,parent in [('coverage_distance','absolute_distance'),('coverage_units','units')]:
 count=0;errors=[]
 for q,r in allrows[name].items():
  d=deriv['rows'].get(q)
  try:
   assert d is not None and d['source_sha256']==specs[name]['source']['sha256']
   pr=allrows[parent][d['parent_qid']];rewording(r,pr)
   assert d['content_sha256']==extent['rows'][q]['content_sha256'];count+=1
  except Exception as e:errors.append({'qid':q,'error':str(e)})
 slices[name]['extent']['verified_exact_rewording_and_inherited_receipt_entries']=count
 slices[name]['extent']['derivation_errors']=errors
stores=[]
for label,p in [('routing_base',base_original),('vqa_N',cfg['streams']['vqa']),('pointing_N',cfg['streams']['pointing']),('pose',pcfg['streams']['pose'])]:
 local=Path(p['path']) if Path(p['path']).is_file() else remote_root/p['path'].lstrip('/')
 if local.is_file():
  d=load(local)
  selected=[d] if 'database' in d else []
  for source in d.get('sources',[]):
   if source.get('receipt'):
    q=remote_root/source['receipt']['path'].lstrip('/')
    if q.is_file():selected.append(load(q))
  for doc in selected:
   db=doc['database'];q=Path(db['path']);localdb=q if q.is_file() else remote_root/db['path'].lstrip('/')
   stores.append({'label':label,'receipt':pin(local),'database':db,'local_status':'EXISTS' if localdb.is_file() else 'MISSING','local_bytes':localdb.stat().st_size if localdb.is_file() else 'MISSING','reported_rows':doc.get('count'),'scope':'Receipt identity, not current remote byte verification'})
frame_archives=[{k:v for k,v in a.items() if k!='inventory'} for a in kit['staged_inputs']['archives'] if a['destination']=='data2root/k6tk']
out={'schema':'full-native-routing-inventory-v1','host':os.uname().nodename,'command':'nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -B work/inventory.py','slices':slices,'routing_base':{'runtime':pin(BASE/'ext/m400real/r.json'),'config':pin(pcfgpath),'original_pin':base_original,'local_pin':pin(base_local),'schema':receipt['schema'],'scene_role':receipt['scene_role'],'heldout_overlap':receipt['heldout_overlap'],'database':receipt['database'],'division':receipt['division'],'N_config_current':cfg['streams']['routing']},'frame_host':{'metadata':metadata,'unique_scene_ordinals_all_five':len(frame_union),'required_store_databases':stores,'recorded_P_frame_audits':frame_audits,'recorded_P_frame_archives':frame_archives,'recorded_P_archive_bytes':sum(a['bytes'] for a in frame_archives),'recorded_P_archive_members':sum(a.get('members',0) for a in frame_archives),'stage_status':'MISSING: no current N slice-specific frame staging receipt; P archive totals do not establish N coverage'},'independent_candidates':[{'pin':archive_pin,'member':'work/auth/alias_map.json','member_pin':archive_member,'independent_of_slice_claims':True,'scope':'Archived original map, retrieved and member hash verified; no raster proof'},{'pin':pin(CHECK/'inputs/lists/authority_aliases.raw'),'independent_of_slice_claims':True,'scope':'External ARKit alias mapping; no raster proof'},{'pin':pin(CHECK/'inputs/lists/authority_visits.raw'),'independent_of_slice_claims':True,'scope':'Capture to physical venue; does not alone bind a row to a scene'},{'pin':pin(CHECK/'inputs/lists/TIERED_ALIAS_MAP.raw'),'independent_of_slice_claims':'MIXED','scope':'Tier A source-row claims are not independent; tier B archived-map witnesses are independent; tier C needs external candidate provenance.'},{'pin':pin(scene_ref),'independent_of_slice_claims':True,'scope':'Dev-S1 reference, not full N row-to-scene coverage'},{'pin':cfg['extent_receipt'],'independent_of_slice_claims':False,'scope':'Extent audit binds supervision geometry; does not independently establish scene identity'},{'pin':pin(W/'build21/proofs/v2h/DERIVATIONS.json'),'independent_of_slice_claims':False,'scope':'Exact wording inheritance, not scene identity or RGB coverage'}],'exclusion_pins':five,'limitations':['No source, launcher, tmux session, process or Git state was modified outside this workspace.','No RGB was copied or read; no network or GPU was used.','Source-room resolution PASS does not imply zero excluded rows.','MISSING placeholders intentionally fail native validation; unknowns are not admission evidence.']}
write('work/INVENTORY_STAGE.json',out)
(ROOT/'STATUS.md').write_text('The five row inventories, per-QID bindings, independent archived-map coverage, exclusion audits, and six envelope drafts are produced. Recovery has 21 K1 hits and units has 262. Native dry-validation records the full-intake host veto and the next local dependency failure. Frame-map/plan bytes and current N frame staging remain missing at the checked paths; the camera lane is absent.\n')
print('DONE',flush=True)
