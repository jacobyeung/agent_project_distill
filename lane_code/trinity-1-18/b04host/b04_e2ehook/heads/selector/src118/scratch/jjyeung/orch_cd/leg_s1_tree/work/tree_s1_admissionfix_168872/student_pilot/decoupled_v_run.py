"""CPU preparation, world-eight Stage 1, and artifact-only held-out readout."""
import argparse
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext, contextmanager
import copy
import gzip
import json
import os
from pathlib import Path
import random
import resource
import sqlite3
import threading
import time

import torch

from .decoupled_v import (RECIPE, base_manifest, head_settings, load_vision, target_tensors,
                          learning_rate, export_heads, load_heads, readout)
from .p3_provenance import digest, file_pin, load, pinned, write
from .decoupled_vc import VC_RECIPE, VC_BATCH4H_RECIPE, parameter_groups
from .next_gpu_check import check as head_probe
from . import decoupled_resume as resume_state


FIXED_CAMERA = dict(pose_reference='first_group_concat_v1', fov_activation='bounded_sigmoid_v1')
SPATIAL_CAMERA = {**FIXED_CAMERA, 'pose_input': 'spatial_tokens_v1'}


def validate(cfg):
    if cfg.get('schema') != 'decoupled-v-run-v1' or cfg.get('mode') not in ('decoupled_v', 'decoupled_vc'):
        raise ValueError('Explicit Stage-1 mode required')
    if type(cfg.get('all_frames', False)) is not bool:
        raise ValueError('all_frames must be boolean')
    allowed = (RECIPE,) if cfg['mode'] == 'decoupled_v' else (VC_RECIPE, VC_BATCH4H_RECIPE)
    if cfg['recipe'] not in allowed or cfg.get('init_heads') is not None:
        raise ValueError('Use the fixed recipe and fresh head initialization')
    if not cfg.get('base_identity'):
        raise ValueError('Explicit base identity required')
    if 'camera_overrides' in cfg and (cfg['mode'] != 'decoupled_vc' or cfg['camera_overrides'] not in (FIXED_CAMERA, SPATIAL_CAMERA)):
        raise ValueError('Camera override must contain exactly the two fixed head settings or the spatial triple')


def identity(cfg):
    return digest({k: v for k, v in cfg.items() if k not in ('preparation', 'admission')})


def processor_for(root):
    from transformers import AutoProcessor
    processor = AutoProcessor.from_pretrained(root, local_files_only=True, trust_remote_code=False)
    processor._student_pilot_student = 'qwen35'
    return processor


# Pose-only training rows carry this empty reasoning target; held-out readout rows carry none.
READOUT_TARGET = '<think>\n\n</think>\n\n'


def encode(processor, row):
    from .pose_samples import encode_row
    if 'target' not in row:
        row = {**row, 'target': READOUT_TARGET}
    batch, _ = encode_row(processor, row)
    # Text preprocessing preserves existing pixel/timestamp rules; no text tensor reaches the model.
    return {k: batch[k] for k in ('pixel_values_videos', 'video_grid_thw')}


