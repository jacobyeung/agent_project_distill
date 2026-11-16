"""Run SAM at the frozen dense prompt setting and check RGB/phrase/noise parity."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import gate
SAM=gate.ROOT/'sam3_tower/work/c1mix_e2e'
sys.path.insert(0,str(SAM))
from scripts.sam3_validate import compare_noise_aware,prediction
from student_pilot.sam3_tower import Sam3Tower,FrameDetections,_map_tensors,normalize_phrase
sys.path.insert(0,str(gate.ROOT/'o3_cache/work/kit/vendor_sam/vendor'))
from sam_backend import make_postprocess,detect_prompt
RULE=json.loads((gate.ROOT/'sam3_tower/out/BATCH_MEASUREMENTS_FINAL.json').read_text())['noise_aware_rule']
def detect(tower,images,phrase):
 import torch,torch.nn.functional as F
 with torch.inference_mode():return [d for d,n in detect_prompt(tower,tower.encode(images),phrase,make_postprocess(F,torch,FrameDetections,.05,30),_map_tensors)]
def check(entry,frame,phrase,fresh):
 if gate.sha(frame)!=entry['frame_sha256']:raise ValueError('Frame SHA differs')
 if phrase!=entry['phrase']:raise ValueError('Phrase differs')
 return compare_noise_aware(entry['prediction'],fresh,gate=.05,joint_gate=True,**RULE)
def run(manifest,out):
 from PIL import Image
 m=json.loads(Path(manifest).read_text())
 if len({x['canonical'] for x in m['entries']})!=10:raise ValueError('GPU parity requires exactly ten fixed scenes')
 tower=Sam3Tower(m['settings']);results=[];cache_entries={}
 for entry in m['entries']:
  if not gate.eligible(*entry['canonical'].split('/')):raise ValueError('Ineligible parity capture')
  frame=Path(entry['frame']['path'])
  if gate.sha(frame)!=entry['frame']['sha256']:raise ValueError('Frame pin differs')
  cache=Path(entry['cache']['path'])
  if str(cache) not in cache_entries:
   if gate.sha(cache)!=entry['cache']['sha256']:raise ValueError('Cache pin differs')
   wanted={r.get('entry_index',0) for r in m['entries'] if r['cache']['path']==str(cache)}
   with cache.open() as f:cache_entries[str(cache)]={i:json.loads(line) for i,line in enumerate(f) if i in wanted}
  cached=cache_entries[str(cache)][entry.get('entry_index',0)]
  with Image.open(frame) as im:fresh=detect(tower,[im.convert('RGB')],entry['phrase'])[0]
  results.append(dict(canonical=entry['canonical'],**check(cached,frame,entry['phrase'],fresh)))
 result=dict(pass_all=all(x['ok'] for x in results),results=results,noise_rule=RULE)
 Path(out).write_text(json.dumps(result,indent=2)+'\n');return result['pass_all']
def prepare(manifest,cache,out):
 import random,hashlib
 m=json.loads(Path(manifest).read_text());captures={c['canonical']:c for c in m['captures'] if any(r['operands'] for r in c['rows'])}
 chosen=random.Random(17).sample(sorted(captures),10);entries=[]
 for canon in chosen:
  c=captures[canon];raw=Path(cache)/hashlib.sha256(json.dumps(canon,sort_keys=True,allow_nan=False).encode()).hexdigest()[:16]/'parity_raw.jsonl'
  pin=dict(path=str(raw.resolve()),sha256=gate.sha(raw));bysha={f['sha256']:f for f in c['dense_frames']}
  with raw.open() as f:
   for i,line in enumerate(f):
    if i>=32:break
    rec=json.loads(line);frame=bysha[rec['frame_sha256']]
    entries.append(dict(canonical=canon,frame={k:frame[k] for k in ('path','sha256')},phrase=rec['phrase'],cache=pin,entry_index=i))
 s=m['gpu'];settings=dict(checkpoint_path=s['sam_checkpoint']['path'],receipt_path=s['sam_receipt']['path'],source_root=s['sam_source'],device='cuda:0',precision='bf16',image_batch_size=1)
 Path(out).write_text(json.dumps(dict(entries=entries,settings=settings,seed=17),indent=2)+'\n')
def main():
 p=argparse.ArgumentParser();p.add_argument('--manifest');p.add_argument('--out');p.add_argument('--cache');p.add_argument('--prepare',action='store_true');p.add_argument('--print-command',action='store_true');a=p.parse_args()
 if a.print_command:
  print('CUDA_VISIBLE_DEVICES=CARD /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B '+str(Path(__file__).resolve())+' --manifest PARITY_10.json --out PARITY_10_RESULT.json');return
 if not a.manifest or not a.out:p.error('--manifest and --out are required')
 if a.prepare:
  if not a.cache:p.error('--prepare requires --cache')
  prepare(a.manifest,a.cache,a.out);return
 raise SystemExit(not run(a.manifest,a.out))
if __name__=='__main__':main()
