"""Simulation only: false refusals with iid Gaussian OFF/ON forward noise."""
import importlib.util
import json
import os
from pathlib import Path
import sys
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='8',
    MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',TOKENIZERS_PARALLELISM='false')
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:8])
import torch
torch.set_num_threads(8)
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'out/kit_timing'))
from replay_compare import pooled_loss_acceptance
spec=importlib.util.spec_from_file_location('delivered_round4',ROOT/'out_round5/kit_timing/replay_compare.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
rng=np.random.default_rng(20261119)
result=dict(label='SIMULATION, not production measurements',seed=20261119,trials_per_scenario=100000,
    noise='independent standard Gaussian per arm, rank and scalar; identical true losses',
    ranks=4,multiplier=2.,scenarios=[])
for n in (1,4,5,12,20):
    old_refused=new_refused=0
    for start in range(0,100000,5000):
        samples=rng.standard_normal((5000,3,4,n))
        a,b,c=samples[:,0],samples[:,1],samples[:,2]
        d=np.abs(a-b).max(axis=2)
        m=np.maximum(np.abs(c-a),np.abs(c-b)).max(axis=2)
        old_pass=(m <= 2*d).all(axis=1)
        new_pass=m.max(axis=1) <= 2*d.max(axis=1)
        old_refused+=int((~old_pass).sum());new_refused+=int((~new_pass).sum())
        if start==0:
            for i in range(32):
                assert bool(old_pass[i])==all(old.loss_acceptance(*[arm[r].tolist() for arm in samples[i]])['accepted'] for r in range(4))
                arms=[[dict(components={str(k):float(v) for k,v in enumerate(rank)},stream_means={},first_step_micro_losses=[]) for rank in arm] for arm in samples[i]]
                assert bool(new_pass[i])==pooled_loss_acceptance(*arms)['accepted']
    result['scenarios'].append(dict(scalars_per_rank=n,delivered_per_rank_false_refusal=old_refused/100000,
        pooled_false_refusal=new_refused/100000,delivered_refusals=old_refused,pooled_refusals=new_refused))
print(json.dumps(result,indent=2))
