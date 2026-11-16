"""Fixed-row teacher-forced diagnostics through the pinned final C1 trainer."""
import fcntl
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import random
import statistics

from .items import sha256
from .pointing_candidates import validate_pin

COMMIT = '19631080d1255229a23f06b3d14a26c8398a4b90'
STREAMS = ('pose', 'vqa', 'pointing', 'routing')
SEGMENT = dict(vqa='vqa_answer', pointing='pointing_coord')


def validate_request(request):
    if (request.get('preset') != 'heldout_loss' or request.get('kind') != 'routed'
            or request['cfg'].get('training_mode') != 'final'
            or request.get('trainer_commit') != COMMIT or request.get('max_new_tokens') is not None
            or type(request.get('rows_per_stream')) is not int
            or not 1 <= request['rows_per_stream'] <= 4096 or type(request.get('seed')) is not int):
        raise ValueError('Invalid held-out loss protocol')
    validate_pin(request['artifact'])
    for name, pin in request['heldout_streams'].items():
        if name not in STREAMS[1:]:
            raise ValueError('Unknown receipt stream')
        validate_pin(pin)


def sample_indices(count, limit, seed, stream, split):
    """No artifact, step, rank or worker-count dependence; never repeat rows."""
    if count < 1:
        raise ValueError('Empty row population')
    salt = hashlib.sha256(f'{seed}:{stream}:{split}'.encode()).hexdigest()
    return sorted(random.Random(int(salt, 16)).sample(range(count), min(count, limit)))


def measure(model, batch, targets, stream):
    """Use the trainer's component and logging sums; never recompute CE."""
    import torch
    model.eval()
    with torch.no_grad():
        result = model(batch, targets, stream=stream)
    component = float(result['components'][stream])
    if not math.isfinite(component):
        raise ValueError('Nonfinite trainer component')
    tokens = int((batch['labels'][:, 1:] != -100).sum()) if stream != 'pose' else 0
    total, count = component * tokens, tokens
    if stream in SEGMENT:
        total, count = result['metrics'].get('segments', {}).get(SEGMENT[stream], [0., 0])
    if type(count) is not int or count < 0 or not math.isfinite(float(total)):
        raise ValueError('Invalid supervised token statistics')
    value = component if stream == 'pose' else (float(total)/count if count else None)
    if value is not None and not math.isfinite(value):
        raise ValueError('Nonfinite stream loss')
    return dict(loss=value, component=component, ce_sum=float(total), tokens=int(count))


def stats(records):
    values = [r['loss'] for r in records if r['loss'] is not None]
    tokens = sum(r['tokens'] for r in records)
    return dict(mean=statistics.fmean(values) if values else None,
                std=statistics.pstdev(values) if values else None, n=len(records), n_scored=len(values),
                component_mean=statistics.fmean(r['component'] for r in records) if records else None,
                token_mean=sum(r['ce_sum'] for r in records)/tokens if tokens else None,
                supervised_tokens=tokens)


def install_paths(request):
    """Resolve staged physical paths without changing config/artifact identity."""
    from student_pilot import p3_provenance as provenance
    mapping = request.get('roots', {}).get('path_map', {})
    if mapping:
        original = provenance.pinned
        def pinned(pin):
            validate_pin(pin)
            text = pin['path']
            for old, new in sorted(mapping.items(), key=lambda x: -len(x[0])):
                if text == old or text.startswith(old.rstrip('/')+'/'):
                    text = new.rstrip('/')+text[len(old.rstrip('/')):]
                    break
            return original(dict(path=text, sha256=pin['sha256']))
        provenance.pinned = pinned
        frames = json.loads(os.environ.get('STUDENT_FRAME_ROOT_MAP', '{}'))
        frames.update(mapping)
        os.environ['STUDENT_FRAME_ROOT_MAP'] = json.dumps(frames)


def verify_source(request):
    import student_pilot
    from student_pilot import p3_provenance as p
    from student_pilot import carrier_c1_run as trainer
    root = Path(student_pilot.__file__).resolve().parent.parent
    spec = request['loss_trainer']
    inventory = p.load(p.pinned(spec['inventory']))
    actual = {str(f.relative_to(root)): sha256(f) for f in root.rglob('*') if f.is_file()}
    if spec['commit'] != COMMIT or inventory != actual:
        raise ValueError('Loss source inventory differs')
    seal = p.load(p.pinned(request['cfg']['code']))
    closure = {str(f.relative_to(root)): sha256(f) for f in p.source_files([Path(trainer.__file__)])}
    if (seal.get('clean') is not True or seal.get('commit') != COMMIT or seal.get('sources') != closure):
        raise ValueError('T0 config code closure differs')


