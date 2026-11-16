"""K1 label-free caching, eligible-room refit, and rendering."""
import argparse,inspect,json,os,sys,time,shutil
from collections import Counter
from pathlib import Path
from types import SimpleNamespace as NS
sys.path[:0]=[str(Path(__file__).parent),str(Path(__file__).parent/'refit')]
import gate
import gt_set as G
sys.path.insert(0,os.environ.get('K1_NATIVE_KIT',str(Path(__file__).resolve().parents[1]/'native_kit')))
import numpy as np
def _native():
 global B,P
 if not globals().get('_sources_verified',False) and (Path(__file__).resolve().parents[1]/'out/DEPENDENCIES.json').exists():
  from verify_sources import verify
  verify();globals()['_sources_verified']=True
 import bindings as B,pipeline as P
def price_reference(*args,**kwargs):
 """Shared frozen pricing comparator; dev-S1 calls must set fixture=True."""
 from backend import price_capture
 return price_capture(*args,**kwargs)
def check_manifest(m,phase="all",gt_set=None,sensitivity=False):
 _native()
 if m.get('production_ready') is not True or m.get('frame_staging_authorized') is not True:raise ValueError('Plan is not staged and admitted for GPU execution')
 if m.get('unresolved_dense_sources') or m.get('unresolved_gt_names'):raise ValueError('Unresolved dense source or GT identity')
 selection=G.load(gt_set,sensitivity)
 if selection is not None and phase!='downstream':raise ValueError('GT sets are downstream only')
 selected,_=G.select(m,selection);selected_ids={c['canonical'] for c in selected}
 inv=B.load(m['inventory']['path'])
 if gate.sha(m['inventory']['path'])!=m['inventory']['sha256'] or not inv['pilot_complete']:raise ValueError('K1 inventory pin differs')
 pilot={c['canonical']:c for c in inv['pilot']}
 if {c['canonical'] for c in m['captures']}!=set(pilot):raise ValueError('K1 requires exact selected capture set')
 for c in m['captures']:
  if not gate.eligible(*c['canonical'].split('/')):raise ValueError('Capture is no longer eligible')
  if c['room']!=pilot[c['canonical']]['room'] or c['k1_split']!=pilot[c['canonical']]['split']:raise ValueError('K1 split differs')
  # o3's split field denotes membership in the training corpus, not K1's internal holdout.
  P.validate_capture(c,dict(complete=True,authorities={'benchmark':True,'dev_s1':True},rooms=[],scenes=[]))
  if c['split']!='train' or not c.get('gt_name_ids_authority'):raise ValueError('GT name mapping authority required')
  si=c['model_row']['student_input']
  if phase in ('all','own') and any(si.get(k) is None for k in ('fps','timestamps','total_num_frames')):raise ValueError('Native source-video metadata is unresolved')
  pins=[c['dense_frames'][i] for i in c['anchor_slots']] if phase=='own' else c['dense_frames'] if phase in ('all','tower_sam') else []
  for pin in pins:B.checked(pin)
  if phase in ('all','downstream') and c['canonical'] in selected_ids:B.checked(c['gt'] if selection is None else selection['entries'][c['canonical']])
 keys={'tower_sam':('tower_weights','tower_config','sam_checkpoint','sam_receipt'),'own':('artifact','config','data_receipt'),'convert':(),'downstream':()}
 for key in keys.get(phase,('artifact','config','data_receipt','tower_weights','tower_config','sam_checkpoint','sam_receipt')):B.checked(m['gpu'][key])
 return m
def native_backend(c,row,geo,raw,policy,dest):
 _native()
 from student_pilot.ground_profiles import build_profile
 from student_pilot.scene_state import FrameMap,SceneState
 source=NS(cache=raw,reader=NS(phrase=B.kitlib.normalize_phrase,rle_decode=B.kitlib.decode),live=None,names=tuple(raw['phrases']),frame_indices=tuple(c['anchor_indices']),identity=B.digest(raw))
 scene=SceneState(c['video_sha256'],FrameMap(tuple(c['anchor_indices'])),geo.identity)
 kwargs=dict(depth_source='tower_scaled',audit_dir=dest,ground_candidate_policy=dict(name='routed_default_v1',weights=B.pin(policy)),question_type=row['type'])
 # The repair tree additionally binds the complete candidate universe before construction.
 from student_pilot.ground_v3 import GroundV3
 if 'expected_candidate_contract' in inspect.signature(GroundV3).parameters:
  from student_pilot.ground_admission import candidate_contract
  kwargs['expected_candidate_contract']=candidate_contract(source,scene.frames.source_indices);kwargs['points_cut_version']='policy-cut-v1'
 backend=build_profile('native_selector',scene,geo,source,**kwargs)
 if backend.geometry_error:raise ValueError(backend.geometry_error)
 backend.allow_own_geometry_fallback=False;backend.geometry_source='checkpoint_conditioned_frozen_g3t';backend.frozen_mask_source=source
 return backend