def prepare(cfg):
    from .compact_label_bank import load_bank_for_rows
    from .camera_config import CAMBRIAN_P_ROUTING
    from .common import binding
    validate(cfg)
    if cfg['mode'] == 'decoupled_vc' and cfg.get('reuse_preparation'):
        return reuse_preparation(cfg)
    wall_start, cpu_start = time.monotonic(), time.process_time()
    out = Path(cfg['preparation_output'])
    out.mkdir(parents=True, exist_ok=False)
    manifest = base_manifest(cfg['base_root'], cfg['base_identity'])
    write(out/'model.json', manifest)
    cpdm = load(pinned(cfg['camera_source']))
    camera = {**cpdm['camera'], **cfg.get('camera_overrides', {}), 'supervision': cfg['bank'], 'gate': None, 'lm_gate': None, 'head_only_steps': 0}
    settings = head_settings(camera, manifest['base_identity'], manifest['feature_encoder_sha256'],
                             all_frames=cfg.get('all_frames', False))
    settings['feature_backing'] = cfg['mode']
    division = load(pinned(cfg['division']))
    if division.get('schema') != 'diagnostic-whole-scene-division-v1' or division.get('training_only') is not True:
        raise ValueError('Expected the sealed training-only inherited division')
    train_scenes, heldout = set(division['train_scenes']), set(division['heldout_scenes'])
    rows, seen, frames = [], set(), {}
    with pinned(cfg['rows']).open() as stream:
        for line in stream:
            row = json.loads(line)
            key = row['dataset']+'/'+row['scene']
            if key not in train_scenes or key in heldout or row.get('category') != 'camera_pose_only':
                raise ValueError('Row violates inherited division/head-only routing')
            if row['qid'] in seen:
                raise ValueError('Duplicate row id')
            seen.add(row['qid'])
            for f in row['student_input']['frames']:
                if f['path'] in frames and frames[f['path']] != f['sha256']:
                    raise ValueError('Conflicting RGB pin')
                frames[f['path']] = f['sha256']
            rows.append(row)
    for path, sha in frames.items():
        binding(path, sha)
    start = time.perf_counter()
    records, audit = load_bank_for_rows(str(pinned(cfg['bank'])), rows,
                                       {**settings['camera'], 'row_routing': CAMBRIAN_P_ROUTING,
                                        **({'max_groups': 32} if cfg.get('all_frames') else {})})
    audit.pop('row_routing', None)
    seconds = time.perf_counter()-start
    if not audit['depth_rows'] or not audit['gravity_rows']:
        raise ValueError('Stage 1 requires matched depth and gravity supervision')
    db = out/'rows.sqlite'
    conn = sqlite3.connect(db)
    conn.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT NOT NULL, target TEXT NOT NULL)')
    for i, (row, target) in enumerate(zip(rows, records)):
        conn.execute('INSERT INTO rows VALUES (?,?,?)', (i, json.dumps(row), json.dumps(target)))
    conn.commit(); conn.close()
    # Measure real RGB decode/augmentation/native processor work only at this CPU preparation site.
    processor = processor_for(manifest['root'])
    timings = []
    for row in rows[:min(16, len(rows))]:
        start = time.perf_counter(); encode(processor, row); timings.append(time.perf_counter()-start)
    receipt = dict(schema='decoupled-v-preparation-v1', config_sha256=identity(cfg),
                   model=file_pin(out/'model.json'), database=file_pin(db), count=len(rows),
                   settings=settings, audit=audit, label_seconds_per_item=seconds/len(rows),
                   rgb_seconds_per_item=sum(timings)/len(timings), rgb_sample_count=len(timings),
                   inputs={k: cfg[k] for k in ('rows', 'division', 'bank', 'camera_source')},
                   larger_microbatch_admitted=False)
    if cfg.get('all_frames'):
        receipt.update(wall_seconds=time.monotonic()-wall_start, cpu_seconds=time.process_time()-cpu_start,
                       bytes=db.stat().st_size+(out/'model.json').stat().st_size)
    write(out/'receipt.json', receipt)
    return receipt


def reuse_preparation(cfg):
    """Derive a V-C receipt from authenticated V data, without copying the database."""
    source = cfg['reuse_preparation']
    old = load(pinned(source['config']))
    if old.get('mode') != 'decoupled_v':
        raise ValueError('Reuse requires the frozen V preparation')
    old['preparation'] = source['receipt']
    receipt, manifest = prepared(old)
    fields = ('rows', 'division', 'bank', 'camera_source', 'base_root', 'base_identity', 'readout')
    if cfg.get('all_frames', False) != old.get('all_frames', False):
        raise ValueError('Reused all-frame contract differs')
    if any(cfg[k] != old[k] for k in fields):
        raise ValueError('Reused preparation inputs differ')
    if (receipt['inputs'] != {k: cfg[k] for k in ('rows', 'division', 'bank', 'camera_source')}
            or manifest['kind'] != 'base' or manifest['root'] != cfg['base_root']
            or manifest['base_identity'] != cfg['base_identity']):
        raise ValueError('Reused base or input provenance differs')
    settings = receipt['settings']
    if settings != head_settings(settings['camera'], cfg['base_identity'], manifest['feature_encoder_sha256'],
                                 all_frames=cfg.get('all_frames', False)):
        raise ValueError('Reused feature contract differs')
    out = Path(cfg['preparation_output'])
    out.mkdir(parents=True, exist_ok=False)
    result = {**receipt, 'config_sha256': identity(cfg), 'reused_from': source,
              'settings': reused_settings(settings, cfg)}
    write(out/'receipt.json', result)
    return result


def reused_settings(settings, cfg):
    # Targets and source pins stay unchanged; only the head recipe is derived.
    return {**settings, 'feature_backing': 'decoupled_vc',
            'camera': {**settings['camera'], **cfg.get('camera_overrides', {})}}