def heldout_pins(cfg, prep, explicit, receipts):
    selected = {}
    for owner in (prep, cfg):
        for name, entry in owner.get('streams', {}).items():
            if name in STREAMS[1:] and isinstance(entry, dict):
                value = entry.get('heldout_receipt') or entry.get('heldout')
                if value:
                    selected[name] = value
        for key in ('heldout', 'heldout_streams'):
            value = owner.get(key)
            if isinstance(value, dict):
                for name in STREAMS[1:]:
                    if value.get(name):
                        selected[name] = value[name]
        if owner.get('routing_heldout'):
            selected['routing'] = owner['routing_heldout']
    for name, receipt in receipts.items():
        for key in ('heldout_receipt', 'heldout'):
            value = receipt.get(key)
            if isinstance(value, dict) and set(value) == {'path', 'sha256'}:
                selected.setdefault(name, value)
    selected.update(explicit)
    for pin in selected.values():
        validate_pin(pin)
    return selected


class DatabaseRows:
    def __init__(self, pin, stream, prep, processor, training_receipt):
        from student_pilot import carrier_c1_run as t, carrier_c1_routing as routing
        from student_pilot.p3_provenance import load, pinned
        receipt = load(pinned(pin))
        self.heldout_scenes = None
        if receipt.get('scene_role', receipt.get('split')) != 'heldout':
            if stream == 'routing' or not receipt.get('division'):
                raise ValueError('Receipt does not attest heldout scene role')
            division = load(pinned(receipt['division']))
            self.heldout_scenes = set(division['heldout_scenes'])
            if self.heldout_scenes & set(division['train_scenes']):
                raise ValueError('Heldout scene division overlaps training')
        if stream == 'routing' and receipt.get('schema') != routing.ROUTING_SCHEMA:
            raise ValueError('Heldout routing receipt schema differs')
        if stream != 'routing' and receipt.get('stream') != stream:
            raise ValueError('Heldout receipt stream differs')
        if (receipt['database'] == training_receipt.get('database')
                or receipt['database']['sha256'] == training_receipt.get('database', {}).get('sha256')):
            raise ValueError('Heldout database equals training database')
        # Reuse the training row reader, including routing response masking and segment tags.
        self.rows = t.Rows({**prep, 'streams': {stream: dict(receipt=pin,
                           database=receipt['database'], count=receipt['count'])}}, processor)
        self.stream, self.pin = stream, pin
        self.count = receipt['count']

    def get(self, index):
        if self.heldout_scenes is not None:
            row, _ = self.rows.row(self.stream, index)
            if row['dataset']+'/'+row['scene'] not in self.heldout_scenes:
                raise ValueError('Heldout row is outside the pinned heldout scene division')
        return self.rows.get(self.stream, index)

    def close(self):
        self.rows.close()


