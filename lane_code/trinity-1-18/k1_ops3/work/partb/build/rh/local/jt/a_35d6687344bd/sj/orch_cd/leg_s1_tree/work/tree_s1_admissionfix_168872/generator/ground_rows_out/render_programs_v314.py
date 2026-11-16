"""Render v3.14 program items from pinned local GT clips, including camera rows.

Each JSONL input has item, gt.path/sha256, and frame_indices. Output keeps dispositions
for every input; no training reader may treat a refused row as an admitted trace.
"""
import argparse,json,hashlib
from pathlib import Path
from derivgen.ground_v312_io import GTClip,reference,load_backend
from derivgen.ground_v313 import Session,MergedInstances,GTInstances,gt_frame_components
from functools import lru_cache
from derivgen.ground_v313_tokens import tokenizer_for_rows
from derivgen.programs_v314 import render

def main():
 p=argparse.ArgumentParser()
 for name in ('items','out','rkit','backend','tokenizer'):p.add_argument('--'+name,required=True)
 p.add_argument('--dev-splits',default='/scratch/jjyeung/orch_cd/rev_ctrl/out/splits.json')
 a=p.parse_args();P,M,_=reference(a.rkit);backend=load_backend(a.backend);tok=tokenizer_for_rows(a.tokenizer)
 current=None;clip=None;dev=None
 with Path(a.items).open() as source,Path(a.out).open('x') as target:
  for line in source:
   value=json.loads(line);pin=value['gt']
   identity=(pin['path'],pin['sha256'],tuple(value['frame_indices']))
   if identity!=current:
    raw=Path(pin['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=pin['sha256']:raise ValueError('gt_pin_mismatch')
    clip=GTClip(pin['path'],value['frame_indices'],P,M);current=identity
    detections=lru_cache(None)(gt_frame_components(clip))
   try:
    if value['item']['type']=='room_size_estimation':
     from render_room_v314 import prepare
     if dev is None:dev=set(json.loads(Path(a.dev_splits).read_text())['all_scenes'])
     row,_=prepare(value['item'],clip,backend,tok,canonical=value.get('canonical',value['item'].get('canonical')),
                   pin=pin,frames=value['frame_indices'],dev=dev)
    else:
     resolver = GTInstances(clip) if value['item']['type'] in ('object_counting','relative_count') else MergedInstances(backend,clip.geo,detections)
     row=render(value['item'],Session(backend,clip.geo,clip.masks,instances=resolver,multi_instance=True),lambda s:len(tok.encode(s,add_special_tokens=False).ids))
    row['gt_input']=pin;row['frame_indices']=value['frame_indices']
   except (ValueError,KeyError) as exc:row=dict(qid=value['item']['qid'],training_admitted=False,refusal=str(exc))
   target.write(json.dumps(row)+'\n')
if __name__=='__main__':main()
