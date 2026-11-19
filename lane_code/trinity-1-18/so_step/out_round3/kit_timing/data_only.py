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
    parser.add_argument('--arm',choices=('off','prefetch','cache','all'),default='off')
    parser.add_argument('--baseline', help='OFF output JSON; required for every ON arm')
    parser.add_argument('--steps', type=int, default=10)
    parser.add_argument('--full-plan', action='store_true', help='Audit every supplied epoch plan; no 100-step cap')
    parser.add_argument('--gpu-copy',action='store_true')
    parser.add_argument('--pin',action='store_true')
    parser.add_argument('--consumer-ms',type=float,default=0.,help='Optional simulated compute delay; NEVER a measured GPU speedup')
    args=parser.parse_args()
    if args.arm != 'off' and not args.baseline:
        parser.error('Every ON arm requires --baseline OFF.json')
    if not args.full_plan and not 1 <= args.steps <= 100:
        parser.error('--steps must be 1..100')
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from row_hash import encoded_hash, compare_rows
    os.environ.update(C1_CPU_PREFETCH='1' if args.arm in ('prefetch','all') else '0',
                      C1_DECODED_CACHE_MIB='512' if args.arm in ('cache','all') else '0',C1_BATCH_METRICS='0')
    sys.path.insert(0,str(Path(args.tree).resolve()))
    import torch
    import numpy as np
    from student_pilot import carrier_c1_run as run
    cfg=run.load(args.config)
    processor=run.processor_for_receipt(run.load(args.manifest),run.load(args.receipt))
    descriptor=SimpleNamespace(recipe=run.recipe_for(cfg),training_mode=cfg.get('training_mode','final'),
                               frame_count=cfg.get('frame_count',32),geometry_online=cfg.get('geometry_online'),
                               r1_training=cfg.get('r1_training'))
    if cfg.get('geometry_online') or cfg.get('mdg') or cfg.get('geometry_connector') == 'gf1':
        raise ValueError('This data-only descriptor covers the four-stream run A path, not geometry/MDG checks')
    frozen=run.load(args.plan)
    if args.full_plan:
        args.steps = len(frozen['plans'])
        if not args.steps:
            raise ValueError('Full plan is empty')
    if not 0 <= args.rank < frozen['world_size'] or len(frozen['plans']) < args.steps:
        raise ValueError('Need a valid rank and at least the requested step plans')
    rows=run.Rows(run.load(args.receipt),processor)
    result=[]
    try:
        for step,plan in enumerate(frozen['plans'][:args.steps],1):
            before_rng=(random.getstate(),np.random.get_state(),torch.get_rng_state().clone())
            tick=time.perf_counter()
            waiting=copy_seconds=hash_seconds=0.
            hashes, draws=[], []
            from student_pilot.c1_cpu_prefetch import tensor_bytes, MAX_GROUP_TENSOR_BYTES
            if 'stream_rows_per_step' in descriptor.recipe:
                from student_pilot.e2e_recipe import plan_groups
                lengths = [len(group) for group in plan_groups(descriptor.recipe, plan)]
            else:
                factor = run.nominal_slices(descriptor.recipe, plan)
                lengths = [len(plan[i:i+factor]) for i in range(0, len(plan), factor)]
            group_sizes, held, slot, group = [], 0, 0, 0
            iterator=run.fetch_plan(rows,descriptor,plan,args.rank,distributed=False)
            for stream, indices in plan:
                before=time.perf_counter()
                batch,targets,audit=next(iterator)
                waiting+=time.perf_counter()-before
                draws.append([stream, int(indices[args.rank]), int(audit['index'])])
                held += tensor_bytes((batch, targets, audit))
                slot += 1
                if slot == lengths[group]:
                    group_sizes.append(held)
                    held, slot, group = 0, 0, group + 1
                hash_start=time.perf_counter()
                hashes.append(encoded_hash((batch,targets)))
                hash_seconds+=time.perf_counter()-hash_start
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
                               max_group_tensor_bytes=max(group_sizes, default=0), group_tensor_bytes=group_sizes,
                               encoded_row_sha256=hashes, row_draws=draws, hash_seconds=hash_seconds,
                               copy_seconds=copy_seconds,simulated_consumer_ms=args.consumer_ms,
                               global_rng_unchanged=rng_equal))
    finally:
        rows.close()
    Path(args.out).write_text(json.dumps(result,indent=2)+'\n')
    peak = max(r['max_group_tensor_bytes'] for r in result)
    Path(args.out+'.manifest.json').write_text(json.dumps(dict(arm=args.arm, full_plan=args.full_plan,
        plans_checked=args.steps, plans_available=len(frozen['plans']), rank=args.rank, world_size=frozen['world_size'],
        peak_group_tensor_bytes=peak, group_budget_bytes=MAX_GROUP_TENSOR_BYTES,
        intraop=torch.get_num_threads(), interop=torch.get_num_interop_threads(),
        environment={k:v for k,v in os.environ.items() if k.startswith(('OMP_', 'MKL_', 'OPENBLAS_', 'TOKENIZERS_'))}),indent=2)+'\n')
    if args.baseline:
        compare_rows(json.loads(Path(args.baseline).read_text()), result)
    if peak > MAX_GROUP_TENSOR_BYTES:
        raise ValueError('Full group tensor budget exceeded; keep prefetch OFF')
    if not all(r['global_rng_unchanged'] for r in result):
        raise ValueError('Actual row/processor path changed a global RNG; do not enable threaded prefetch')
    print(json.dumps(dict(arm=args.arm,steps=args.steps,encoded_rows_equal_to_off=True if args.baseline else None,median_wall_seconds=statistics.median(x['wall_seconds'] for x in result),
        median_data_seconds=statistics.median(x['data_seconds'] for x in result),loss_parity='not measured: no model',
        scope='actual encoding/copies; no LM, heads, FSDP, optimizer or inter-rank admission'),indent=2))


if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'kit_profile'))
    from privacy import filter_streams
    filter_streams()
    main()
