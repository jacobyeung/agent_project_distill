"""Scale-head scale for each dev-S1 clip of job 170056 from its raw G3T tower output (CPU).
Usage: python -I -B scale_devs1.py HEAD_DIR CLIP_TO_RAW.json R1_GEOMETRY_DIR OUT.json"""
import json, sys
from pathlib import Path
import numpy as np
import torch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'heads/scale'))
from scale_head import load_head, prepare_inputs, file_sha256

head_dir, clipmap, geo_dir, out = sys.argv[1:5]
head = load_head(head_dir)
meta = json.loads((Path(head_dir) / 'scale_head.json').read_text())
m = json.loads(Path(clipmap).read_text())
res, ratio = {}, []
with torch.no_grad():
    for clip, raw in sorted(m.items()):
        s = float(torch.exp(head(**prepare_inputs(raw)))[0])
        old = float(np.load(Path(geo_dir) / (clip + '.npz'))['scale'])
        res[clip] = s
        ratio.append(s / old)
r = np.array(ratio)
Path(out).write_text(json.dumps(dict(head_weights_sha256=meta['weights_sha256'], clips=len(res),
                                     ratio_new_over_old=dict(median=float(np.median(r)), q10=float(np.quantile(r, .1)),
                                                             q90=float(np.quantile(r, .9))),
                                     scales=res), indent=1) + '\n')
print(len(res), np.median(r), np.quantile(r, [.1, .9]))