class PoseRows:
    """One canonical RGB row per bank scene, with the bank's original target masks."""
    def __init__(self, held, cfg, processor):
        from student_pilot.all_frame_bank import read_bank
        from student_pilot.compact_label_bank import frame_set_sha256
        from student_pilot.p3_provenance import load, pinned
        self.bank = bank = read_bank(str(pinned(held['bank'])))
        keys = list(zip(bank['dataset_tokens'].tolist(), bank['scene_tokens'].tolist()))
        training = {tuple(k) for k in load(pinned(held['training_scenes']))['scenes']}
        if len(keys) != len(set(keys)) or set(keys) & training:
            raise ValueError('Pose bank overlaps training scenes or repeats scenes')
        lookup = {k: i for i, k in enumerate(keys)}
        chosen = {}
        for pin in load(pinned(held['rows_inventory']))['files']:
            path = pinned(pin)
            opener = gzip.open if path.suffix == '.gz' else open
            with opener(path, 'rt') as handle:
                for line in handle:
                    row = json.loads(line)
                    key = (row['dataset'], row['scene'])
                    if key not in lookup:
                        raise ValueError('Unexpected heldout RGB scene')
                    i = lookup[key]
                    if frame_set_sha256(row['student_input']['frame_indices']) != str(bank['frame_set_sha256'][i]):
                        raise ValueError('Heldout RGB frame set differs')
                    if key in chosen and chosen[key]['student_input']['frames'] != row['student_input']['frames']:
                        raise ValueError('Conflicting heldout RGB')
                    if key not in chosen or str(row['qid']) < str(chosen[key]['qid']):
                        chosen[key] = row
        if set(chosen) != set(keys):
            raise ValueError('Missing heldout pose RGB scene')
        self.entries = [(lookup[k], chosen[k]) for k in sorted(chosen)]
        self.count = len(self.entries)
        self.cfg, self.processor = cfg, processor

    def get(self, index):
        from student_pilot import carrier_c1_data as data
        i, row = self.entries[index]
        b = self.bank
        target = {key: b[key][i].tolist() for key in ('camera', 'camera_mask', 'gravity', 'gravity_mask', 'trajectory_scale')}
        target['point_depth'] = dict(uv=b['point_depth_uv'][i].tolist(), depth=b['point_depth_gt'][i].tolist(),
                                     mask=b['point_depth_mask'][i].tolist())
        layout, gap = data.layout_settings(self.cfg)
        return data.encode(self.processor, row, target, 'pose', self.cfg['carrier_placement'], 'final', layout, gap)

    def close(self):
        pass


def populations(request, prep, processor):
    from student_pilot.p3_provenance import load, pinned
    cfg = request['cfg']
    receipts = {name: load(pinned(pin)) for name, pin in cfg['streams'].items()}
    pins = heldout_pins(cfg, prep, request['heldout_streams'], receipts)
    held, missing = {}, {}
    readout = cfg.get('readout') or prep.get('readout')
    if readout and all(readout.get(k) for k in ('bank', 'rows_inventory', 'training_scenes')):
        held['pose'] = PoseRows(readout, cfg, processor)
    else:
        missing['pose'] = 'No pinned readout bank, rows inventory and training scenes in cfg/preparation'
    for stream in STREAMS[1:]:
        if stream in pins:
            held[stream] = DatabaseRows(pins[stream], stream, prep, processor, receipts[stream])
        else:
            missing[stream] = 'No heldout receipt pinned in cfg, preparation or training receipt'
    return held, missing, dict(pose=readout, **pins)


def make_plan(request, counts, held, missing):
    plan, limits = [], {}
    for stream in STREAMS:
        n = min(request['rows_per_stream'], counts[stream], held[stream].count) if stream in held else min(request['rows_per_stream'], counts[stream])
        limits[stream] = dict(requested=request['rows_per_stream'], selected=n,
            reason='Population smaller than requested; no replacement' if n < request['rows_per_stream'] else None,
            heldout_missing=missing.get(stream))
        for split, count in [('training', counts[stream]), *([('heldout', held[stream].count)] if stream in held else [])]:
            for index in sample_indices(count, n, request['seed'], stream, split):
                plan.append(dict(key=f'{stream}:{split}:{index}', stream=stream, split=split, index=index))
    return plan, limits