def cache_capture(c,boundary,dest):
 _native()
 from PIL import Image
 dest=Path(dest);dest.mkdir(parents=True,exist_ok=False);images=[]
 for pin in c['dense_frames']:
  with Image.open(B.checked(pin)) as im:images.append(im.convert('RGB'))
 state=boundary.tower(c,images);anchors=[images[s] for s in c['anchor_slots']]
 if state.frame_indices[state.anchor_slots].tolist()!=c['anchor_indices']:raise ValueError('Tower anchor order differs')
 own,gravity=boundary.own(c,anchors,state)
 geometry=B.geometry.convert(state,own,gravity,images[0].size[::-1],dest/'geometry.npz')
 raw_proposals(c,anchors,boundary,dest)
 receipt=dict(capture_sha256=B.digest(c),checkpoint=boundary.checkpoint,synthetic=boundary.synthetic,geometry=geometry,
   sources=B.source_identity(),files={n:B.pin(dest/n) for n in ['geometry.npz','candidates.json','parity_raw.jsonl']},phase='unselected_cache_no_responses')
 B.write(dest/'CACHE_COMPLETE.json',receipt);return receipt
def raw_proposals(c,anchors,boundary,dest):
 _native()
 # Preserve raw prompt/query identities before alias merging reindexes them.
 original=B.sam_backend.prediction;slots={}
 with (dest/'parity_raw.jsonl').open('x') as parity:
  def record_prediction(det,n_above,prompt,encoder):
   record=original(det,n_above,prompt,encoder);slot=slots.get(prompt,0)%32;slots[prompt]=slots.get(prompt,0)+1
   parity.write(json.dumps(dict(frame_sha256=c['dense_frames'][c['anchor_slots'][slot]]['sha256'],phrase=prompt,prediction=record))+'\n')
   return record
  B.sam_backend.prediction=record_prediction
  try:raw=P.proposals(c,anchors,boundary)
  finally:B.sam_backend.prediction=original
 B.write(dest/'candidates.json',raw)
 return raw
def cached(c,dest):
 _native()
 import k1_guard as guard
 guard.install()
 from student_pilot.ground_profiles import load_geometry
 from student_pilot.scene_state import FrameMap
 dest=Path(dest)
 receipt=B.load(dest/'CACHE_COMPLETE.json')
 if receipt['capture_sha256']!=B.digest(c):raise ValueError('Cache capture differs')
 guard.check_receipt(c,dest,receipt)
 for pin in receipt['files'].values():B.checked(pin)
 raw=B.load(dest/'candidates.json')
 with guard.capture(c):
  if receipt.get('geometry_refusal'):
   try:load_geometry(dest/'REFUSED_GEOMETRY.npz',FrameMap(tuple(c['anchor_indices'])),'tower_scaled')
   except guard.geometry_profiles.GeometryError as error:
    if str(error)!=guard.CODE:raise
   else:raise ValueError('Cache refusal geometry passed reviewed guard')
   geo=None
  else:geo=load_geometry(dest/'geometry.npz',FrameMap(tuple(c['anchor_indices'])),'tower_scaled')
 if guard.verdict(c)!=receipt['gravity_verdict']:raise ValueError('Cache gravity verdict differs')
 return raw,geo,receipt
def gt_canvas(instances):
 """Map integer GT labels onto the deployed mask canvas; reject other shapes."""
 from student_pilot import routed_features as F
 from scipy import ndimage
 if instances.ndim!=3 or not np.issubdtype(instances.dtype,np.integer):raise ValueError('GT requires integer instance-label frames')
 shape=tuple(instances.shape[1:]);canvas=tuple(F.OUTPUT_SHAPE)
 if canvas!=(240,320):raise ValueError('Deployed GT canvas differs')
 if shape==canvas:return instances,'identity'
 if shape!=canvas[::-1]:raise ValueError('GT raster differs; no silent resize')
 # routed_features.resize uses these zoom arguments on bool masks. Sampling
 # integer labels once preserves every instance, including background labels.
 mapped=np.stack([ndimage.zoom(frame,(canvas[0]/shape[0],canvas[1]/shape[1]),order=0,prefilter=False) for frame in instances])
 return mapped,'stretch_nearest_320x240_to_240x320'