def prepared(cfg, require_admission=False):
    validate(cfg)
    receipt = load(pinned(cfg['preparation']))
    if receipt.get('schema') != 'decoupled-v-preparation-v1' or receipt['config_sha256'] != identity(cfg):
        raise ValueError('CPU preparation differs from the run')
    for p in receipt['inputs'].values():
        pinned(p)
    pinned(receipt['database'])
    manifest = load(pinned(receipt['model']))
    if receipt['settings']['feature_backing'] != cfg['mode'] or receipt['settings']['anchors'] != (
            list(range(1, 33)) if cfg.get('all_frames') else list(range(2, 33, 2))):
        raise ValueError('Prepared head contract differs')
    if cfg['mode'] == 'decoupled_vc' and cfg.get('reuse_preparation'):
        if (receipt.get('reused_from') != cfg['reuse_preparation']
                or receipt['settings']['feature_backing'] != 'decoupled_vc'):
            raise ValueError('Private encoder preparation differs')
        for pin in receipt['reused_from'].values():
            pinned(pin)
        if 'camera_overrides' in cfg:
            source = load(Path(cfg['reuse_preparation']['receipt']['path']))
            if (receipt['settings'] != reused_settings(source['settings'], cfg)
                    or any(receipt[k] != source[k] for k in ('model', 'database', 'inputs', 'count', 'audit'))):
                raise ValueError('Derived head settings or reused data differ')
    if 'camera_overrides' in cfg and any(
            receipt['settings']['camera'].get(k) != v for k, v in cfg['camera_overrides'].items()):
        raise ValueError('Prepared camera overrides differ')
    if require_admission:
        admission = load(pinned(cfg['admission']))
        if (admission.get('verdict') != 'PASS' or admission.get('config_sha256') != identity(cfg)
                or admission.get('preparation') != cfg['preparation'] or not admission.get('reviewer')):
            raise ValueError('Parent must bind an independent review of this exact preparation')
    return receipt, manifest


def index_batches(count):
    """The production shuffle, including wraparound within a global batch."""
    if count < 1:
        raise ValueError('Empty preparation')
    order, epoch, cursor = list(range(count)), -1, 0
    while True:
        indices = []
        while len(indices) < RECIPE['global_batch']:
            if epoch < 0 or cursor == len(order):
                epoch += 1; cursor = 0
                random.Random(RECIPE['seed']+epoch).shuffle(order)
            take = min(RECIPE['global_batch']-len(indices), len(order)-cursor)
            indices.extend(order[cursor:cursor+take]); cursor += take
        yield indices


