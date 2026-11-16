"""Measure the legacy byte fixture at both allowed CPU thread counts."""
import hashlib
import json
import os
from pathlib import Path
import sys

L = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(L / 'work/tree_r1'))
import torch
from student_pilot import g3t_online as gx
from tests.test_gx_carrier import settings, fusion_settings, architecture

rows = []
for threads in (1, 8):
    torch.set_num_threads(threads)
    for fusion in (False, True):
        block = settings()
        if fusion:
            block['patch_fusion'] = fusion_settings(50)
        torch.manual_seed(1109)
        encoder = gx.G3TEncoder(block, architecture(), image_size=28)
        result = encoder(torch.rand(4, 3, 28, 28))
        rows.append(dict(threads=threads, fusion=fusion,
                         hashes=[hashlib.sha256(x.numpy().tobytes()).hexdigest() for x in result]))
files = ['student_pilot/g3t_online.py', 'tests/test_gx_carrier.py']
source = {name: {label: hashlib.sha256((root / name).read_bytes()).hexdigest()
                 for label, root in [('build5', L / 'work/contracts_r6/tree_copy'),
                                     ('build6', L / 'work/tree_r1')]}
          for name in files}
out = L / 'work/build6/proofs/tensor_threads'
out.mkdir(parents=True, exist_ok=True)
(out / 'RESULTS.json').write_text(json.dumps(dict(measurements=rows, sources=source), indent=2) + '\n')
print(json.dumps(rows, indent=2))