def run_worker(request, rank, world_size, device=None):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('evalpath/heldout_loss.py:run_worker')
    import torch
    from .run import binding_for, read_journal, append_record, write_json
    validate_request(request)
    device = torch.device(device or f'cuda:{rank}')
    if device.type != 'cuda' or world_size != 4 or not 0 <= rank < world_size:
        raise ValueError('Four GPU loss workers required')
    torch.cuda.set_device(device)
    install_paths(request)
    verify_source(request)
    from student_pilot import carrier_c1_run as trainer
    cfg = request['cfg']
    prep, manifest = trainer.prepared(cfg, admission=True)
    # Authenticate against the pinned base manifest while using the kit's staged snapshot.
    manifest = {**manifest, 'root': request['snapshot']}
    processor = trainer.processor_for_receipt(manifest, prep)
    training = trainer.Rows(prep, processor)
    held = {}
    output = Path(request['output']); output.mkdir(parents=True, exist_ok=True)
    with (output/f'worker-{rank}.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            held, missing, sources = populations(request, prep, processor)
            plan, limits = make_plan(request, training.counts, held, missing)
            binding = binding_for(request, world_size)
            journal = output/f'loss-{rank}.jsonl'
            records = read_journal(journal, binding)
            assigned = plan[rank::world_size]
            if not set(records) <= {r['key'] for r in assigned}:
                raise ValueError('Loss journal has foreign rows')
            model = trainer.load_model(manifest, prep, processor)
            artifact = trainer.load_artifact(model, request['artifact'])
            if (artifact['base_identity'] != cfg['base_identity'] or artifact['config_sha256'] != trainer.identity(cfg)
                    or type(artifact.get('step')) is not int
                    or cfg.get('milestones') and artifact['step'] not in cfg['milestones']):
                raise ValueError('Artifact/config identity or step differs')
            model.to(device).eval().requires_grad_(False)
            for task in assigned:
                if records.get(task['key'], {}).get('status') == 'complete':
                    continue
                rows = training if task['split'] == 'training' else held[task['stream']]
                batch, targets, _ = rows.get(task['stream'], task['index']) if rows is training else rows.get(task['index'])
                # No trainer fetch/retry substitution: a failed fixed row fails coverage.
                result = measure(model, trainer.move(batch, device), trainer.move(targets, device), task['stream'])
                append_record(journal, dict(binding=binding, status='complete', **task, **result))
            write_json(output/f'loss-plan-{rank}-{request["attempt"]}.json', dict(binding=binding,
                step=artifact['step'], plan=plan, limits=limits, sources=sources, missing=missing))
        finally:
            training.close()
            for rows in held.values():
                rows.close()


def merge(request, world_size):
    from .run import binding_for, read_journal, write_json
    validate_request(request)
    binding = binding_for(request, world_size)
    output = Path(request['output'])
    plans, records, errors = [], {}, []
    for rank in range(world_size):
        path = output/f'loss-plan-{rank}-{request["attempt"]}.json'
        if not path.exists():
            errors.append(f'Worker {rank} did not complete'); continue
        plan = json.loads(path.read_text())
        if plan['binding'] != binding or plans and plan != plans[0]:
            raise ValueError('Worker loss plans differ')
        plans.append(plan)
        rows = read_journal(output/f'loss-{rank}.jsonl', binding)
        allowed = {r['key'] for r in plan['plan'][rank::world_size]}
        if not set(rows) <= allowed:
            raise ValueError('Loss journal shard differs')
        records.update(rows)
    first = plans[0] if plans else dict(plan=[], missing={}, sources={}, limits={}, step=None)
    expected = {r['key'] for r in first['plan']}
    complete = {k for k, r in records.items() if r.get('status') == 'complete'}
    coverage = not errors and world_size == 4 and complete == expected and bool(expected)
    streams = {}
    for stream in STREAMS:
        cells = {split: stats([r for r in records.values() if r['stream'] == stream and r['split'] == split
                              and r.get('status') == 'complete']) for split in ('training', 'heldout')}
        a, b = cells['heldout']['mean'], cells['training']['mean']
        streams[stream] = dict(**cells, overfit_ratio=a/b if a is not None and b not in (None, 0.) else None,
            status='missing' if stream in first['missing'] else 'complete' if coverage else 'incomplete',
            reason=first['missing'].get(stream), selection=first['limits'].get(stream),
            metric='pose component row loss' if stream == 'pose' else SEGMENT.get(stream, 'supervised routing')+' token CE')
    report = dict(schema='heldout-loss-v1', artifact=request['artifact'], step=first['step'],
        trainer_commit=COMMIT, cfg_raw_sha256=request['cfg_raw_sha256'], seed=request['seed'],
        rows_per_stream=request['rows_per_stream'], streams=streams, sources=first['sources'],
        selection=first['plan'], coverage_complete=coverage, errors=errors,
        numbers_status='eligible' if coverage else 'do not count',
        aggregation='mean/std across row losses (population std); token_mean weights CE by supervised tokens; '
                    'n counts selected rows, n_scored excludes rows without requested tokens; ratio=heldout/training')
    # Atomic replacement supports a resumed allocation while preserving every attempt report.
    write_json(output/f'heldout_loss-{request["attempt"]}.json', report)
    temp = output/f'heldout_loss-{request["attempt"]}.part'
    with temp.open('x') as handle:
        json.dump(report, handle, indent=2, sort_keys=True, allow_nan=False); handle.write('\n')
    temp.replace(output/'heldout_loss.json')
    return report