def row_workers(local_world):
    """Reserve a CPU for the rank and cap decoders at four within its allocation."""
    cpus = len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else (os.cpu_count() or 1)
    budgets = [max(1, cpus // local_world)]
    for key in ('SLURM_CPUS_ON_NODE', 'SLURM_CPUS_PER_TASK'):
        if os.environ.get(key):
            budgets.append(max(1, int(os.environ[key]) // local_world))
    if os.environ.get('SLURM_CPUS_PER_GPU'):
        budgets.append(int(os.environ['SLURM_CPUS_PER_GPU']))
    return max(1, min(4, min(budgets)-1))


def rank_rows(count, rank, world, steps, start_step=0):
    batches = index_batches(count)
    for _ in range(start_step):
        next(batches)
    for _ in range(start_step, steps):
        yield from next(batches)[rank::world]


@contextmanager
def prefetch_rows(database, processor, indices, *, workers, all_frames=False):
    """Yield ordered CPU rows with at most four pending decodes per rank.

    Each thread owns its processor and read-only connection. Threads avoid
    forking a CUDA rank or copying image tensors through process IPC. The row
    encoder uses row-local randomness; it never draws from training's RNG.
    """
    state = threading.local()
    connections, pending = [], deque()
    lock = threading.Lock()
    indices = iter(indices)

    def decode(index):
        if not hasattr(state, 'connection'):
            state.processor = copy.deepcopy(processor)
            # Only the owning worker queries this connection; the main thread
            # closes it after every worker has joined, including on failure.
            state.connection = sqlite3.connect('file:'+str(database)+'?mode=ro', uri=True,
                                               check_same_thread=False)
            with lock:
                connections.append(state.connection)
        raw, target = state.connection.execute('SELECT row,target FROM rows WHERE i=?', (index,)).fetchone()
        batch = encode(state.processor, json.loads(raw))
        targets = target_tensors(json.loads(target), 'cpu', **({'all_frames': True} if all_frames else {}))
        return index, batch, targets

    pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix='row-decode')

    def submit():
        index = next(indices, None)
        if index is not None:
            pending.append(pool.submit(decode, index))

    def stream():
        for _ in range(4):
            submit()
        while pending:
            result = pending.popleft().result()  # Propagate errors at this row, before its forward.
            submit()
            yield result

    rows = stream()
    try:
        yield rows
    finally:
        rows.close()
        pool.shutdown(wait=True, cancel_futures=True)
        for connection in connections:
            connection.close()


def setup_mode(model, cfg):
    if cfg['mode'] == 'decoupled_vc':
        model.gradient_checkpointing = cfg.get('gradient_checkpointing', True)
    model.train()
    model.auxiliary_heads.requires_grad_(True)


def dryrun(cfg, report_path):
    """Exercise the admitted first batch without CUDA or a process group."""
    from .decoupled_v import tensor_identity
    from safetensors import safe_open
    report = dict(status='FAIL', phases_seconds={}, checks={}, ranks=[], grad_norms={})
    connection = None

    @contextmanager
    def phase(name):
        start = time.perf_counter()
        try:
            yield
        except Exception:
            report['checks']['phase_'+name] = False
            raise
        else:
            report['checks']['phase_'+name] = True
        finally:
            report['phases_seconds'][name] = time.perf_counter()-start

    def check(name, passed):
        report['checks'][name] = bool(passed)
        if not passed:
            raise ValueError('Dry run check failed: '+name)

    def fingerprint(parameters):
        return tensor_identity({str(i): p.detach() for i, p in enumerate(parameters)})

    try:
        with phase('prepared'):
            receipt, manifest = prepared(cfg, require_admission=True)
        torch.manual_seed(RECIPE['seed'])
        with phase('load_vision'):
            model = load_vision(manifest, receipt['settings']).to('cpu')
        with phase('mode_optimizer'):
            setup_mode(model, cfg)
            groups = parameter_groups(model, cfg['recipe'])
            optimizer = torch.optim.AdamW(groups, weight_decay=cfg['recipe']['weight_decay'])
            before = {g['name']: fingerprint(g['params']) for g in groups}
            frozen = [p for p in model.model.parameters() if not p.requires_grad]
            frozen_before = fingerprint(frozen)
            report['dtype_policy'] = dict(device='cpu', encoder_parameters=str(next(model.model.parameters()).dtype),
                heads=str(next(model.auxiliary_heads.parameters()).dtype), encoder_compute='torch.bfloat16',
                differences=['CPU device; no CUDA, NCCL or DDP; one row backward rather than eight-row accumulation'])
        with phase('processor'):
            processor = processor_for(manifest['root'])
        with phase('database_order'):
            connection = sqlite3.connect('file:'+receipt['database']['path']+'?mode=ro', uri=True)
            indices = next(index_batches(receipt['count']))
            report['step_1_indices'] = indices
        first = None
        for rank in range(8):
            with phase('rank_'+str(rank)+'_encode_targets'):
                index = indices[rank::8][0]
                raw, target = connection.execute('SELECT row,target FROM rows WHERE i=?', (index,)).fetchone()
                batch = encode(processor, json.loads(raw))
                targets = target_tensors(json.loads(target), 'cpu', **({'all_frames': True} if cfg.get('all_frames') else {}))
                report['ranks'].append(dict(rank=rank, index=index,
                    token_grid_shapes={k:list(v.shape) for k,v in batch.items()},
                    grid=batch['video_grid_thw'].tolist(),
                    target_shapes={k:list(v.shape) for k,v in targets.items()}))
                if rank == 0:
                    first = batch, targets
        check('all_rank_rows_encoded', len(report['ranks']) == 8)
        optimizer.zero_grad(set_to_none=True)
        with phase('forward'):
            loss = model(*first).mean()/8
            check('finite_loss', torch.isfinite(loss).item())
            report['loss'] = float(loss.detach())
        with phase('backward'):
            loss.backward()
            for group in groups:
                grads = [p.grad for p in group['params'] if p.grad is not None]
                check(group['name']+'_grads_present', bool(grads) and
                      (group['name'] != 'heads' or len(grads) == len(group['params'])))
                check(group['name']+'_grads_finite', all(torch.isfinite(g).all().item() for g in grads))
                norm = sum(g.detach().double().square().sum().item() for g in grads)**.5
                report['grad_norms'][group['name']] = norm
                check(group['name']+'_grads_nonzero', norm > 0)
        with phase('head_probe'):
            report['head_probe'] = dict(step=1, rank=0, row_index=indices[0],
                                        **head_probe(model, *first))
        with phase('optimizer_step'):
            torch.nn.utils.clip_grad_norm_([p for g in groups for p in g['params']], 1.)
            for group in optimizer.param_groups:
                group['lr'] = learning_rate(1, {**cfg['recipe'], 'learning_rate':group['initial_lr']})
            optimizer.step()
            for group in groups:
                check(group['name']+'_updated', before[group['name']] != fingerprint(group['params']))
            check('frozen_parameters_unchanged', frozen_before == fingerprint(frozen) and
                  all(p.grad is None for p in frozen))
        with phase('base_unchanged'):
            # Recheck original vision bytes, including V-C's source, which is never trained.
            state = {}
            for name in manifest['files']:
                if name.endswith('.safetensors'):
                    with safe_open(Path(manifest['root'])/name, framework='pt', device='cpu') as handle:
                        for key in handle.keys():
                            if key.startswith('model.visual.'):
                                state[key] = handle.get_tensor(key)
            check('base_unchanged', tensor_identity(state) == manifest['feature_encoder_sha256'])
        report['status'] = 'PASS'
        return report
    except Exception as error:
        report['error_type'] = type(error).__name__
        raise
    finally:
        if connection is not None:
            connection.close()
        report['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
        write(report_path, report)


def update_smoke(path, value):
    # Only the rank-zero owner of a newly claimed smoke directory calls this.
    temporary = path.with_suffix('.part')
    temporary.write_text(json.dumps(value, sort_keys=True)+'\n')
    os.replace(temporary, path)


def training_ranks():
    rank, world, local = (int(os.environ[k]) for k in ('RANK', 'WORLD_SIZE', 'LOCAL_RANK'))
    if world != 8 or not os.environ.get('SLURM_JOB_ID'):
        raise ValueError('Production training requires the parent world-eight Slurm job')
    return rank, world, local


def _train(cfg, smoke_steps=None, resume=False):
    import torch.distributed as dist
    from torch.nn.parallel import DistributedDataParallel
    receipt, manifest = prepared(cfg, require_admission=True)
    rank, world, local = training_ranks()
    # The kit owns the bound run directory; the trainer exclusively claims its child.
    output = (Path(cfg['output'])/'smoke'/os.environ['SLURM_JOB_ID'] if smoke_steps is not None
              else Path(cfg['output'])/'train')
    if rank == 0 and not resume:
        output.mkdir(parents=True, exist_ok=False)
        write(output/'run.json', cfg)
    bound = resume_state.binding(cfg, identity(cfg), world, receipt['count']) if resume else None
    payload = resume_state.newest(output, bound) if resume else None
    start_step = payload['next_batch'] if payload else 0
    torch.cuda.set_device(local)
    if smoke_steps is not None:
        torch.cuda.reset_peak_memory_stats(local)
    dist.init_process_group('nccl')
    dist.barrier()
    if smoke_steps is None and bound is None:
        bound = resume_state.binding(cfg, identity(cfg), world, receipt['count'])
    torch.manual_seed(RECIPE['seed'])
    recipe = cfg['recipe']
    model = load_vision(manifest, receipt['settings']).to(device=f'cuda:{local}')
    setup_mode(model, cfg)
    # ViT merger and any blocks after the last selected feature have no head loss.
    wrapped = DistributedDataParallel(model, device_ids=[local], broadcast_buffers=False,
                                      find_unused_parameters=cfg['mode'] == 'decoupled_vc')
    groups = parameter_groups(model, recipe)
    parameters = [p for group in groups for p in group['params']]
    optimizer = torch.optim.AdamW(groups, weight_decay=recipe['weight_decay'])
    processor = processor_for(manifest['root'])
    if payload is not None:
        resume_state.restore(payload, model, optimizer, rank)
        if rank == 0:
            resume_state.restore_metrics(output, payload)
        dist.barrier()
    steps = smoke_steps if smoke_steps is not None else recipe['steps']
    indices = rank_rows(receipt['count'], rank, world, steps, start_step)
    frozen = {n: p._version for n, p in model.model.named_parameters() if not p.requires_grad}
    smoke = dict(status='RUNNING', steps=[], per_rank_peak_cuda_memory=[], head_probes=[])
    probe_batch = None
    with prefetch_rows(receipt['database']['path'], processor, indices,
                       workers=row_workers(int(os.environ.get('LOCAL_WORLD_SIZE', world))),
                       all_frames=cfg.get('all_frames', False)) as rows:
        for step in range(start_step+1, steps+1):
            if smoke_steps is not None:
                torch.cuda.synchronize(local)
                step_start = time.perf_counter()
                data_seconds = 0.
                compute_seconds = 0.
            optimizer.zero_grad(set_to_none=True)
            losses = []
            for micro in range(RECIPE['global_batch']//world):
                if smoke_steps is not None:
                    data_start = time.perf_counter()
                index, cpu_batch, cpu_targets = next(rows)
                batch = {k: v.to(local) for k, v in cpu_batch.items()}
                targets = {k: v.to(local) for k, v in cpu_targets.items()}
                if smoke_steps is not None:
                    torch.cuda.synchronize(local)
                    data_seconds += time.perf_counter()-data_start
                    compute_start = time.perf_counter()
                with wrapped.no_sync() if micro < 7 else nullcontext():
                    loss = wrapped(batch, targets).mean()/8
                    if not torch.isfinite(loss):
                        raise ValueError('Nonfinite Stage-1 loss')
                    loss.backward()
                if smoke_steps is not None:
                    torch.cuda.synchronize(local)
                    compute_seconds += time.perf_counter()-compute_start
                losses.append(loss.detach())
            if smoke_steps is not None and rank == 0 and step in (1, 3):
                if probe_batch is None:
                    probe_batch = batch, targets
                    probe_index = index
                smoke['head_probes'].append(dict(step=step, rank=rank, row_index=probe_index,
                    component_loss_row_index=index, **head_probe(model, *probe_batch)))
                update_smoke(output/'smoke.json', smoke)
            for p in model.auxiliary_heads.parameters():
                if p.grad is None:
                    raise ValueError('Missing head gradient')
            if cfg['mode'] == 'decoupled_vc' and not any(p.grad is not None for p in model.model.visual.parameters()):
                raise ValueError('Private encoder graph was detached')
            for p in parameters:
                if p.grad is not None and not torch.isfinite(p.grad).all():
                    raise ValueError('Missing or nonfinite head gradient')
            torch.nn.utils.clip_grad_norm_(parameters, 1.)
            for group in optimizer.param_groups:
                group['lr'] = learning_rate(step, {**recipe, 'learning_rate': group['initial_lr']})
            optimizer.step()
            total = torch.stack(losses).sum()
            dist.all_reduce(total); total /= world
            if rank == 0:
                with (output/'metrics.jsonl').open('a') as f:
                    f.write(json.dumps(dict(step=step, loss=float(total), lr=learning_rate(step, recipe),
                                           group_lrs={g['name']:g['lr'] for g in optimizer.param_groups}))+'\n')
            if smoke_steps is not None:
                torch.cuda.synchronize(local)
                timing = dict(rank=rank, wall_seconds=time.perf_counter()-step_start,
                              data_wait_seconds=data_seconds, compute_seconds=compute_seconds)
                timing['other_seconds'] = max(0., timing['wall_seconds']-data_seconds-compute_seconds)
                timings = [None]*world
                dist.all_gather_object(timings, timing)
                smoke['steps'].append(dict(step=step, loss=float(total),
                                          wall_seconds=max(t['wall_seconds'] for t in timings), ranks=timings))
                if rank == 0:
                    update_smoke(output/'smoke.json', smoke)
            if smoke_steps is None and step in recipe['milestones']:
                if any(p.grad is not None or p._version != frozen[n]
                       for n, p in model.model.named_parameters() if n in frozen):
                    raise ValueError('Frozen base vision changed')
                provenance = dict(base=receipt['model'], start=receipt['model'], preparation=cfg['preparation'],
                                  recipe=recipe, config_sha256=identity(cfg))
                if step < recipe['steps']:
                    resume_state.save(output, step, model, optimizer, bound,
                                      lambda directory: export_heads(model, directory, step, provenance))
                elif rank == 0:
                    resume_state.final_export(output, step,
                        lambda directory: export_heads(model, directory, step, provenance))
                dist.barrier()
    if smoke_steps is not None:
        memory = dict(rank=rank, allocated_bytes=torch.cuda.max_memory_allocated(local),
                      reserved_bytes=torch.cuda.max_memory_reserved(local))
        smoke['per_rank_peak_cuda_memory'] = [None]*world
        dist.all_gather_object(smoke['per_rank_peak_cuda_memory'], memory)
        smoke['status'] = 'PASS'
        if rank == 0:
            update_smoke(output/'smoke.json', smoke)
    dist.destroy_process_group()


def train(cfg, smoke_steps=None, resume=False):
    if resume and smoke_steps is not None:
        raise ValueError('Resume cannot be combined with smoke steps')
    if smoke_steps is None:
        with resume_state.run_lock(cfg['output'], int(os.environ['RANK'])):
            try:
                return _train(cfg, resume=resume)
            finally:
                import torch.distributed as dist
                if dist.is_initialized():
                    dist.destroy_process_group()
    if type(smoke_steps) is not int or not 1 <= smoke_steps <= 10:
        raise ValueError('Smoke steps must be between 1 and 10')
    # The claim must remain exclusive even on failure; never overwrite an older attempt.
    output = Path(cfg['output'])/'smoke'/os.environ.get('SLURM_JOB_ID', '')
    existed = output.exists()
    try:
        return _train(cfg, smoke_steps)
    except Exception as error:
        if not existed and output.is_dir() and os.environ.get('RANK') == '0':
            path = output/'smoke.json'
            result = load(path) if path.exists() else dict(steps=[], per_rank_peak_cuda_memory=[])
            update_smoke(path, {**result, 'status':'FAIL', 'error_type':type(error).__name__})
        raise
    finally:
        import torch.distributed as dist
        if dist.is_initialized():
            dist.destroy_process_group()


def evaluate(cfg, artifact_pins):
    from .compact_label_bank import read_bank, frame_set_sha256
    from .gate_eval import evaluate as score_gate
    from .gate_driver import heads_of
    from .readout_geometry import validation_summary
    receipt, manifest = prepared(cfg, require_admission=True)
    held = cfg['readout']
    if cfg.get('all_frames'):
        from .all_frame_bank import read_bank
    bank = read_bank(str(pinned(held['bank'])))
    lookup = {k: i for i, k in enumerate(zip(bank['dataset_tokens'].tolist(), bank['scene_tokens'].tolist()))}
    training = {tuple(x) for x in load(pinned(held['training_scenes']))['scenes']}
    if len(lookup) != 38 or set(lookup) & training:
        raise ValueError('Readout must cover 38 disjoint held-out scenes')
    inventory = load(pinned(held['rows_inventory']))
    chosen = {}
    for pin in inventory['files']:
        with gzip.open(pinned(pin), 'rt') as f:
            for line in f:
                row = json.loads(line); key = row['dataset'], row['scene']
                if key not in lookup:
                    raise ValueError('Extra held-out scene')
                i = lookup[key]
                if frame_set_sha256(row['student_input']['frame_indices']) != str(bank['frame_set_sha256'][i]):
                    raise ValueError('Readout bank frame selection differs')
                if key in chosen and row['student_input']['frames'] != chosen[key]['student_input']['frames']:
                    raise ValueError('Multiple held-out RGB selections')
                chosen.setdefault(key, row)
    if set(chosen) != set(lookup):
        raise ValueError('Incomplete held-out coverage')
    processor = processor_for(manifest['root'])
    model = load_vision(manifest, receipt['settings']).to('cuda:0')
    output = Path(cfg['readout_output']); output.mkdir(parents=True, exist_ok=False)
    for pin in artifact_pins:
        artifact = load_heads(model, pin)
        if cfg['mode'] == 'decoupled_vc':
            from .decoupled_vc import freeze_for_inference
            freeze_for_inference(model)
        sessions, records = {}, []
        for key, row in sorted(chosen.items()):
            i = lookup[key]
            batch = {k: v.to('cuda:0') for k, v in encode(processor, row).items()}
            uv, mask = bank['point_depth_uv'][i], bank['point_depth_mask'][i]
            values = readout(model, batch, uv)
            sessions['/'.join(key)] = {**values, 'qid': row['qid'], 'bank': held['bank'],
                'point_depth_uv': uv.tolist(), 'point_depth_mask': mask.tolist(),
                'frame_indices': row['student_input']['frame_indices'],
                'selection_key': hashlib_selection(row)}
            records.append({'dataset': key[0], 'scene': key[1],
                'gt': {'camera': bank['camera'][i].astype('float64'), 'camera_mask': bank['camera_mask'][i],
                       'gravity': bank['gravity'][i].astype('float64'), 'gravity_mask': bool(bank['gravity_mask'][i]),
                       'trajectory_scale': float(bank['trajectory_scale'][i]), 'point_depth_uv': uv.astype('float64'),
                       'point_depth_gt': bank['point_depth_gt'][i].astype('float64'), 'point_depth_mask': mask,
                       **({'depth_anchor_frames': bank['depth_anchor_frames'].tolist()} if cfg.get('all_frames') else {})},
                'pred': {'camera': values['raw_pose'], 'gravity': values['gravity_up'],
                         'trajectory_step_m': values['trajectory_step_m'], 'point_depth': values['point_depth'],
                         'geometry_error': values.get('geometry_error'),
                         'invalid_fov_frames': values.get('invalid_fov_frames', [])}})
        result = score_gate(records, heads_of(model.auxiliary_heads.camera), sorted(lookup), sorted(training))
        if cfg.get('all_frames'):
            from .all_frame_readout import evaluate as score_all_frames
            result['all_frame_comparison'] = score_all_frames(records, heads_of(model.auxiliary_heads.camera),
                                                               sorted(lookup), sorted(training))
        summary = {'passed': result['gate']['passed'], 'checks': result['gate']['checks'], 'summary': result['overall'],
                   'geometry_validation': validation_summary(sessions.values())}
        # P3 queries every point, including masked groups. Only bank-mask True points
        # enter depth metrics or decisions, exactly as in the shared A0 scorer.
        depth_semantics = {'unit': 'metres', 'convention': 'optical_axis',
                           'predicted_points': 'all bank UV points including masked groups',
                           'scored_points': 'only held-out bank point_depth_mask True points',
                           'bank': held['bank']}
        report_path = output/'reports'/f"report_{artifact['step']}.json"
        write(report_path, {'report': {'heads': summary}, 'detail': result,
                            'source': artifact, 'heads': artifact['weights'],
                            'depth_semantics': depth_semantics})
        write(output/f"{artifact['step']}.json", dict(heads=pin, scene_first_session=sessions,
              gate_report_summary=summary, report=file_pin(report_path), depth_semantics=depth_semantics))


def hashlib_selection(row):
    import hashlib
    return hashlib.sha256('\n'.join(f['sha256'] for f in row['student_input']['frames']).encode()).hexdigest()


def probe(cfg, artifact_pin):
    """One-GPU, 32-RGB-frame private-stack inference cost, excluding RGB decode."""
    import statistics
    from .decoupled_v import features
    from .decoupled_vc import freeze_for_inference
    receipt, manifest = prepared(cfg, require_admission=True)
    if cfg['mode'] != 'decoupled_vc' or not os.environ.get('SLURM_JOB_ID') or torch.cuda.device_count() != 1:
        raise ValueError('Probe requires the parent one-GPU V-C Slurm allocation')
    torch.cuda.set_device(0)
    inventory = load(pinned(cfg['readout']['rows_inventory']))
    with gzip.open(pinned(inventory['files'][0]), 'rt') as stream:
        row = json.loads(next(stream))
    if len(row['student_input']['frames']) != 32 or len(row['student_input']['frame_indices']) != 32:
        raise ValueError('Probe requires exactly 32 RGB frames')
    model = load_vision(manifest, receipt['settings'])
    artifact = load_heads(model, artifact_pin)
    freeze_for_inference(model).to('cuda:0')
    batch = {k: v.to('cuda:0') for k, v in encode(processor_for(manifest['root']), row).items()}
    if batch['video_grid_thw'].shape != (1, 3) or int(batch['video_grid_thw'][0, 0]) != 16:
        raise ValueError('Probe must use 16 fused temporal pairs')
    batch['pixel_values_videos'] = batch['pixel_values_videos'].bfloat16()
    measurements = {}
    operations = {
        'encoder_forward': lambda: model.model.visual(batch['pixel_values_videos'], grid_thw=batch['video_grid_thw']),
        'encoder_and_feature_capture': lambda: features(model, batch),
    }
    with torch.inference_mode():
        for name, operation in operations.items():
            for _ in range(5):
                operation()
            torch.cuda.synchronize()
            baseline = torch.cuda.memory_allocated()
            torch.cuda.reset_peak_memory_stats()
            wall, gpu = [], []
            for _ in range(20):
                start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
                before = time.perf_counter()
                start.record(); operation(); end.record()
                torch.cuda.synchronize()
                wall.append((time.perf_counter()-before)*1000)
                gpu.append(start.elapsed_time(end))
            peak = torch.cuda.max_memory_allocated()
            measurements[name] = dict(wall_ms=wall, cuda_ms=gpu, median_wall_ms=statistics.median(wall),
                median_cuda_ms=statistics.median(gpu), p95_wall_ms=sorted(wall)[18],
                baseline_allocated_bytes=baseline, peak_allocated_bytes=peak,
                incremental_peak_bytes=peak-baseline, peak_reserved_bytes=torch.cuda.max_memory_reserved())
    write(cfg['probe_output'], dict(schema='decoupled-vc-probe-v1', artifact=artifact_pin,
        encoder_copy=artifact['encoder_copy'], frames=32, video_grid_thw=batch['video_grid_thw'].tolist(),
        pixel_shape=list(batch['pixel_values_videos'].shape), selection_key=hashlib_selection(row),
        row_inventory=cfg['readout']['rows_inventory'], warmup=5, repeats=20,
        device=torch.cuda.get_device_name(0), torch_version=torch.__version__, cuda_version=torch.version.cuda,
        measurements=measurements, scope='one private encoder plus heads resident; no LM or original encoder; RGB decode excluded'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'train', 'evaluate', 'probe', 'dryrun', 'overfit'))
    parser.add_argument('--config', required=True)
    parser.add_argument('--artifacts', nargs='*')
    parser.add_argument('--report')
    parser.add_argument('--smoke-steps', type=int)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if args.smoke_steps is not None and args.action != 'train':
        parser.error('--smoke-steps requires train')
    if args.resume and (args.action != 'train' or args.smoke_steps is not None):
        parser.error('--resume requires full train')
    if args.report is not None and args.action not in ('dryrun', 'overfit'):
        parser.error('--report requires dryrun or overfit')
    cfg = load(args.config)
    if args.action == 'prepare':
        prepare(cfg)
    elif args.action == 'train':
        train(cfg, args.smoke_steps, resume=args.resume)
    elif args.action == 'dryrun':
        if not args.report:
            parser.error('dryrun requires --report')
        dryrun(cfg, args.report)
    elif args.action == 'overfit':
        if not args.report:
            parser.error('overfit requires --report')
        from .pose_overfit import real_row_overfit
        real_row_overfit(cfg, args.report)
    else:
        if not args.artifacts:
            raise ValueError('Readout requires milestone artifact JSON paths')
        if args.action == 'probe':
            if len(args.artifacts) != 1:
                raise ValueError('Probe requires exactly one milestone')
            probe(cfg, file_pin(args.artifacts[0]))
        else:
            evaluate(cfg, [file_pin(p) for p in args.artifacts])


if __name__ == '__main__':
    main()
