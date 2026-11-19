"""Use the real trainer's admission/load/wrap/restore, then a disposable measurement loop."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tree', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--resume', help='Same explicit resume-pin JSON for all timing arms; never latest')
    parser.add_argument('--mode', choices=('profile', 'timing'), default='profile')
    parser.add_argument('--plan', help='Plan JSON emitted by the baseline arm (mandatory for timing ON arms)')
    parser.add_argument('--arm', choices=('off', 'prefetch', 'cache', 'metrics', 'all'), default='off')
    parser.add_argument('--profile-microsteps', type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.profile_microsteps <= 8:
        parser.error('Profile at most eight microsteps to bound trace memory')
    sys.path.insert(0, str(Path(args.tree).resolve()))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import torch
    import torch.distributed as dist
    torch.set_num_threads(8)
    from student_pilot import carrier_c1_run as run
    from instrument import Phases, hooks, instrument_step, profiler_table
    from disposable import measurement_train
    switches = {'C1_CPU_PREFETCH': '0', 'C1_DECODED_CACHE_MIB': '0', 'C1_BATCH_METRICS': '0'}
    if args.arm in ('prefetch', 'all'):
        switches['C1_CPU_PREFETCH'] = '1'
    if args.arm in ('cache', 'all'):
        switches['C1_DECODED_CACHE_MIB'] = '512'
    if args.arm in ('metrics', 'all'):
        switches['C1_BATCH_METRICS'] = '1'
    os.environ.update(switches)
    if args.mode == 'timing' and args.arm != 'off' and not args.plan:
        parser.error('An ON timing arm requires the baseline --plan')
    output = Path(args.out).resolve()
    output.mkdir(parents=True, exist_ok=False)
    resume_pin = run.load(args.resume) if args.resume else None
    # torchrun processes share --out: callers pass a rank suffix via the wrapper below.

    def measured_loop(model, wrapped, optimizer, rows, counts, trainer_output, cfg, bound, device,
                      rank=0, start_step=0, *unused, **kwargs):
        recipe = run.recipe_for(cfg)
        nsteps = 10 if args.mode == 'timing' else 2
        offset = cfg.get('row_start_step', 0)
        if args.plan:
            frozen = json.loads(Path(args.plan).read_text())
            if frozen['start_step'] != start_step or frozen['world_size'] != dist.get_world_size():
                raise ValueError('Timing plan checkpoint/world differs')
            plans = frozen['plans'][:nsteps]
        else:
            plans = list(run.data.mixed_indices(counts, offset + start_step + nsteps,
                start_step=offset + start_step, training_mode=cfg.get('training_mode', 'mixed'),
                mix=recipe['mix'], world=recipe['world_size'], r2_sampling=cfg.get('r2_sampling'),
                require_r2='r2_identity' in cfg))
        if len(plans) != nsteps:
            raise ValueError('Need exactly the requested number of fixed step plans')
        (output/'plan.json').write_text(json.dumps(dict(start_step=start_step, world_size=dist.get_world_size(), plans=plans))+'\n')
        names = [(name, p.numel(), str(p.dtype)) for name,p in run.full_ft.named_trainable(wrapped)]
        manifest = dict(arm=args.arm, switches=switches, config_sha256=run.identity(cfg), binding=bound,
                        start_step=start_step, resume=resume_pin, torch=torch.__version__, trainables=names,
                        profiler_ran=False, disposable=True)
        manifest['device_memory'] = dict(total_bytes=torch.cuda.get_device_properties(device).total_memory,
                                         free_bytes_at_loop_entry=torch.cuda.mem_get_info(device)[0])
        manifest['delta_bindings'] = []
        for name, module in model.named_modules():
            if type(module).__name__ in ('Qwen3_5GatedDeltaNet','Qwen3NextGatedDeltaNet'):
                manifest['delta_bindings'].append(dict(name=name,
                    dimensions={k:getattr(module,k,None) for k in ('hidden_size','num_v_heads','num_k_heads',
                                'head_k_dim','head_v_dim','conv_dim','conv_kernel_size')},
                    functions={k:None if (v:=getattr(module,k,None)) is None else
                        getattr(v,'__module__','')+'.'+getattr(v,'__name__',type(v).__name__)
                        for k in ('causal_conv1d_fn','causal_conv1d_update','chunk_gated_delta_rule','recurrent_gated_delta_rule')},
                    norm=type(module.norm).__module__+'.'+type(module.norm).__name__))
        (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
        gates = None
        if recipe.get('scheduled_sampling'):
            gates = run.routing.Gates(recipe['scheduled_sampling'], getattr(model, 'depth_stage1', False))
            state = [run.replay_gates(cfg['output'], start_step, gates).ema if rank == 0 else None]
            dist.broadcast_object_list(state, src=0)
            gates.ema = dict(state[0])
        first_losses = []
        hook = model.register_forward_hook(lambda m,a,o: first_losses.append(o['loss'].detach().clone())
                                           if isinstance(o, dict) and 'loss' in o else None)
        records = []
        for index, plan in enumerate(plans):
            step = start_step + index + 1
            dist.barrier()
            torch.cuda.synchronize(device)
            tick = time.perf_counter()
            if args.mode == 'profile' and index == 1:
                phases = Phases(device)
                # CPU/CUDA event scopes span the full step. Detailed Kineto tracing
                # spans a bounded prefix only; it still includes actual recomputation.
                with hooks(run, wrapped, phases):
                    operation = instrument_step(run, phases)
                    prof = torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,
                        torch.profiler.ProfilerActivity.CUDA], record_shapes=False,
                        profile_memory=False, with_stack=False)
                    original_fetch = run.fetch_plan
                    counter = [0]
                    def fetch(*a, **kw):
                        for value in original_fetch(*a, **kw):
                            if counter[0] == args.profile_microsteps:
                                prof.stop()
                            counter[0] += 1
                            yield value
                    # instrument_step has a private globals dict: replace its fetch too.
                    operation.__globals__['fetch_plan'] = fetch
                    prof.start()
                    try:
                        info, _ = operation(wrapped, optimizer, rows, plan, rank, device, step, True, gates)
                    finally:
                        if counter[0] <= args.profile_microsteps:
                            prof.stop()
                    phases.table(output/'phase_table.json')
                    profiler_table(prof, output/'profiler_table.json')
                    prof.export_chrome_trace(str(output/'trace.json'))
                    manifest['profiler_ran'] = True
                    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
            else:
                info, _ = run.optimize_step(wrapped, optimizer, rows, plan, rank, device, step, True, gates)
            elapsed = time.perf_counter() - tick
            record = {k: info[k] for k in ('step','wall_seconds','data_seconds','components',
                                         'stream_means','peak_allocated_bytes','peak_reserved_bytes')}
            record.update(end_to_end_seconds=elapsed, rank=rank, arm=args.arm,
                          plan_sha256=hashlib.sha256(json.dumps(plan,sort_keys=True).encode()).hexdigest())
            if index == 0:
                record['first_step_micro_losses'] = torch.stack(first_losses).double().cpu().tolist()
                hook.remove()
            if gates is not None:
                gates.update(info['head_metrics'])
            records.append(record)
            (output/'steps.json').write_text(json.dumps(records, indent=2)+'\n')
            print('SO_STEP ' + json.dumps(record), flush=True)
        return records

    run.run_steps = measured_loop
    cfg = run.load(args.config)
    # Each arm uses its own disposable smoke directory. The configuration remains
    # unchanged for native authorization, checkpoint identity and gate replay.
    train = measurement_train(run, output.parent / 'trainer')
    train(cfg, smoke_steps=10 if args.mode == 'timing' else 2,
          resume_pin=resume_pin)


if __name__ == '__main__':
    # Every rank owns a fresh output directory. The root is created only by rank 0's
    # wrapper shell before torchrun; Python's mkdir(parents=True) is race-safe.
    if '--out' in sys.argv:
        i = sys.argv.index('--out') + 1
        sys.argv[i] = str(Path(sys.argv[i]) / ('rank' + os.environ.get('RANK', '0')))
    main()
