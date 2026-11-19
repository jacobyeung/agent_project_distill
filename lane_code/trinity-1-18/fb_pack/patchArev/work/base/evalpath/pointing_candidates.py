"""Pinned full-weight candidates for the fixed pointing protocol."""
import fcntl
import json
from pathlib import Path
import re
import time

from .items import pinned, sha256

FULL_FT_SHA256 = '6e65d17fa82f6330c5d7cbf935d3f4f994f1b28dba9e8c02c889c9bd57cd7c89'


def validate_pin(pin):
    if (not isinstance(pin, dict) or set(pin) != {'path', 'sha256'} or
            not isinstance(pin['path'], str) or not Path(pin['path']).is_absolute() or
            not isinstance(pin['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', pin['sha256'])):
        raise ValueError('Require absolute path@sha256')


def model_specs(request):
    if request['kind'] == 'base':
        if 'candidates' in request or 'with_base' in request:
            raise ValueError('Candidate fields require kind candidate')
        return [dict(name='base', artifact=None)]
    specs = request.get('candidates')
    if (request['kind'] != 'candidate' or not isinstance(specs, list) or not specs or
            type(request.get('with_base')) is not bool):
        raise ValueError('Require candidates and a boolean with_base')
    seen = {'base'}
    for spec in specs:
        if (not isinstance(spec, dict) or set(spec) != {'name', 'artifact'} or
                not isinstance(spec['name'], str) or not re.fullmatch('[A-Za-z0-9_-]{1,80}', spec['name']) or
                spec['name'] in seen):
            raise ValueError('Candidate names must be unique safe labels; base is reserved')
        seen.add(spec['name'])
        validate_pin(spec['artifact'])
    return ([dict(name='base', artifact=None)] if request['with_base'] else []) + specs


def parse_candidates(values):
    specs = []
    for value in values:
        try:
            name, text = value.split('=', 1)
            path, sha = text.rsplit('@', 1)
        except ValueError as exc:
            raise ValueError('Require NAME=ARTIFACT_JSON_ABS_PATH@SHA256') from exc
        specs.append(dict(name=name, artifact=dict(path=path, sha256=sha)))
    model_specs(dict(kind='candidate', candidates=specs, with_base=False))
    return specs


def load_candidate(model, artifact_pin):
    """Use the authenticated trainer loader; heads and carrier modules are unused."""
    import torch
    from student_pilot import full_ft
    if sha256(Path(full_ft.__file__)) != FULL_FT_SHA256:
        raise ValueError('Full-weight loader differs from pinned C1 source')
    validate_pin(artifact_pin)
    artifact = json.loads(pinned(artifact_pin).read_text())
    if artifact.get('schema') != 'carrier-c1-artifact-v1':
        raise ValueError('Require a C1 milestone/soup artifact')
    pin = artifact['full_weights']
    validate_pin(pin)
    manifest_path = pinned(pin)
    if manifest_path.name != full_ft.EXPORT_MANIFEST:
        raise ValueError('Require the full_weights.json export manifest')
    manifest = json.loads(manifest_path.read_text())
    if (manifest.get('schema') != 'full-ft-export-v1' or
            Path(manifest['index']['name']).name != manifest['index']['name']):
        raise ValueError('Invalid full-weight manifest/index')
    # HF retains GDN A_log/dt_bias in FP32. The C1 export rounds them to BF16.
    # Convert the live parameters exactly as carrier_c1_run.load_artifact does.
    for _, parameter in full_ft.base_parameters(model):
        parameter.data = parameter.data.to(torch.bfloat16)
    # read_export verifies the index and every shard SHA before copying tensors.
    report = full_ft.load_export(model, manifest_path.parent)
    return dict(artifact=artifact_pin, full_weights=pin, load=report,
                full_ft_sha256=FULL_FT_SHA256, step=artifact.get('step'))


def record_key(task, condition, model):
    from .pointing_markers import record_key as base_key
    return model+':'+base_key(task, condition)


def expected_keys(tasks, specs):
    from .pointing_markers import CONDITIONS
    return {record_key(t, c, s['name']) for t in tasks for c in CONDITIONS for s in specs}


def summarize(records, tasks, specs, parities):
    from . import pointing_markers as pm
    models = {}
    for spec in specs:
        name = spec['name']
        subset = {pm.record_key(r, r['condition']): r for r in records.values() if r['model'] == name}
        models[name] = pm.summarize(subset, tasks, parities.get(name, False))
    expected = expected_keys(tasks, specs)
    complete = {k for k, r in records.items() if r.get('status') == 'complete'}
    coverage = complete == expected and set(records) <= expected
    parity = all(parities.get(s['name'], False) for s in specs)
    return dict(expected_count=len(expected), completed=len(complete), coverage_complete=coverage,
                parity_pass=parity, models=models,
                numbers_status='eligible' if coverage and parity else 'do not count',
                scoring_protocol='Trinity score_pointing_video.score_rows per model/condition, variant A')


def check_records(records, tasks, specs):
    from .pointing_markers import CONDITIONS
    names = {s['name'] for s in specs}
    if not set(records) <= expected_keys(tasks, specs):
        raise ValueError('Journal has items outside model/shard cells')
    for key, row in records.items():
        if (row.get('model') not in names or row.get('condition') not in CONDITIONS or
                key != record_key(row, row['condition'], row['model'])):
            raise ValueError('Journal model/condition/key differs')


def run_worker(request, rank, world_size, device=None):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('evalpath/pointing_candidates.py:run_worker')
    import torch
    from student_pilot.carrier_c1_run import move
    from . import pointing_markers as pm
    from .runtime import load_model
    from .run import append_record, binding_for, read_journal, shard_items, write_json
    pm.validate_request(request)
    device = device or f'cuda:{rank}'
    if torch.device(device).type != 'cuda':
        raise ValueError('GPU worker required')
    specs = model_specs(request)
    output = Path(request['output'])
    output.mkdir(parents=True, exist_ok=True)
    binding = binding_for(request, world_size)
    with (output/f'worker-{rank}.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        tasks = pm.load_tasks(request)
        assigned = shard_items(tasks, rank, world_size)
        journal = output/f'items-{rank}.jsonl'
        records = read_journal(journal, binding)
        check_records(records, assigned, specs)
        parities, receipts = {}, {}
        for spec in specs:
            name = spec['name']
            # Reload base for every candidate so no previous export can leak into it.
            model, processor, info = load_model('base', request['cfg'], snapshot=request['snapshot'], device=device)
            if spec['artifact'] is not None:
                info = {**info, 'kind': 'candidate', **load_candidate(model, spec['artifact'])}
            parity = dict(binding=binding, rank=rank, attempt=request['attempt'], model=name,
                          model_info=info, items=[], **{'pass': False})
            try:
                for task in tasks[:5]:
                    parity['items'].append(pm.parity_item(processor, task, request['frame_cache']))
                parity['pass'] = len(parity['items']) == 5
            except Exception as exc:
                parity['error'] = f'{type(exc).__name__}: {exc}'
            path = output/f"parity-{rank}-{name}-{request['attempt']}.json"
            write_json(path, parity)
            parities[name], receipts[name] = parity['pass'], str(path)
            for task in assigned:
                pending = [c for c in pm.CONDITIONS if records.get(record_key(task, c, name), {}).get('status') != 'complete']
                if not pending:
                    continue
                started = time.perf_counter()
                try:
                    row, receipt = pm.trainer_row(task, request['frame_cache'])
                    batch, audit, trainer_ids = pm.encode_prompt(processor, row)
                    pair = pm.marker_pair(processor, batch)
                    pm.group_evidence(processor.tokenizer, pair)
                    error = None
                except Exception as exc:
                    error = f'{type(exc).__name__}: {exc}'
                for condition in pending:
                    record = {k: task[k] for k in ('benchmark', 'example_id', 'membership_id', 'variant',
                                                   'scene', 'obj', 'frame', 'source_index')}
                    record.update(item_id=task['membership_id'], condition=condition, model=name,
                        key=record_key(task, condition, name), binding=binding, rank=rank,
                        attempt=request['attempt'], status='error', raw_generation='', max_new_tokens=64)
                    try:
                        if error:
                            raise ValueError(error)
                        record.update(pm.native_generate(model, processor, move(pair[condition], device)),
                            status='complete', processed_height_width=audit['processed_height_width'],
                            trainer_prompt_ids_sha256=pm.digest(trainer_ids),
                            anchor_pixel_sha256=receipt['anchor_pixel_sha256'],
                            duplicate_pixel_sha256=receipt['duplicate_pixel_sha256'], num_frames=64, num_viewpoints=32)
                    except Exception as exc:
                        record['error'] = f'{type(exc).__name__}: {exc}'
                    record['elapsed_s'] = time.perf_counter()-started
                    append_record(journal, record)
                    records[record['key']] = record
            del model, processor
        summary = summarize(records, assigned, specs, parities)
        summary.update(binding=binding, rank=rank, parity_paths=receipts)
        write_json(output/f"summary-{rank}-{request['attempt']}.json", summary)
        return summary


def merge(request, world_size):
    from . import pointing_markers as pm
    from .run import binding_for, read_journal, shard_items, write_json
    pm.validate_request(request)
    specs = model_specs(request)
    tasks = pm.load_tasks(request)
    binding = binding_for(request, world_size)
    output, records = Path(request['output']), {}
    parities = {s['name']: [] for s in specs}
    for rank in range(world_size):
        shard = read_journal(output/f'items-{rank}.jsonl', binding)
        check_records(shard, shard_items(tasks, rank, world_size), specs)
        if set(shard) & set(records):
            raise ValueError('Duplicate model/shard cells')
        records.update(shard)
        for spec in specs:
            name = spec['name']
            path = output/f"parity-{rank}-{name}-{request['attempt']}.json"
            parity = json.loads(path.read_text()) if path.exists() else {'pass': False, 'missing': str(path)}
            if path.exists():
                if (parity.get('binding') != binding or parity.get('rank') != rank or
                        parity.get('attempt') != request['attempt'] or parity.get('model') != name):
                    raise ValueError('Parity belongs to another model/run/shard')
                if parity.get('pass') and [i['example_id'] for i in parity.get('items', [])] != [t['example_id'] for t in tasks[:5]]:
                    raise ValueError('Parity items differ from fixed five')
            parities[name].append(parity)
    summary = summarize(records, tasks, specs, {n: all(p['pass'] for p in ps) for n, ps in parities.items()})
    summary.update(binding=binding, parities=parities, protocol_request=request)
    write_json(output/f"summary-{request['attempt']}.json", summary)
    for condition in [None, *pm.CONDITIONS]:
        name = 'per-item' if condition is None else condition
        with (output/f"{name}-{request['attempt']}.jsonl").open('x') as stream:
            for _, record in sorted(records.items()):
                if condition is None or record['condition'] == condition:
                    stream.write(json.dumps(record, sort_keys=True, allow_nan=False)+'\n')
    return summary
