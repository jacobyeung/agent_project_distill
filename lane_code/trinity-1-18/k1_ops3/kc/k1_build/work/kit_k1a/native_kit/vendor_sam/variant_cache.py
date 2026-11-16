"""One-card delta inference. Reuse unchanged baseline calls; preserve source scores."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from kitlib import *
from variantlib import *
from cache_masks import timed
import argparse,time,shutil,copy,io
from sam_backend import rle_encode

def baseline_parity(old,new):
 keep=[p for p in new['instances'] if p['joint_score']>=.2][:10]
 if [p['query'] for p in keep]!=[p['query'] for p in old['instances']]:raise ValueError('Dense baseline subset query mismatch')
 for a,b in zip(old['instances'],keep):
  if abs(a['score']-b['score'])>.001 or abs(a['joint_score']-b['joint_score'])>.001:raise ValueError('Dense baseline subset score mismatch')
  aa,bb=decode(a['mask']),decode(b['mask']);union=np.logical_or(aa,bb).sum()
  if union and np.logical_and(aa,bb).sum()/union<.99:raise ValueError('Dense baseline subset mask mismatch')

def merge_record(base,extra,hw,source,box=None):
 out=copy.deepcopy(base)
 for p in out['instances']:p.setdefault('source_presence',base['presence']);p.setdefault('source_prompt',base['prompt'])
 for p in extra['instances']:
  p=copy.deepcopy(p);p['source_query']=p['query'];p['source_presence']=extra['presence'];p['source_prompt']=source
  if box:
   x,y,x2,y2=box;m=np.zeros(hw,bool);m[y:y2,x:x2]=decode(p['mask']);p['mask']=rle_encode(m);p['box']=[p['box'][0]+x,p['box'][1]+y,p['box'][2]+x,p['box'][3]+y];p['source_tile']=list(box)
  mask=decode(p['mask'])
  if any((lambda b:np.logical_and(mask,b).sum()/max(1,np.logical_or(mask,b).sum())>.95)(decode(q['mask'])) for q in out['instances']):continue
  out['instances'].append(p)
 out['instances']=sorted(out['instances'],key=lambda p:-p['score'])
 for j,p in enumerate(out['instances']):p['query']=j
 out['n_above_floor']=len(out['instances']);out['joint_score']=max((p['joint_score'] for p in out['instances']),default=-1.)
 return out

def load_presence(path,m):
 if not path:raise ValueError('Student gate requires bound per-frame presence rows')
 data=rows(path);out={};e=m['experiment']
 if sha(path)!=e['presence_sha256']:raise ValueError('Student presence file pin mismatch')
 expected={(c['scene'],ph,k):(c['anchor_indices'][k],c['frames'][k]['sha256']) for c in m['captures'] for ph in c['phrases'] for k in range(32)}
 for r in data:
  key=(r['scene'],r['phrase'],r['slot'])
  if key in out or key not in expected:raise ValueError('Duplicate/unexpected presence row')
  if r.get('stub') or r.get('oracle') or not r.get('checkpoint_id') or not r.get('binding'):raise ValueError('Unbound/stub/oracle presence')
  if (r['frame_index'],r['frame_sha256'])!=expected[key] or not isinstance(r['p_yes'],(float,int)) or not np.isfinite(r['p_yes']) or not 0<=r['p_yes']<=1:raise ValueError('Presence frame/probability mismatch')
  out[key]=r['p_yes']
 if set(out)!=set(expected):raise ValueError('Presence coverage incomplete')
 return out

def verify_baseline(cache,c,m):
 sid=c['scene'].replace('/','__');p=Path(cache)/(sid+'.npz');base_c={k:v for k,v in c.items() if k!='cache_contract'};e=m['experiment']
 if sha(p)!=e['baseline_cache_sha256'][c['scene']]:raise ValueError('Baseline cache pin')
 raw=validate_cache(load_cache(p),base_c,e['baseline_manifest_sha256'],allow_stub=m.get('test_stub',False));j=rows(Path(cache)/(sid+'.journal.jsonl'))
 if not j or j[-1].get('event')!='complete' or j[-1].get('sha256')!=sha(p):raise ValueError('Baseline journal mismatch')
 return raw

def run(a):
 m=json.loads(Path(a.manifest).read_text());validate_manifest(m);e=m['experiment'];spec=e['spec'];msha=sha(a.manifest)
 combo=spec['mode'] in COMBOS
 if combo and not a.reuse_dense:raise ValueError('Combo variants require --reuse-dense; refusing to start from baseline')
 if combo and code_pins()!=e['inference_code_sha256']:raise ValueError('Inference code differs from the combo manifest pins')
 dense_m=None
 if a.reuse_dense:
  dmp=Path(a.reuse_dense).parent/'MANIFEST.json';dense_m=json.loads(dmp.read_text());validate_manifest(dense_m)
  if dense_m['experiment']['name']!='dense' or dense_m['experiment']['baseline_manifest_sha256']!=e['baseline_manifest_sha256']:raise ValueError('Dense source binding')
  if (dense_m['receipt_sha256'],dense_m['checkpoint_sha256'])!=(m['receipt_sha256'],m['checkpoint_sha256']) or dense_m['experiment']['baseline_cache_sha256']!=e['baseline_cache_sha256']:raise ValueError('Dense source SAM receipt, checkpoint or baseline pins differ')
  if combo:
   d=e['dense_source']
   if sha(dmp)!=d['manifest_sha256'] or sha(Path(a.reuse_dense)/'COMPLETE.json')!=d['complete_sha256'] or sha(Path(a.reuse_dense)/'BINDING.json')!=d['binding_sha256']:raise ValueError('Dense source manifest/receipts differ from combo pins')
 out=scratch(a.out);out.mkdir(parents=True,exist_ok=True)
 if (out/'HALTED.json').exists() and not a.review_halt:raise ValueError('HALTED; operator review required')
 binding=dict(manifest_sha256=msha,stub=a.stub,code_sha256=code_pins(),dense_source_manifest_sha256=sha(Path(a.reuse_dense).parent/'MANIFEST.json') if a.reuse_dense else None)
 if (out/'BINDING.json').exists() and json.loads((out/'BINDING.json').read_text())!=binding:raise ValueError('Resume binding differs')
 dump(out/'BINDING.json',binding)
 presence=load_presence(a.presence,m) if spec['mode']=='student_tiles' else None
 if not a.stub and shutil.disk_usage(out).free < 100*1024**3+a.max_bytes:raise ValueError('100 GiB free reserve plus output cap required')
 if a.stub!=bool(m.get('test_stub',False)):raise ValueError('Stub manifest/run mismatch')
 if not a.stub and (not a.reuse_dense or spec['mode'] in ('dense_aliases','dense_tiles')) and (not os.environ.get('CUDA_VISIBLE_DEVICES') or ',' in os.environ['CUDA_VISIBLE_DEVICES']):raise ValueError('One visible GPU required')
 for key in ('HF_HOME','XDG_CACHE_HOME','TRITON_CACHE_DIR'):os.environ[key]=str(out/'runtime_cache')
 start=time.monotonic();written=sum(p.stat().st_size for p in out.glob('*.npz'));tower=None;feature_cache={}
 def detect(images,phrase,floor,cap,feature_key=None):
  nonlocal tower
  import torch
  import torch.nn.functional as F
  from sam3_tower import attach_sam3_tower,FrameDetections,_map_tensors
  from sam_backend import make_postprocess,detect_prompt,prediction
  torch.set_num_threads(1)
  if tower is None:
   if a.stub:
    from stub_backend import StubBackend
    backend=StubBackend();settings={'device':'cpu'}
   else:
    if torch.cuda.device_count()!=1 or torch.cuda.get_device_properties(0).total_memory<40*1024**3:raise ValueError('One >=40 GiB GPU required')
    scratch(a.checkpoint);scratch(a.source)
    if sha(a.receipt)!=m['receipt_sha256']:raise ValueError('SAM receipt pin mismatch')
    settings=dict(device='cuda',checkpoint_path=a.checkpoint,source_root=a.source,receipt_path=a.receipt);backend=None
   tower=attach_sam3_tower(torch.nn.Linear(1,1),settings,enabled=True,backend=backend);timed(a.stall_seconds,tower._load)
  features=feature_cache.get(feature_key) if feature_key is not None else None
  if features is None:
   features=timed(a.stall_seconds,tower.encode,images)
   if feature_key is not None:feature_cache[feature_key]=features
  ds=timed(a.stall_seconds,detect_prompt,tower,features,phrase,make_postprocess(F,torch,FrameDetections,floor,cap),_map_tensors)
  return [prediction(d,n,phrase,rle_encode) for d,n in ds]
 expected_receipt=None if a.stub else json.loads(Path(a.receipt).read_text())
 if not a.stub and sha(a.receipt)!=m['receipt_sha256']:raise ValueError('SAM receipt pin mismatch')
 from PIL import Image
 for c in m['captures']:
  sid=c['scene'].replace('/','__');path=out/(sid+'.npz');journal=out/(sid+'.journal.jsonl')
  def event(kind,**kw):
   with journal.open('a') as f:f.write(json.dumps(dict(event=kind,scene=c['scene'],elapsed_seconds=time.monotonic()-start,**kw))+'\n');f.flush();os.fsync(f.fileno())
   print(sid,kind,flush=True)
  if path.exists():
   validate_cache(load_cache(path),c,msha,a.stub);j=rows(journal)
   if not j or j[-1].get('event')!='complete' or j[-1].get('sha256')!=sha(path):raise ValueError('Uncommitted/corrupt output; use a fresh directory')
   print(sid,'resume_validated',flush=True);continue
  if ((out/'STOP').exists() and (out/'STOP').read_text().strip()!='RESUME') or time.monotonic()-start>=a.max_seconds or written>=a.max_bytes:return 4
  raw=verify_baseline(a.baseline_cache,c,m);value=copy.deepcopy(raw);event('start')
  ims=None;feature_cache.clear()
  if a.reuse_dense:
   source=Path(a.reuse_dense)/(sid+'.npz');source_m=Path(a.reuse_dense).parent/'MANIFEST.json';sm=dense_m
   if combo and sha(source)!=e['dense_source']['npz_sha256'][c['scene']]:raise ValueError('Dense source NPZ differs from combo pin')
   v=load_cache(source)
   sc=next(x for x in sm['captures'] if x['scene']==c['scene'])
   if {k:x for k,x in sc.items() if k!='cache_contract'}!={k:x for k,x in c.items() if k!='cache_contract'}:raise ValueError('Dense source capture identity differs')
   validate_cache(v,sc,sha(source_m),a.stub)
   if v.get('receipt')!=expected_receipt:raise ValueError('Dense source cached SAM receipt differs')
   sj=rows(Path(a.reuse_dense)/(sid+'.journal.jsonl'))
   if not sj or sj[-1].get('event')!='complete' or sj[-1].get('sha256')!=sha(source):raise ValueError('Dense source journal')
   value=copy.deepcopy(v);event('reuse_dense',sha256=sha(source))
  if not a.reuse_dense or spec['mode'] in ('dense_aliases','dense_tiles'):
   for ph in c['phrases']:
    extra_ph=e['prompt_expansions'][ph] if spec['mode'] in ('aliases','dense_aliases') else [ph]
    slots=selected_slots(value if spec['mode']=='dense_tiles' else raw,ph,spec,presence,c['scene']) if 'tiles' in spec['mode'] else list(range(32))
    if not extra_ph or not slots:continue
    if ims is None:
     ims=[]
     for f in c['frames']:
      p=scratch(Path(a.frames)/f['path'])
      if sha(p)!=f['sha256']:raise ValueError('Frame SHA mismatch')
      with Image.open(p) as im:
       if list(im.size)!=c['hw'][::-1]:raise ValueError('Frame raster mismatch')
       ims.append(im.convert('RGB'))
     event('frames_verified')
    for prompt in extra_ph:
     if 'tiles' in spec['mode']:
      boxes=tile_boxes(c['hw']);images=[ims[k].crop(box) for k in slots for box in boxes];preds=detect(images,prompt,spec['floor'],spec['cap'])
      for (k,box),rec in zip([(k,b) for k in slots for b in boxes],preds):value['frames'][str(k)]['phrases'][ph]=merge_record(value['frames'][str(k)]['phrases'][ph],rec,c['hw'],prompt,box)
     else:
      preds=detect(ims,prompt,spec['floor'],spec['cap'],feature_key='full')
      for k,rec in enumerate(preds):
       if spec['mode']=='dense':baseline_parity(raw['frames'][str(k)]['phrases'][ph],rec)
       value['frames'][str(k)]['phrases'][ph]=rec if spec['mode']=='dense' else merge_record(value['frames'][str(k)]['phrases'][ph],rec,c['hw'],prompt)
     event('prompt_complete',phrase=prompt,slots=slots)
  if tower is not None and value.get('receipt')!=tower.receipt:raise ValueError('Cached SAM receipt differs from the live receipt')
  value.update(manifest_sha256=msha,contract=m['density'],stub=a.stub,experiment=e['name'],baseline_sha256=e['baseline_cache_sha256'][c['scene']])
  validate_cache(value,c,msha,a.stub)
  b=io.BytesIO();np.savez_compressed(b,payload=np.frombuffer(json.dumps(value,allow_nan=False).encode(),np.uint8))
  if written+b.tell()>a.max_bytes:event('write_cap');return 4
  with path.open('xb') as f:f.write(b.getbuffer());f.flush();os.fsync(f.fileno())
  written+=path.stat().st_size;event('complete',sha256=sha(path),bytes=path.stat().st_size)
 dump(out/'COMPLETE.json',dict(manifest_sha256=msha,captures=len(m['captures']),seconds=time.monotonic()-start,bytes=written,stub=a.stub));return 0

def main():
 p=argparse.ArgumentParser(__doc__)
 for n in ['manifest','baseline-cache','out']:p.add_argument('--'+n,required=True)
 for n in ['frames','checkpoint','source','presence','reuse-dense']:p.add_argument('--'+n)
 p.add_argument('--receipt',default=str(HERE/'vendor/SAM3_RECEIPT.json'));p.add_argument('--stub',action='store_true');p.add_argument('--review-halt',action='store_true');p.add_argument('--stall-seconds',type=float,default=900);p.add_argument('--max-seconds',type=float,default=7200);p.add_argument('--max-bytes',type=int,default=500_000_000)
 a=p.parse_args()
 if json.loads(Path(a.manifest).read_text()).get('experiment',{}).get('name') in COMBOS and not a.reuse_dense:p.error('combo variants require --reuse-dense')
 try:return run(a)
 except Exception as ex:
  out=scratch(a.out);out.mkdir(parents=True,exist_ok=True);dump(out/'HALTED.json',dict(error=type(ex).__name__+': '+str(ex),automatic_retry=False));raise
if __name__=='__main__':sys.exit(main())
