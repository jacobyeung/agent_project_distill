"""Eight-frame encoder smoke; one encoder at a time, no dense-map files."""
import argparse
import json
import math
import os
import platform
from pathlib import Path
import time
import torch
from PIL import Image
from own_feats import load,pool
from own_feats.core import readout_maps
from probe_common import ROOT,ARMS,gate,RULES_PATH,rules
from provenance import receipt,write_json
from extract import raster_masks
from spatial_flip import validate_correspondence


def run(a):
    if platform.node().split('.')[0]!='trinity-1-18' or os.environ.get('CUDA_VISIBLE_DEVICES')!='7' or a.device!='cuda:0':
        raise ValueError('Smoke requires trinity-1-18 physical GPU 7 as the sole visible card')
    rules();rows=gate.read_manifest(a.manifest)[:8]
    if len(rows)!=8:raise ValueError('Eight training frames required')
    frames=[];masks=[];raster_cache={}
    for r in rows:
        gate.check_row(r)
        with Image.open(r['rgb_path']) as im:frames.append(im.convert('RGB'))
        if r['scene'] not in raster_cache:raster_cache[r['scene']]=raster_masks(r)
        choices=[]
        for item in r['instances']:
            if item['instance_id'] not in raster_cache[r['scene']]:continue
            m=torch.from_numpy(raster_cache[r['scene']][item['instance_id']][r['slot']].copy())
            area=float(m.float().mean());overlap=float((m&m.flip(-1)).sum()/m.sum().clamp_min(1))
            if .001<=area<=.25 and overlap<.1:choices.append((area,item['instance_id'],m))
        if not choices:raise ValueError('No asymmetric real instance on smoke frame; spatial gate remains unverified')
        masks.append(min(choices,key=lambda x:(x[0],x[1]))[2])
    kind,arm_size=ARMS[a.arm]
    if kind=='paired':raise ValueError('A8 reuses its two component smokes')
    cfg=json.loads(Path(a.weights).read_text())[kind];enc=load(kind,cfg,a.device);result=[]
    for size in (arm_size,):
        requested=size
        # Eight frames are serialized for non-temporal encoders to bound memory.
        torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();start=time.monotonic()
        batches=[frames] if kind=='g3t' else [[f] for f in frames]
        shapes=None;original=[];flipped=[];contexts=[]
        for batch in batches:
            maps=enc.encode(batch,size);shapes=[list(m.shape) for m in maps]
            contexts.append(enc.last_forward_context)
            original.append(maps)
            from PIL import ImageOps
            flipped.append(enc.encode([ImageOps.mirror(f) for f in batch],size))
            contexts.append(enc.last_forward_context)
        original=[torch.cat([m[k] for m in original]) for k in range(4)]
        flipped=[torch.cat([m[k] for m in flipped]) for k in range(4)]
        spatial=validate_correspondence(original,flipped,torch.stack(masks))
        autocast=all(c['bf16_autocast'] for c in contexts)
        torch.cuda.synchronize();seconds=time.monotonic()-start
        result.append(dict(requested_hw=requested,actual_hw=size,frames=8,encoder_calls=2*len(batches),
                           seconds=seconds,frames_per_second=16/seconds,peak_bytes=torch.cuda.max_memory_allocated(),tap_shapes=shapes,readouts=['four','final','unstandardized'],spatial_correspondence=spatial,bf16_autocast=autocast))
    write_json(a.out,dict(arm=a.arm,measurements=result,encoder=enc.metadata,host=platform.node().split('.')[0],physical_gpu=7,
                         provenance=receipt([a.weights,a.manifest,RULES_PATH],[Path(__file__)],vars(a))))
    if a.arm=='A7' and not autocast:raise ValueError('SAM 3 forward did not run under bf16 autocast on the assigned GPU')
    if spatial['status']!='PASS':raise ValueError('Real-frame spatial correspondence gate failed; extraction is blocked')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--arm',choices=ARMS,required=True);p.add_argument('--weights',required=True)
    p.add_argument('--manifest',default=str(ROOT/'out/b2_manifest.jsonl'));p.add_argument('--out',required=True)
    p.add_argument('--device',default='cuda:0');run(p.parse_args())
