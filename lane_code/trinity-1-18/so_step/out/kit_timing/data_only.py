"""Actual CPU rows/processor on one host; optional copies fit a single 48 GB GPU."""
import argparse
import json
import os
import random
from pathlib import Path
import statistics
import sys
import time
from types import SimpleNamespace


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--tree',required=True)
    parser.add_argument('--receipt',required=True,help='Actual prepared receipt JSON, with local staged frame paths')
    parser.add_argument('--manifest',required=True,help='The base-model manifest used by processor_for_receipt')
    parser.add_argument('--plan',required=True,help='off/rank0/plan.json from the production comparison')
    parser.add_argument('--config',required=True)
    parser.add_argument('--out',required=True)
    parser.add_argument('--rank',type=int,default=0)
    parser.add_argument('--arm',choices=('off','prefetch','cache'),default='off')
    parser.add_argument('--gpu-copy',action='store_true')
    parser.add_argument('--pin',action='store_true')
    parser.add_argument('--consumer-ms',type=float,default=0.,help='Optional simulated compute delay; NEVER a measured GPU speedup')
    args=parser.parse_args()
    os.environ.update(C1_CPU_PREFETCH='1' if args.arm=='prefetch' else '0',
                      C1_DECODED_CACHE_MIB='512' if args.arm=='cache' else '0',C1_BATCH_METRICS='0')
    sys.path.insert(0,str(Path(args.tree).resolve()))
    import torch
    import numpy as np
    torch.set_num_threads(8)
    from student_pilot import carrier_c1_run as run
    cfg=run.load(args.config)
    processor=run.processor_for_receipt(run.load(args.manifest),run.load(args.receipt))
    descriptor=SimpleNamespace(recipe=run.recipe_for(cfg),training_mode=cfg.get('training_mode','final'),
                               frame_count=cfg.get('frame_count',32),geometry_online=cfg.get('geometry_online'),
                               r1_training=cfg.get('r1_training'))
    if cfg.get('geometry_online') or cfg.get('mdg'):
        raise ValueError('This data-only descriptor covers the four-stream run A path, not geometry/MDG checks')
    frozen=run.load(args.plan)
    if not 0 <= args.rank < frozen['world_size'] or len(frozen['plans']) != 10:
        raise ValueError('Need a valid rank and exactly ten step plans')
    rows=run.Rows(run.load(args.receipt),processor)
    result=[]
    try:
        for step,plan in enumerate(frozen['plans'],1):
            before_rng=(random.getstate(),np.random.get_state(),torch.get_rng_state().clone())
            tick=time.perf_counter()
            waiting=copy_seconds=0.
            iterator=run.fetch_plan(rows,descriptor,plan,args.rank,distributed=False)
            for _ in plan:
                before=time.perf_counter()
                batch,targets,_=next(iterator)
                waiting+=time.perf_counter()-before
                if args.gpu_copy:
                    before=time.perf_counter()
                    if args.pin:
                        batch={k:v.pin_memory() if isinstance(v,torch.Tensor) else v for k,v in batch.items()}
                        targets=None if targets is None else {k:v.pin_memory() for k,v in targets.items()}
                    copied=[None if group is None else {k:v.to('cuda:0',non_blocking=args.pin)
                            if isinstance(v,torch.Tensor) else v for k,v in group.items()} for group in (batch,targets)]
                    torch.cuda.synchronize()
                    copy_seconds+=time.perf_counter()-before
                if args.consumer_ms:
                    time.sleep(args.consumer_ms/1000.)
            iterator.close()
            after_rng=(random.getstate(),np.random.get_state(),torch.get_rng_state())
            rng_equal=(before_rng[0]==after_rng[0] and before_rng[1][0]==after_rng[1][0]
                       and np.array_equal(before_rng[1][1],after_rng[1][1])
                       and before_rng[1][2:]==after_rng[1][2:] and torch.equal(before_rng[2],after_rng[2]))
            result.append(dict(step=step,wall_seconds=time.perf_counter()-tick,data_seconds=waiting,
                               copy_seconds=copy_seconds,simulated_consumer_ms=args.consumer_ms,
                               global_rng_unchanged=rng_equal))
    finally:
        rows.close()
    Path(args.out).write_text(json.dumps(result,indent=2)+'\n')
    if not all(r['global_rng_unchanged'] for r in result):
        raise ValueError('Actual row/processor path changed a global RNG; do not enable threaded prefetch')
    print(json.dumps(dict(arm=args.arm,steps=10,median_wall_seconds=statistics.median(x['wall_seconds'] for x in result),
        median_data_seconds=statistics.median(x['data_seconds'] for x in result),loss_parity='not measured: no model',
        scope='actual encoding/copies; no LM, heads, FSDP, optimizer or inter-rank admission'),indent=2))


if __name__ == '__main__':
    main()