def gt_arrays(c,selection=None):
 _native()
 with np.load(B.checked(c['gt'] if selection is None else selection['entries'][c['canonical']]),allow_pickle=False) as z:
  instances,mapping=gt_canvas(z['instances'] if 'instances' in z else z['inst'])
  return dict(instances=instances,frame_indices=z['frame_indices'],gt_canvas_map=mapping)
def tables(m,cache,out,gt_set=None,sensitivity=False):
 _native()
 import build_tables
 import k1_guard as guard
 guard.install();refused={};canvas_maps={}
 selection=G.load(gt_set,sensitivity);captures,meta=G.select(m,selection)
 out=Path(out);out.mkdir(parents=True,exist_ok=False)
 with (out/'candidates.jsonl').open('w') as cf,(out/'pairs.jsonl').open('w') as pf:
  for c in captures:
   raw,geo,receipt=cached(c,Path(cache)/B.digest(c['canonical'])[:16])
   gt=gt_arrays(c,selection);canvas_maps[c['canonical']]=gt['gt_canvas_map']
   if geo is None:
    refused[c['canonical']]=receipt['geometry_refusal']['code'];continue
   with guard.capture(c):rows,pairs=build_tables.build_capture(c,raw,geo,gt)
   for row in rows:cf.write(json.dumps(row)+'\n')
   for row in pairs:pf.write(json.dumps(row)+'\n')
 guard.write_report(out)
 record=dict(geometry_refused=refused,manifest_sha256=B.digest(m),inventory=m['inventory'],producer_sha256=B.sha(build_tables.__file__),build_sha256=gate.sha(gate.ROOT/'grd_selector/work/setsel/build.py'),files={n:B.pin(out/n) for n in ['candidates.jsonl','pairs.jsonl']})
 record.update(gt_canvas_map=canvas_maps,gt_canvas_map_counts=dict(Counter(canvas_maps.values())))
 if meta is None:B.write(out/'TABLE_RECEIPT.json',record)
 else:G.write(out/'TABLE_RECEIPT.json',record,meta)
