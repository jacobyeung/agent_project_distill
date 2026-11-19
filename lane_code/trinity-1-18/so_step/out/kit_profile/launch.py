"""Use the real trainer's admission/load/wrap/restore, then a disposable measurement loop."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import signal
import threading
from privacy import opaque, scrub, write_json


def save_interrupted(output, progress, phases, signum):
    progress['stage'] = 'incomplete_signal_' + str(signum)
    write_json(output/'progress.json', progress)
    if phases is not None:
        phases.table(output/'phase_partial.json', partial=True)
    print('SO_INCOMPLETE signal=' + str(signum), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tree', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--resume', help='Same explicit resume-pin JSON for all timing arms; never latest')
    parser.add_argument('--resume-config', help='Original production configuration for a source-only checkpoint bridge')
    parser.add_argument('--warmup', type=int, default=20)
    parser.add_argument('--measure', type=int, default=20)
    parser.add_argument('--mode', choices=('profile', 'timing', 'replay'), default='profile')
    parser.add_argument('--plan', help='Plan JSON emitted by the baseline arm (mandatory for timing ON arms)')
    parser.add_argument('--arm', choices=('off', 'prefetch', 'cache', 'metrics', 'all'), default='off')
    parser.add_argument('--batch-metrics', choices=('0','1'), default='0', help='Hold 03 constant across acceptance replays')
    parser.add_argument('--profile-microsteps', type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.profile_microsteps <= 8:
        parser.error('Profile at most eight microsteps to bound trace memory')
    if not 10 <= args.warmup <= 100 or not 10 <= args.measure <= 100:
        parser.error('Timing requires 10..100 warmup and 10..100 measured steps')
    sys.path.insert(0, str(Path(args.tree).resolve()))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    output = Path(args.out).resolve()
    output.mkdir(parents=True, exist_ok=False)
    progress = dict(stage='imports', completed_steps=0, completed_microsteps=0)
    write_json(output/'progress.json', progress)
    active_phases = [None]
    done = threading.Event()
    def heartbeat():
        while not done.is_set():
            write_json(output/'heartbeat.json', dict(progress, time=time.time()))
            print('SO_PROGRESS ' + json.dumps(scrub(progress)), flush=True)
            done.wait(30)
    threading.Thread(target=heartbeat, name='so-progress', daemon=True).start()
    def interrupted(signum, frame):
        done.set()
        save_interrupted(output, progress, active_phases[0], signum)
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    import torch
    import torch.distributed as dist
    from student_pilot import carrier_c1_run as run
    from instrument import Phases, hooks, instrument_step, profiler_table
    from disposable import measurement_train
    switches = {'C1_CPU_PREFETCH': '0', 'C1_DECODED_CACHE_MIB': '0', 'C1_BATCH_METRICS': args.batch_metrics, 'C1_CPU_PREFETCH_FALLBACK': '0'}
    if args.arm in ('prefetch', 'all'):
        switches['C1_CPU_PREFETCH'] = '1'
    if args.arm in ('cache', 'all'):
        switches['C1_DECODED_CACHE_MIB'] = '512'
    if args.arm in ('metrics', 'all'):
        switches['C1_BATCH_METRICS'] = '1'
    os.environ.update(switches)
    if args.mode == 'replay' and (not args.resume or not args.plan):
        parser.error('Replay requires --resume and the CPU-audited --plan')
    if args.mode == 'timing' and args.arm != 'off' and not args.plan:
        parser.error('An ON timing arm requires the baseline --plan')
    resume_pin = run.load(args.resume) if args.resume else None
    progress['stage'] = 'startup'
    # torchrun processes share --out: callers pass a rank suffix via the wrapper below.

    def measured_loop(model, wrapped, optimizer, rows, counts, trainer_output, cfg, bound, device,
                      rank=0, start_step=0, *unused, **kwargs):
        recipe = run.recipe_for(cfg)
        nsteps = args.warmup + args.measure if args.mode == 'timing' else 1
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
        names = [(opaque(name), p.numel(), str(p.dtype)) for name,p in run.full_ft.named_trainable(wrapped)]
        manifest = dict(arm=args.arm, switches=switches, config_sha256=run.identity(cfg), binding=bound,
                        start_step=start_step, resume=resume_pin, torch=torch.__version__, trainables=names,
                        profiler_ran=False, disposable=True, warmup=args.warmup if args.mode == 'timing' else 0,
                        measured_steps=args.measure if args.mode == 'timing' else 1,
                        threads=dict(intraop=torch.get_num_threads(), interop=torch.get_num_interop_threads(),
                          environment={k:v for k,v in os.environ.items() if k.startswith(('OMP_', 'MKL_', 'OPENBLAS_', 'TOKENIZERS_'))}),
                        cache_environment={k:os.environ.get(k) for k in ('CUDA_CACHE_PATH','TRITON_CACHE_DIR','TORCHINDUCTOR_CACHE_DIR')})
        manifest['device_memory'] = dict(total_bytes=torch.cuda.get_device_properties(device).total_memory,
                                         free_bytes_at_loop_entry=torch.cuda.mem_get_info(device)[0])
        manifest['lin_attn_bindings'] = []
        for name, module in model.named_modules():
            if type(module).__name__ in ('Qwen3_5GatedDeltaNet','Qwen3NextGatedDeltaNet'):
                manifest['lin_attn_bindings'].append(dict(name=opaque(name),
                    dimensions={k:getattr(module,k,None) for k in ('hidden_size','num_v_heads','num_k_heads',
                                'head_k_dim','head_v_dim','conv_dim','conv_kernel_size')},
                    functions={opaque(k):None if (v:=getattr(module,k,None)) is None else
                        opaque(getattr(v,'__module__','')+'.'+getattr(v,'__name__',type(v).__name__))
                        for k in ('causal_conv1d_fn','causal_conv1d_update','chunk_gated_delta_rule','recurrent_gated_delta_rule')},
                    norm=opaque(type(module.norm).__module__+'.'+type(module.norm).__name__)))
        write_json(output/'manifest.json', manifest)
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
            progress.update(stage='step', step=step, completed_microsteps=0)
            if args.mode == 'profile':
                phases = Phases(device)
                active_phases[0] = phases
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
                            progress['completed_microsteps'] = counter[0]
                            phases.table(output/'phase_partial.json', partial=True)
                            print('SO_MICROSTEP ' + str(counter[0]), flush=True)
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
                    fd = os.memfd_create('so-trace')
                    try:
                        prof.export_chrome_trace('/proc/self/fd/' + str(fd))
                        os.lseek(fd, 0, os.SEEK_SET)
                        with os.fdopen(os.dup(fd)) as source:
                            write_json(output/'trace.json', json.load(source))
                    finally:
                        os.close(fd)
                    manifest['profiler_ran'] = True
                    write_json(output/'manifest.json', manifest)
            else:
                phases = Phases(device, cuda_events=False)
                operation = instrument_step(run, phases)
                info, _ = operation(wrapped, optimizer, rows, plan, rank, device, step, True, gates)
            elapsed = time.perf_counter() - tick
            record = {k: info[k] for k in ('step','wall_seconds','data_seconds','components',
                                         'stream_means','peak_allocated_bytes','peak_reserved_bytes')}
            record['microstep_host'] = {label: [wall for name,wall,_,_ in phases.records if name == label]
                for label in ('forward_total', 'backward_including_recompute_and_fsdp')}
            record['measured'] = args.mode != 'timing' or index >= args.warmup
            if 'performance' in info:
                record['performance'] = info['performance']
            if 'decoded_cache' in info:
                record['decoded_cache'] = info['decoded_cache']
            record.update(end_to_end_seconds=elapsed, rank=rank, arm=args.arm,
                          plan_sha256=hashlib.sha256(json.dumps(plan,sort_keys=True).encode()).hexdigest())
            if index == 0:
                record['first_step_micro_losses'] = torch.stack(first_losses).double().cpu().tolist()
                hook.remove()
            if gates is not None:
                gates.update(info['head_metrics'])
            records.append(record)
            write_json(output/'steps.json', records)
            progress.update(completed_steps=index+1, completed_microsteps=len(plan))
            write_json(output/'progress.json', progress)
            print('SO_STEP ' + json.dumps(scrub(record)), flush=True)
        return records

    run.run_steps = measured_loop
    cfg = run.load(args.config)
    # Each arm uses its own disposable smoke directory. The configuration remains
    # unchanged for native authorization, checkpoint identity and gate replay.
    from resume import preflight
    def resume_check(config, commit, pin):
        bound = preflight(run, config, commit, pin, args.resume_config)
        write_json(output/'resume_preflight.json', dict(binding=bound, bridged=bool(args.resume_config)))
        return bound
    total = args.warmup + args.measure if args.mode == 'timing' else 1
    train = measurement_train(run, output.parent / 'trainer', resume_check=resume_check,
                              max_steps=total, redact=scrub)
    from gpu_guard import check as gpu_check
    write_json(output/'gpu_guard.json', gpu_check(local_rank=int(os.environ.get('LOCAL_RANK', '0'))))
    train(cfg, smoke_steps=total, resume_pin=resume_pin)
    progress['stage'] = 'complete'
    done.set()
    write_json(output/'progress.json', progress)


if __name__ == '__main__':
    # Every rank owns a fresh output directory. The root is created only by rank 0's
    # wrapper shell before torchrun; Python's mkdir(parents=True) is race-safe.
    if '--out' in sys.argv:
        i = sys.argv.index('--out') + 1
        sys.argv[i] = str(Path(sys.argv[i]) / ('rank' + os.environ.get('RANK', '0')))
    main()
