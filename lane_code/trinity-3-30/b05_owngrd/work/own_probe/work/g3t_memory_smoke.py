"""Live G3T 32/64-frame peak memory and all-head hash parity, before/after retention."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import torch
from PIL import Image
from g3t_taps import import_vendor,TapCapture,VENDOR
from own_feats.core import pixels
from probe_common import ROOT,gate
from provenance import sha256,receipt,write_json


def hashes(value):
    if isinstance(value,torch.Tensor):
        return hashlib.sha256(value.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()
    if isinstance(value,list):return [hashes(x) for x in value]
    return {k:hashes(v) for k,v in value.items()}


def run(a):
    from safetensors.torch import load_file
    cfg=json.loads(Path(a.weights).read_text())['g3t'];path=cfg['path']
    if sha256(path)!=cfg['sha256']:raise ValueError('G3T weight hash mismatch')
    cls=import_vendor(cfg.get('source_root',VENDOR));model=cls().eval().requires_grad_(False)
    model.load_state_dict(load_file(path,device='cpu'),strict=True);model.to(a.device)
    rows=gate.read_manifest(a.manifest)[:32];frames=[]
    for r in rows:
        with Image.open(r['rgb_path']) as im:frames.append(im.convert('RGB'))
    measurements=[]
    for n in (32,64):
        images=pixels((frames*2)[:n],(392,518),(0,0,0),(1,1,1)).to(a.device)
        baseline=None
        for sparse in (False,True):
            torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();start=time.monotonic()
            with torch.inference_mode(),torch.autocast('cuda',dtype=torch.bfloat16):
                if sparse:
                    with TapCapture(model,(392,518),sparse=True) as capture:prediction=model(images)
                else:prediction=model(images)
            torch.cuda.synchronize();elapsed=time.monotonic()-start;peak=torch.cuda.max_memory_allocated()
            output_hashes=hashes(prediction)
            if sparse:
                if baseline!=output_hashes:raise ValueError('G3T head outputs changed under sparse retention')
                capture.maps=None
            else:baseline=output_hashes
            measurements.append(dict(frames=n,sparse=sparse,peak_bytes=peak,seconds=elapsed,output_hashes=output_hashes))
            del prediction
        del images
    write_json(a.out,dict(status='PASS',measurements=measurements,
                         clip='First 32 admitted training frames; repeated once for the 64-frame memory stress test',
                         provenance=receipt([a.weights,a.manifest],[Path(__file__),ROOT/'work/g3t_taps.py'],vars(a))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--weights',required=True);p.add_argument('--out',required=True)
    p.add_argument('--manifest',default=str(ROOT/'out/b2_manifest.jsonl'));p.add_argument('--device',default='cuda:0');run(p.parse_args())