def responses(m,cache,fit_dir,out,gt_set=None,sensitivity=False):
 _native()
 import render
 import k1_guard as guard
 guard.install()
 selection=G.load(gt_set,sensitivity);captures,meta=G.select(m,selection)
 fit_dir=Path(fit_dir);fit_path=fit_dir/'FIT_RECEIPT.json';fit=B.load(fit_path);policy=fit_dir/'NATIVE_POLICY.json'
 G.require(fit,meta)
 if meta is not None:
  table_pin=fit['table_receipt'];table=B.load(B.checked(table_pin));G.check_table(table,m,selection)
 if fit.get('fixture_only') is not False:raise ValueError('Fixture refit cannot render training responses')
 if B.sha(policy)!=fit['native_policy_sha256']:raise ValueError('Native refit pin differs')
 if fit['inputs'].get(m['inventory']['path'])!=m['inventory']['sha256']:raise ValueError('Refit inventory differs')
 if set(fit['train_rooms'])&set(fit['heldout_rooms']):raise ValueError('Refit room leakage')
 out=Path(out);out.mkdir(parents=True,exist_ok=False);all_rows=[];analysis=[];canvas_maps={}
 for c in captures:
  raw,geo,receipt=cached(c,Path(cache)/B.digest(c['canonical'])[:16]);gt=gt_arrays(c,selection);results=[]
  canvas_maps[c['canonical']]=gt['gt_canvas_map']
  dest=out/B.digest(c['canonical'])[:16];dest.mkdir()
  for row in c['rows']:
   if geo is None:
    record=dict(calls=[dict(call=P.calls_for(row)[0],kind='error',**receipt['geometry_refusal'],response='Geometry refused: '+receipt['geometry_refusal']['message'])])
   else:
    with guard.capture(c):
     backend=native_backend(c,row,geo,raw,policy,dest/'audit') if row['operands'] else None
     record=B.perception.execute_calls(geo,backend,P.calls_for(row))
   for i,call in enumerate(record['calls']):
    if P.failure(call):record['calls']=record['calls'][:i+1];break
   match=P.mask_agreement(record,row,gt,c['anchor_indices']) if not any(P.failure(x) for x in record['calls']) else {'ok':False}
   result=dict(id=row['id'],type=row['type'],calls=record['calls'],mask_match=match,synthetic=False)
   result['decision']=P.classify(row,result,match);results.append(result)
   render_row={k:v for k,v in row.items() if k!='fallback'} if geo is None else row
   rendered=render.render(render_row,result,c,expected_calls_sha256=B.digest(result['calls']),backend_hashes={**receipt['sources'],'native_policy':B.sha(policy)},fixture=False);all_rows.append(rendered)
   analysis.append(dict(id=row['id'],canonical=c['canonical'],type=row['type'],gt_value=row['gt_value'],pred=result['decision']['value'],
     label='excluded' if result['decision']['label']=='left_out' else result['decision']['label'],
     rendered_label=rendered['label'],training_target_available='target' in rendered,printed_cues=printed_cues(result)))
  B.write(dest/'responses.json',results)
  complete=dict(capture_sha256=B.digest(c),sources=receipt['sources'],eligible_refit_sha256=B.sha(fit_path),files={'responses.json':B.pin(dest/'responses.json')})
  if meta is None:B.write(dest/'COMPLETE.json',complete)
  else:G.write(dest/'COMPLETE.json',complete,meta)
 guard.write_report(out)
 render.write_rows(all_rows,out/'rows')
 (out/'K1_ANALYSIS_INPUT.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in analysis))
 record=dict(manifest_sha256=B.digest(m),fit=G.pin(fit_path),gt_canvas_map=canvas_maps,gt_canvas_map_counts=dict(Counter(canvas_maps.values())),files={'analysis':B.pin(out/'K1_ANALYSIS_INPUT.jsonl')})
 if meta is None:B.write(out/'RENDER_RECEIPT.json',record)
 else:G.write(out/'RENDER_RECEIPT.json',dict(record,table_receipt=fit['table_receipt']),meta)
def printed_cues(result):
 _native()
 import re
 calls=result['calls'];body='\n'.join(c['response'] for c in calls);cue={'status':int(any(P.failure(c) for c in calls))}
 counts=[len(m.split(',')) for m in re.findall(r'frames ([0-9,]+)',body)]
 if counts:cue['low_frames']=min(counts)
 spread=[float(x) for x in re.findall(r'spread ([0-9.]+)',body)]
 if spread:cue['spread']=max(spread)
 grounds=[c for c in calls if c['call'].startswith('<ground obj=') and not P.failure(c)]
 if grounds:cue['missing_size']=int(any('size ' not in c['response'] for c in grounds))
 return cue
def cache_run(m,out,boundary,max_seconds=21600,max_bytes=1_500_000_000):
 _native()
 out=Path(out);out.mkdir(parents=True,exist_ok=True);start=time.monotonic()
 if (out/'HALTED.json').exists():raise ValueError('HALTED: operator review and fresh root required')
 identity=dict(manifest_sha256=B.digest(m),sources=B.source_identity(),producer_sha256=gate.sha(__file__))
 if (out/'BINDING.json').exists():
  if B.load(out/'BINDING.json')!=identity:raise ValueError('Resume binding differs')
 else:B.write(out/'BINDING.json',identity)
 try:
  for c in m['captures']:
   if time.monotonic()-start>=max_seconds or ((out/'STOP').exists() and (out/'STOP').read_text().strip()!='RESUME'):return 4
   if not boundary.synthetic and shutil.disk_usage(out).free<100*1024**3+max_bytes:raise ValueError('Disk reserve')
   dest=out/B.digest(c['canonical'])[:16]
   if (dest/'CACHE_COMPLETE.json').exists():cached(c,dest)
   elif dest.exists():raise ValueError('Incomplete capture preserved; use a fresh root after review')
   else:cache_capture(c,boundary,dest)
   with (out/'PROGRESS.jsonl').open('a') as f:f.write(json.dumps(dict(canonical=c['canonical'],elapsed=time.monotonic()-start,receipt_sha256=B.sha(dest/'CACHE_COMPLETE.json')))+'\n')
   if sum(p.stat().st_size for p in out.rglob('*') if p.is_file())>max_bytes:raise ValueError('Output cap')
  return 0
 except Exception as e:
  B.write(out/'HALTED.json',dict(error=repr(e),automatic_retry=False));raise
def main():
 _native()
 from k1_cli import main as launch
 return launch()
if __name__=='__main__':raise SystemExit(main())
