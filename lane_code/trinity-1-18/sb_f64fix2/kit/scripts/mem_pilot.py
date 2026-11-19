"""Four-rank GPU memory and step-time pilot of the bound 64-viewpoint R1 config. Written, not yet run.

It runs the trainer's own setup and update from carrier_c1_run: `prepared`, `load_model` with the init
artifact and depth init, `wrap_model` (FSDP FULL_SHARD over FP32 master weights, BF16 compute, FP32
reduce, replicated heads), AdamW over `parameter_groups`, and `optimize_step`, whose LM layers run
non-reentrant activation checkpointing. Each optimizer step is one full accumulation cycle: the sampler's
own microstep layout for the run's first step (72 microsteps per rank at world 4, global batch 288), with
every microstep's rows replaced by the longest audited rows of its stream, longest first. Step 1
allocates the Adam state; later steps measure the steady state. After the last step every rank writes
its shard of one resume checkpoint with the trainer's `checkpoint`, and the pilot records that peak too.

Launch on one node with four 80-GB GPUs, after the orchestrator authorizes the allocation, in the
production launch environment (C1_EXPECT_FLA=1 when that launch binds the fla overlay, because the
linear-attention kernel changes activation memory):
  torchrun --standalone --nproc_per_node 4 mem_pilot.py --config BOUND_CFG.json --audit SUMMARY.json --out DIR
The audit's shard files must sit at the paths its summary records, and BOUND_CFG.json must be the audited file.
It refuses before loading weights when the world size differs from the recipe's, when any GPU has less
than 79 GiB and C1_FSDP_CPU_OFFLOAD is not 1 (48-GB cards are unsupported for the non-offloaded config),
when the audit summary is not complete coverage of this config's run, when any audited row fails check_row
or exceeds the ceiling (rows over the tripwire alone pass, for calibration), or when R1 admission refuses the
config (missing r2_sampling, preparation, code, admission or depth-init pins). Rank 0 writes
DIR/PILOT.json: per rank and step, the allocated and reserved peaks of every microstep, the memory after
the optimizer step, the Adam state bytes, the checkpoint peak, step seconds, the plan with its tokens,
and the verdict against --budget-gib.
"""
import argparse
import datetime
import json
import os
import random
import sys
import time
from pathlib import Path

TREE = Path(os.environ.get('F64_TREE', '/scratch/jjyeung/orch_n30/sb_f64/pkg/work/tree_f64'))
sys.path[:0] = [str(TREE), str(Path(__file__).resolve().parent)]
GIB = 2 ** 30
MIN_DEVICE_GIB = 79


def longest_plan(layout, longest, world):
    """One step's [(stream, rank indices)] layout -> the same streams, filled with the longest audited rows."""
    cursor, plan, tokens = {}, [], []
    for stream, indices in layout:
        if len(indices) != world:
            raise ValueError('microstep layout differs from the world size')
        rows = longest.get(stream)
        if not rows:
            raise ValueError(f'the audit has no passing rows for stream {stream}')
        start = cursor.get(stream, 0)
        chosen = [rows[(start + rank) % len(rows)] for rank in range(world)]
        cursor[stream] = start + world
        plan.append((stream, [row['index'] for row in chosen]))
        tokens.append([row['tokens'] for row in chosen])
    return plan, tokens


def check_audit(summary_path, config_path):
    """The summary must re-derive from its own shard files and cover this config's whole run, and no audited row
    may fail check_row or exceed the ceiling, since the trainer aborts on such a row and the longest-row plan would
    omit it. Rows over the tripwire alone pass: they are the rows this pilot calibrates memory on."""
    import token_audit
    summary = json.loads(Path(summary_path).read_text())
    files = summary.get('shard_files') or {}
    for path, sha in files.items():
        if token_audit.file_sha256(path) != sha:
            raise ValueError('audit shard changed since its summary: ' + path)
    again = token_audit.summarize(list(files), token_audit.file_sha256(config_path))
    if again['run_id'] != summary.get('run_id') or again['longest'] != summary.get('longest'):
        raise ValueError('audit summary differs from its shards')
    if again['errors']:
        raise ValueError('audit is not complete coverage of this run: ' + '; '.join(again['errors'][:4]))
    if sum(entry['rows'] for entry in again['streams'].values()) != again['coverage']['planned']:
        raise ValueError('audit stream counts do not cover the plan')
    refused = {}
    for stream, entry in sorted(again['streams'].items()):
        ranked = again['longest'].get(stream, [])
        omitted = min(entry['rows'], token_audit.LONGEST) - len(ranked)
        top = ranked[0]['tokens'] if ranked else 0
        if entry['failed'] or entry['over_ceiling'] or omitted or top != entry['max_tokens']:
            refused[stream] = dict(failed=entry['failed'], over_ceiling=entry['over_ceiling'], rows=entry['rows'],
                                   omitted_from_longest=omitted, longest_tokens=top, max_tokens=entry['max_tokens'])
    if refused:
        raise ValueError('audit has rows the trainer refuses (check_row failure or over the ceiling): '
                         + json.dumps(refused, sort_keys=True))
    return again


