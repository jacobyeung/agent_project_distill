"""Timed two-step single-GPU rehearsal; requires real, qualified production pins."""
import argparse
from pathlib import Path
import time
from rl_on_n import provenance as P

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--out',required=True)
    args=ap.parse_args();P.sha(__file__)
    cfg=P.load(args.config);P.tree(cfg['tree_root'])
    from rl_on_n.serving import load_binding
    load_binding(cfg.get('grounding'))
    for key in ('export_restore','export_config','pool_config','pool'):
        if not cfg.get(key):raise ValueError('MISSING config binding: '+key)
        P.checked(cfg[key])
    import torch
    torch.set_num_threads(8)
    if torch.cuda.device_count()!=1:raise ValueError('Expose exactly one assigned GPU')
    output=Path(args.out).resolve();output.mkdir(parents=True,exist_ok=True)
    cfg.update(world_size=1,steps=2,dry_run=True,output=str(output),sequences_per_rank=32,gradient_accumulation=32)
    config=output/'DRY_RUN_CONFIG.json';P.write(config,cfg)
    from rl_on_n.train import run
    torch.cuda.synchronize();start=time.monotonic();run(config);torch.cuda.synchronize()
    progress=P.load(output/'PROGRESS_rank0.json')
    P.write(output/'TIMING.json',dict(schema='rl-on-n-timing-v1',status='PASS',steps=progress['steps'],
        total_seconds=time.monotonic()-start,scope='Measured one-GPU two-step rehearsal; no multi-GPU speedup claim',
        command='bash scripts/run_gpu_dry_run.sh --config '+args.config+' --out '+args.out))
if __name__=='__main__':main()
