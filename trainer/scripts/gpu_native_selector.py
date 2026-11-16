"""One-card B4 routed read with the native_selector profile; no downloads."""
from pathlib import Path
import argparse,hashlib,json,sys,time
TREE=Path(__file__).resolve().parents[1]
R=TREE if (TREE/'inputs').is_dir() else TREE.parents[1]
sys.path.insert(0,str(TREE))
from student_pilot.trace_version import model_version
from student_pilot.acceptance_evidence import stage_assertions
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
@stage_assertions(6)
def main():
 p=argparse.ArgumentParser(__doc__)
 for n in ['config','artifact','bundle','rows','geometry','sam-source','sam-checkpoint','out']:p.add_argument('--'+n,required=True)
 p.add_argument('--call-mode',choices=('scripted','free'),required=True)
 p.add_argument('--inputs',help='bound LIVE_INPUTS.json; required for scripted token identity')
 p.add_argument('--check-reread',action='store_true')
 p.add_argument('--depth-source',choices=['depth_head','tower_scaled'],default='depth_head');p.add_argument('--max-seconds',type=int,default=3600)
 p.add_argument('--start-check',action='store_true')
 p.add_argument('--trace-program-version',choices=('3.13','3.14'));a=p.parse_args()
 cpu=getattr(sys,"_acceptance_cpu_e2e",None)
 if a.start_check:
  from acceptance_start_check import begin
  begin(6,a)
 import torch
 from PIL import Image
 from student_pilot.mdg_runtime import load_runtime
 from student_pilot.p3_provenance import file_pin
 from student_pilot.carrier_c1_canary import prompt_batch,answer_of
 from student_pilot.carrier_c1_routing import tool_mode
 from student_pilot.carrier_c1_run import move
 from student_pilot.carrier_c1_batch_benchmark import select_rows
 from student_pilot.sam3_tower import attach_sam3_tower
 from student_pilot.ground_sources import TowerSAM3
 from student_pilot.ground_profiles import load_geometry,build_profile
 from student_pilot.scene_state import FrameMap,SceneState
 from student_pilot import carrier_c1_decode as D
 from student_pilot.live_trace313 import LiveSession,check_record
 from rk.sam3mask import tower as codec
 if a.start_check:
  from acceptance_start_check import native_check
  native_check(a)
  return
 if not cpu and torch.cuda.device_count()!=1:raise ValueError('Expose one assigned card')
 capacity=48*2**30 if cpu else torch.cuda.get_device_properties(0).total_memory
 if not 44*2**30<=capacity<=50*2**30:raise ValueError('Requires one 48 GB card')
 out=Path(a.out);out.mkdir(parents=True,exist_ok=False);device=torch.device('cpu' if cpu else 'cuda:0');torch.set_num_threads(1)
 model,processor,_=load_runtime(dict(trace_program_version=a.trace_program_version,c1_config=file_pin(a.config),base_artifact=file_pin(a.artifact),bundle=file_pin(a.bundle)),device)
 if a.call_mode=='scripted':
  if not a.inputs:raise ValueError('Scripted mode requires --inputs')
  from acceptance_model_contract import check_runtime_binding
  live=json.loads(Path(a.inputs).read_text())
  if live['call_mode']!=a.call_mode or live['bundle']!=file_pin(a.bundle):raise ValueError('Scripted inputs differ from loaded bundle')
  check_runtime_binding(live,processor.tokenizer)
 model.eval();cfg=json.loads(Path(a.config).read_text())
 tower=attach_sam3_tower(model,dict(checkpoint_path=a.sam_checkpoint,source_root=a.sam_source,
     receipt_path=str(R/'inputs/sam3_tower/SAM3_RECEIPT.json'),device=str(device)),enabled=True)
 metadata=json.loads(Path(a.geometry).read_text());rows=select_rows(a.rows);records=[];start=time.monotonic()
 if cpu: rows=rows[:4]
 else: torch.cuda.reset_peak_memory_stats()
 for first in range(0,len(rows),4):
  if time.monotonic()-start>a.max_seconds:raise TimeoutError('Native profile read budget exhausted')
  batches=[];backends=[]
  for row in rows[first:first+4]:
   meta=metadata[row['qid']];pin=meta[a.depth_source];frames=[]
   if sha(pin['path'])!=pin['sha256']:raise ValueError('Geometry hash differs')
   for frame in row['student_input']['frames']:
    if sha(frame['path'])!=frame['sha256']:raise ValueError('RGB hash differs')
    with Image.open(frame['path']) as im:frames.append(im.convert('RGB'))
   mapping=FrameMap(tuple(row['student_input']['frame_indices']),rgb_sha256=tuple(hashlib.sha256(im.tobytes()).hexdigest() for im in frames))
   geo=load_geometry(pin['path'],mapping,a.depth_source)
   source=TowerSAM3(tower,frames,mapping,'sam3_cache_contract:'+sha(R/'inputs/sam3_tower/SAM3_RECEIPT.json'),codec())
   backend=build_profile('native_selector',SceneState(meta['video_sha256'],mapping,geo.identity),geo,source,
       depth_source=a.depth_source,audit_dir=out/'audits'/row['qid'])
   batch=move(prompt_batch(processor,tool_mode(row,cfg.get('tool_mode_flag')),cfg),device)
   batch.update(video_sha256=meta['video_sha256'],frame_indices=list(mapping.source_indices),
       hrp_frame_indices=list(mapping.source_indices),frame_rgb_sha256=list(mapping.rgb_sha256),ground_frames=dict(enumerate(frames,1)))
   batches.append(batch);backends.append(backend)
  refs=[r.get('reference_trace') for r in rows[first:first+4]] if a.call_mode=='scripted' else None
  if first==0 and a.check_reread:
   from student_pilot.precision_parity import record_parity,tensor_sha,attention
   def hashes():return [{k:tensor_sha(v) for k,v in batch.items() if isinstance(v,torch.Tensor)} for batch in batches]
   input_hashes=hashes()
  outputs=D.generate(model,processor,batches,max_new_tokens=16384,mask_source='svp_sam3',ground_backend=backends,verify=None,reread=None,trace_session=[LiveSession(b,program_version=model_version(model,a.trace_program_version)) for b in backends],reference_trace=refs)
  if first==0 and a.check_reread:
   repeat_input_hashes=hashes()
   repeat_started=time.monotonic()
   repeat=D.generate(model,processor,batches,max_new_tokens=16384,mask_source='svp_sam3',ground_backend=backends,verify=None,reread=None,trace_session=[LiveSession(b,program_version=model_version(model,a.trace_program_version)) for b in backends],reference_trace=refs)
   repeat_seconds=time.monotonic()-repeat_started
   actual_input_hashes=hashes()
   from student_pilot.reread import Config as ReReadConfig
   reread_batches=[]
   for batch in batches:
    config=ReReadConfig(frames=batch['ground_frames'],frame_indices=tuple(batch['frame_indices']),
        clip_key=batch['video_sha256'],layers=(1,2,3) if cpu else (9,17,25,27),size_hw=(768,1024),preload_ids=(1,7,20,32))
    reread_batches.append(dict(batch,own_vit_reread=config))
   enabled=D.generate(model,processor,reread_batches,max_new_tokens=16384,mask_source='svp_sam3',ground_backend=backends,verify=None,reread=None,trace_session=[LiveSession(b,program_version=model_version(model,a.trace_program_version)) for b in backends],reference_trace=refs)
   from student_pilot.decode_parity import save_comparison
   strict_report=save_comparison(out/'reread_comparison',outputs,enabled,ids=[r['qid'] for r in rows[:4]],
       full_records=True,labels=['B4 preload disabled','B4 preload enabled'])
   strict_report['diagnostic_only']=True
   (out/'reread_comparison/COMPARISON.json').write_text(json.dumps(strict_report,indent=2)+'\n')
   parity=record_parity(outputs,repeat,enabled,half=next(model.parameters()).dtype in (torch.bfloat16,torch.float16))
   after_hashes=hashes()
   parity['inputs_equal']=input_hashes==repeat_input_hashes==actual_input_hashes==after_hashes
   parity['ok']=parity['ok'] and parity['inputs_equal']
   provenance=dict(gpu_name='CPU tiny Qwen' if cpu else torch.cuda.get_device_name(0),parameter_dtype=str(next(model.parameters()).dtype),
       reference='same loaded model, same card, same precision; preload disabled twice',
       batch_shapes=[4,4,4],input_hashes=input_hashes,tokenizer_padding_side=processor.tokenizer.padding_side,
       decode_padding='unpadded per-row prefills; left-padded full-attention KV; unpadded recurrent state',
       repeat_input_hashes=repeat_input_hashes,actual_input_hashes=actual_input_hashes,after_input_hashes=after_hashes,
       attention_implementation=attention(model),reference_repeat_seconds=repeat_seconds,
       comparison='exact decisions and structure; numeric fields use measured reference floor')
   (out/'reread_comparison/reference_repeat.json').write_text(json.dumps(repeat)+'\n')
   parity.update(numerical_provenance=provenance,slots=[1,7,20,32],size_hw=[768,1024],
       scope='Full loaded student; own-ViT preload plus native-selector B4 decode')
   (out/'REREAD_DECODE_PARITY.json').write_text(json.dumps(parity,indent=2)+'\n')
   print(json.dumps(dict(reread_decode_parity={k:v for k,v in parity.items() if k!='numeric_fields'})),flush=True)
   if not parity['ok']:raise AssertionError('Own-ViT reread changes B4 decode records; inspect REREAD_DECODE_PARITY.json')
  for row,record in zip(rows[first:first+4],outputs):
   replay=check_record(record,row.get("reference_trace") if a.call_mode=="scripted" else None)
   records.append(dict(qid=row['qid'],type=row['question_type'],answer=answer_of(record['text']),record=record,replay=replay))
   if record['finish']!='eos' or record['errors'] or not any(c['kind']=='ground' for c in record['calls']) or not replay['byte_equal']:
    (out/'PARTIAL.json').write_text(json.dumps(records)+'\n');raise AssertionError('Incomplete routed read: '+row['qid'])
 (out/'ROUTED_32.json').write_text(json.dumps(records)+'\n')
 peak=0 if cpu else torch.cuda.max_memory_allocated();free=capacity if cpu else torch.cuda.mem_get_info()[0]
 if capacity-peak<4*2**30 or free<4*2**30:raise AssertionError('Less than 4 GiB GPU headroom')
 result=dict(status='PASS',call_mode=a.call_mode,response_parse_and_replay=True,all_eos=True,zero_errors=True,profile='native_selector',depth_source=a.depth_source,rows=len(records),batch=4,
     seconds=time.monotonic()-start,peak_cuda_bytes=peak,geometry_sha256=sha(a.geometry),rows_sha256=sha(a.rows),
     profile_source_sha256=sha(R/'work/tree/student_pilot/ground_profiles.py'),scope='Live backend responses and free final answers; learned routing unmeasured in scripted mode.')
 (out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
