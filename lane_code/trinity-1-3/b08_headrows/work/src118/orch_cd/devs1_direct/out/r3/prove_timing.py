"""CPU proof of training/dev video metadata using the reviewed kit and HF metadata class."""
import argparse,copy,hashlib,importlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import adapter as A
import numpy as np
from transformers.video_utils import VideoMetadata
from transformers.models.qwen3_vl.processing_qwen3_vl import Qwen3VLProcessor

def prove(model):
 name='cp1' if model=='cp1m200' else 'f17';work=ROOT.parents[1]/'work/r3'
 data,media,_=A.kit_import(work/f'final_{name}/kit')
 layout_inputs=importlib.import_module('trainer.layout_reference').layout_inputs
 _,_,tasks,captures=A.payload(ROOT);cell=json.loads((ROOT/f'cells_{model}.json').read_text())[0]
 training=A.jsonl(ROOT/'TRAINING_TIMING_ROWS.jsonl')
 lineage={r['dataset']:r for r in training if r['kind']=='resolved_lineage'}
 selected=[];used={t['native'] for t in tasks}
 for d,count in [('d1',7),('d2',7),('d3',6)]:
  candidates=[c for c in captures.values() if c['native'] in used and c['native'].startswith(d+'/')]
  selected+=sorted(candidates,key=lambda c:hashlib.sha256(('devS1-r3-timing|'+c['native']).encode()).hexdigest())[:count]
 proofs=[]
 for c in selected:
  d=c['native'].split('/')[0];sample=lineage[d];row=sample['row'];inputs=layout_inputs(row,layout=cell['layout'])
  assert row['student_input']['timestamps']==[i/row['student_input']['fps'] for i in row['student_input']['frame_indices']]
  task=dict(benchmark='devrows',example_id=c['native'],native=c['native'],video_path='identity-only',source_frame_indices=c['anchor_indices'])
  receipt=A.receipt_template(task,cell,c,media);dm=receipt['audit']['metadata']
  # Exactly the fields passed by carrier_c1_data.encode / pose_samples.encode.
  # Dimensions are array-derived; small synthetic RGB arrays avoid reading production pixels.
  tm=dict(fps=inputs['fps'],frames_indices=inputs['frame_indices'],total_num_frames=inputs['total_num_frames'],height=2,width=3)
  dv,tv=VideoMetadata(**dm),VideoMetadata(**tm)
  assert set(dm)==set(tm)=={'fps','frames_indices','total_num_frames','height','width'}
  assert set(dv)==set(tv)
  assert dv.fps==tv.fps
  assert dv.timestamps==receipt['audit']['timestamps']==[i/dv.fps for i in dv.frames_indices]
  assert tv.timestamps==inputs['timestamps']==[i/tv.fps for i in tv.frames_indices]
  for metadata in (dv,tv):
   actual=Qwen3VLProcessor._calculate_timestamps(None,list(metadata.frames_indices),metadata.fps,2)
   assert actual==[(a+b)/2 for a,b in zip(metadata.timestamps[::2],metadata.timestamps[1::2])]
  expanded=layout_inputs(dict(student_input=dict(frames=c['frames'],frame_indices=c['anchor_indices'],timestamps=c['timestamps'],fps=c['fps'],total_num_frames=c['total_num_frames'])),layout=cell['layout'])
  assert expanded['timestamps']==dv.timestamps and expanded['frame_indices']==dv.frames_indices
  if cell['layout']=='duplicate':
   assert dv.timestamps[::2]==dv.timestamps[1::2]==c['timestamps']
   assert tv.timestamps[::2]==tv.timestamps[1::2]==row['student_input']['timestamps']
  # Exercise the real official VSI decode metadata path with its decoded RGB/FPS boundary injected.
  original=media.sample_video
  media.sample_video=lambda task,args:(np.zeros((32,2,3,3),dtype=np.uint8),row['student_input']['frame_indices'],row['student_input']['fps'],row['student_input']['total_num_frames'])
  try:_,audit=media.decode(dict(benchmark='vsi500',video_path='cpu-injected-decode'),cell['layout'],frames=32)
  finally:media.sample_video=original
  assert audit['metadata']==tm
  proofs.append(dict(native=c['native'],dataset=d,selection_sha256=hashlib.sha256(('devS1-r3-timing|'+c['native']).encode()).hexdigest(),
    dev_metadata=dm,training_metadata=tm,training_source={k:sample[k] for k in ('source','source_sha256','line','line_sha256')},training_qid=row['qid'],
    dev_timestamps=dv.timestamps,training_timestamps=tv.timestamps,
    dev_temporal_patch_timestamps=[(a+b)/2 for a,b in zip(dv.timestamps[::2],dv.timestamps[1::2])],
    training_temporal_patch_timestamps=[(a+b)/2 for a,b in zip(tv.timestamps[::2],tv.timestamps[1::2])],
    same_keys=True,same_fps=True,same_timestamp_formula=True,same_capture_training_layout_exact=True,official_vsi_metadata_exact=True,
    total_num_frames_lower_bound=c['total_num_frames_lower_bound']))
 A.dump(ROOT/f'TIMING_EQUIVALENCE_{model}.json',dict(model=model,layout=cell['layout'],captures=20,
  selection='Within each dataset sort SHA256(devS1-r3-timing|native): d1=7,d2=7,d3=6; eligible captures appear in the dev tasks.',
  scope='Actual HF VideoMetadata and kit layout/decode metadata; injected RGB decode boundary, no production pixels, weights, tokenizer, GPU, or inference.',proofs=proofs))
 for d in ('d1','d2','d3'):
  p=next(p for p in proofs if p['dataset']==d)
  print(json.dumps(dict(model=model,native=p['native'],training_qid=p['training_qid'],fps=p['dev_metadata']['fps'],
   dev_indices=p['dev_metadata']['frames_indices'][:4],dev_seconds=p['dev_timestamps'][:4],
   training_indices=p['training_metadata']['frames_indices'][:4],training_seconds=p['training_timestamps'][:4],keys=sorted(p['dev_metadata']))))
 print(model+': PASS: 20 captures, actual HF timestamps, training layout, official VSI metadata path')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--model',choices=['cp1m200','f17'],required=True);prove(p.parse_args().model)