def adam_state(optimizer):
    import torch
    tensors = [v for state in optimizer.state.values() for v in state.values() if torch.is_tensor(v)]
    missing = sum(1 for group in optimizer.param_groups for p in group['params']
                  if p.grad is not None and not {'exp_avg', 'exp_avg_sq'} <= set(optimizer.state.get(p, {})))
    return dict(bytes=sum(t.numel() * t.element_size() for t in tensors), tensors=len(tensors),
                params_with_grad_without_state=missing)


def peaks(device):
    import torch
    free, total = torch.cuda.mem_get_info(device)
    return dict(max_allocated_bytes=torch.cuda.max_memory_allocated(device),
                max_reserved_bytes=torch.cuda.max_memory_reserved(device),
                device_used_bytes=total - free)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--audit', required=True, help='token_audit summarize output for this config')
    parser.add_argument('--out', required=True, help='fresh node-local directory')
    parser.add_argument('--steps', type=int, default=3)
    parser.add_argument('--budget-gib', type=float, default=76.)
    args = parser.parse_args()
    import numpy as np
    import torch
    import torch.distributed as dist
    from student_pilot import carrier_c1_data as data, carrier_c1_routing as routing, carrier_c1_run as run, full_ft
    from student_pilot.carrier_c1 import RECIPE, parameter_groups
    from student_pilot.trace_version import bind, metadata

    cfg = json.loads(Path(args.config).read_text())
    version_metadata = metadata(cfg)
    run.validate(cfg)
    if 'r1_training' in cfg:
        from launch_r1.entry import admit
        admit(cfg)
    recipe = run.recipe_for(cfg)
    world = int(os.environ.get('WORLD_SIZE', '0'))
    if world != recipe['world_size'] or not torch.cuda.is_available() or args.steps < 1:
        raise SystemExit(f'the pilot needs torchrun with {recipe["world_size"]} CUDA ranks and --steps >= 1')
    rank, local = int(os.environ['RANK']), int(os.environ['LOCAL_RANK'])
    device = torch.device(f'cuda:{local}')
    torch.cuda.set_device(local)
    properties = torch.cuda.get_device_properties(device)
    offload = os.environ.get('C1_FSDP_CPU_OFFLOAD', '0') == '1'
    if properties.total_memory < MIN_DEVICE_GIB * GIB and not offload:
        raise SystemExit(f'{properties.name} has {properties.total_memory / GIB:.1f} GiB; 48-GB cards are unsupported '
                         'for the non-offloaded config (set C1_FSDP_CPU_OFFLOAD=1 for a separate offload pilot)')
    audit = check_audit(args.audit, args.config)
    out = Path(args.out)
    dist.init_process_group('nccl', timeout=datetime.timedelta(seconds=900))
    startup = dist.new_group(backend='gloo', timeout=datetime.timedelta(seconds=3600))
    if rank == 0:
        out.mkdir(parents=True, exist_ok=False)
        (out / 'state').mkdir()
    values = [None]
    if rank == 0:
        try:
            values[0] = run.prepared(cfg, admission=True)
        except Exception as exc:
            values[0] = dict(error=f'{type(exc).__name__}: {exc}')
    dist.broadcast_object_list(values, src=0, group=startup)
    if isinstance(values[0], dict):
        raise ValueError('Rank 0 preparation check failed: ' + values[0]['error'][:400])
    receipt, manifest = values[0]
    commit = run.authenticate(cfg)
    torch.manual_seed(RECIPE['seed']); random.seed(RECIPE['seed']); np.random.seed(RECIPE['seed'])
    processor = run.processor_for_receipt(manifest, receipt)
    model, error = None, None
    if rank == 0:
        try:
            model = run.load_model(manifest, receipt, processor)
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
    run.agree(startup, error if rank == 0 else None)
    if rank != 0:
        try:
            model = run.load_model(manifest, receipt, processor, verify_assets=False)
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
    if error is None and os.environ.get('C1_EXPECT_FLA') == '1':
        error = run.fla_check(model)
    run.agree(startup, error)
    kernel = getattr(model.model.language_model.layers[0].linear_attn.chunk_gated_delta_rule, '__module__', '')
    bind(model, version_metadata, cfg)
    model.train()
    from student_pilot.r1_handover import verify_trainable_groups
    model.handover_group_tables = verify_trainable_groups(cfg, model)
    masters = sorted({str(p.dtype) for _, p in full_ft.base_parameters(model) if p.requires_grad})
    checkpointed = any(getattr(m, 'gradient_checkpointing', False) for m in model.model.language_model.modules())
    if masters != ['torch.float32'] or not checkpointed:
        raise ValueError(f'pilot needs FP32 masters and LM activation checkpointing: {masters}')
    wrapped = run.wrap_model(model, device, mixed_precision=True)
    bind(wrapped, version_metadata, cfg)
    optimizer = torch.optim.AdamW(parameter_groups(wrapped, inherited=set(getattr(model, 'inherited_head_params', ())),
                                                   pose_lr_scale=cfg.get('pose_lr_scale', 1.0),
                                                   lm_lr_scale=cfg.get('lm_lr_scale', 1.0), **run.gx_recipe(model)),
                                  weight_decay=RECIPE['weight_decay'])
    bound = dict(config_sha256=run.identity(cfg), preparation=cfg['preparation'], trainer_commit=commit, world_size=world)
    start = 0
    if 'r1_training' in cfg:
        from student_pilot.r1_training import start as r1_start
        start = r1_start(cfg)
    rows = run.Rows(receipt, processor)
    counts = {k: v['count'] for k, v in receipt['streams'].items()}
    offset = cfg.get('row_start_step', 0)
    layout = next(data.mixed_indices(counts, offset + start + 1, start_step=offset + start,
                                     training_mode=cfg.get('training_mode', 'mixed'), mix=recipe['mix'],
                                     world=world, r2_sampling=cfg.get('r2_sampling'), require_r2='r2_identity' in cfg))
    plan, tokens = longest_plan(layout, audit['longest'], world)
    if len(plan) * world != recipe['global_batch']:
        raise ValueError('one step must be the full accumulation cycle of the global batch')
    gates = (routing.Gates(recipe['scheduled_sampling'], getattr(model, 'depth_stage1', False))
             if recipe.get('scheduled_sampling') else None)
    dist.barrier()
    steps = []
    try:
        for step in range(start + 1, start + 1 + args.steps):
            torch.cuda.reset_peak_memory_stats(device)
            info, _ = run.optimize_step(wrapped, optimizer, rows, plan, rank, device, step, True, gates)
            if gates is not None:
                gates.update(info['head_metrics'])
            steps.append(dict(step=step, wall_seconds=info['wall_seconds'], data_seconds=info['data_seconds'],
                              skipped=info['skipped_microsteps'], peak_allocated_bytes=info['peak_allocated_bytes'],
                              peak_reserved_bytes=info['peak_reserved_bytes'], microbatches=info['memory']['microbatches'],
                              after_optimizer_step=info['memory']['after_optimizer_step'], adam=adam_state(optimizer),
                              **peaks(device)))
        torch.cuda.reset_peak_memory_stats(device)
        tick = time.perf_counter()
        saved = run.checkpoint(out / 'state' / f'checkpoint_{start + args.steps:06d}', wrapped, optimizer, bound,
                               start + args.steps, rotate=False)
        saving = dict(seconds=time.perf_counter() - tick, complete=saved, **peaks(device))
    finally:
        rows.close()
    local_value = dict(rank=rank, device=properties.name, total_bytes=properties.total_memory, steps=steps, checkpoint=saving)
    gathered = [None] * world
    dist.all_gather_object(gathered, local_value)
    if rank == 0:
        budget = args.budget_gib * GIB
        worst = max(max([s['peak_reserved_bytes'] for s in r['steps']] + [r['checkpoint']['max_reserved_bytes']])
                    for r in gathered)
        steady = [s['wall_seconds'] for r in gathered for s in r['steps'][1:]]
        (out / 'PILOT.json').write_text(json.dumps(dict(
            schema='f64-gpu-pilot-v1', config=dict(path=args.config, sha256=audit['identity']['config_sha256']),
            audit=dict(path=args.audit, run_id=audit['run_id']), trainer_commit=commit, torch=torch.__version__,
            cuda=torch.version.cuda, world_size=world, cpu_offload=offload, master_dtypes=masters,
            linear_attention_kernel=kernel, expect_fla=os.environ.get('C1_EXPECT_FLA') == '1',
            activation_checkpointing='non-reentrant LM layers', global_batch=recipe['global_batch'],
            microsteps_per_rank=len(plan), plan=[dict(stream=s, indices=i, tokens=t) for (s, i), t in zip(plan, tokens)],
            ranks=gathered, budget_gib=args.budget_gib, worst_reserved_gib=worst / GIB,
            steady_step_seconds=max(steady) if steady else None, fits=worst <= budget), indent=1) + '\n')
        print(json.dumps(dict(worst_reserved_gib=round(worst / GIB, 2), fits=worst <= budget)), flush=True)
    dist.barrier()
    dist.destroy_process_group()


if __name__ == '__main__':
    main()
