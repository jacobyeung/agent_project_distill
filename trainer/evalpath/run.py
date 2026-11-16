"""One GPU worker per item shard; resume journals and official aggregation."""
import argparse
from collections import Counter, defaultdict
import fcntl
import json
import os
from pathlib import Path
import re
import time

from . import official
from .items import assert_prompt_equal, digest, load_items, trainer_row, sha256


def key(task):
    return task['benchmark'] + ':' + task['example_id']


def shard_items(tasks, rank, world_size):
    if not 0 <= rank < world_size:
        raise ValueError('Invalid shard rank/world size')
    return [t for t in tasks if int(digest(key(t)), 16) % world_size == rank]


def read_journal(path, binding):
    """Latest record wins; an interrupted JSON line has no terminal semantics."""
    latest = {}
    if not Path(path).exists():
        return latest
    with open(path) as f:
        for line in f:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue  # append-only recovery; incomplete writes never count
            if record.get('binding') != binding:
                raise ValueError('Resume journal belongs to another model/data/protocol')
            latest[record['key']] = record
    return latest


def pending_items(tasks, records):
    return [t for t in tasks if records.get(key(t), {}).get('status') != 'complete']


def append_record(path, record, durable=False):
    # A leading newline isolates a partial last write without deleting its bytes.
    with Path(path).open('a') as f:
        f.write('\n' + json.dumps(record, sort_keys=True, allow_nan=False) + '\n')
        f.flush()
        if durable:
            os.fsync(f.fileno())


def write_json(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, sort_keys=True, indent=2, allow_nan=False)
        f.write('\n')


def worker_error(request, rank, exc):
    """Retain a durable diagnostic without retaining question text or host paths."""
    from .worker_errors import error_row
    output = Path(request['output'])
    output.mkdir(parents=True, exist_ok=True)
    append_record(output / f"parity-items-{rank}-{request['attempt']}.jsonl",
                  error_row(rank, exc), durable=True)


def score_item(task, decode):
    response, branch = official.extract_q35_final_answer(decode['text'], enable_thinking=True)
    fuzzy = official.official_fuzzy_matching(response)
    answer_type = official.infer_answer_type(task)
    if answer_type == 'multiple_choice':
        score = official.official_exact_match(fuzzy, str(task['ground_truth']).strip())
        parse_failed = not fuzzy
    else:
        value = official.official_to_float(fuzzy)
        score = official.official_mra(value, official.official_to_float(str(task['ground_truth']).strip()))
        parse_failed = value is None
    # The generation prompt already contains <think>\n. Count only its continuation.
    close = list(re.finditer(r'</think\s*>', decode['text'], re.IGNORECASE))
    think = decode['text'][:close[-1].start()] if close else decode['text']
    think = re.sub(r'^<think\s*>\s*', '', think, flags=re.IGNORECASE)
    cap_hit = decode['finish'] in ('max_new_tokens', 'context_exhaustion')
    return dict(response_text=response, extract_branch=branch, official_fuzzy_pred=fuzzy,
                score=score, parse_failed=parse_failed, hit_token_cap=cap_hit,
                empty_think=bool(close) and not think.strip(), think_chars=len(think),
                _think_text=think)


def aggregate(records, tasks, parity_pass):
    """Official fuzzy EM/MRA primary; strict cell parsing remains a named diagnostic."""
    summary = dict(schema='evalpath-summary-v1', expected_count=len(tasks), terminal_count=len(records),
                   completed=sum(r.get('status') == 'complete' for r in records),
                   errors=sum(r.get('status') != 'complete' for r in records), parity_pass=parity_pass)
    summary['coverage_complete'] = ({r['key'] for r in records} == {key(t) for t in tasks}
                                    and summary['completed'] == len(tasks))
    summary['numbers_status'] = 'eligible' if parity_pass and summary['coverage_complete'] else 'do not count'
    if any(record.get('development_tool_mode_flag') for record in records):
        summary['numbers_status'] = 'development prompt override; not a headline evaluation'
    summary['scoring_protocol'] = 'official_full fuzzy MCA exact match / NA MRA; task macro aggregation'
    summary['cap_hits'] = sum(r.get('hit_token_cap', False) for r in records)
    summary['parse_failures'] = sum(r.get('parse_failed', True) for r in records)
    summary['empty_thinks'] = sum(r.get('empty_think', False) for r in records)
    summary['calls'] = sum(len(r.get('decode', {}).get('calls', [])) for r in records)
    summary['call_errors'] = sum(r.get('decode', {}).get('errors', 0) for r in records)
    summary['generated_tokens'] = sum(r.get('output_tokens', 0) for r in records)
    summary['sampled_tokens'] = sum(r.get('sampled_tokens', 0) for r in records)
    summary['finish_reasons'] = dict(Counter(r.get('finish_reason', 'item_error') for r in records))
    lengths = [r['think_tokens'] for r in records if 'think_tokens' in r]
    summary['think_length_tokens'] = dict(count=len(lengths), total=sum(lengths),
        mean=sum(lengths) / max(len(lengths), 1), maximum=max(lengths, default=0))
    by_type = defaultdict(list)
    for record in records:
        by_type[(record['benchmark'], record['question_type'])].append(record.get('score', 0.))
    summary['per_type'] = {b + ':' + t: {'count': len(v), 'score': sum(v) / len(v)}
                           for (b, t), v in sorted(by_type.items())}
    summary['benchmarks'] = {}
    for benchmark in sorted({t['benchmark'] for t in tasks}):
        rows = [r for r in records if r['benchmark'] == benchmark]
        if benchmark in ('vsi500', 'official5130', 'routed_dev'):
            official_summary = official.score_official_vsibench(rows, expected_count=0)
            official_summary.pop('scored_records')
            if benchmark == 'routed_dev':
                official_summary.update(benchmark='routed_dev', metric='official EM/MRA on three development types')
            summary['benchmarks'][benchmark] = official_summary
        else:
            # official_full only recognizes VSI names; the official cell scorer
            # applies the same EM/MRA and the five VSTI primary task groups.
            cell, _ = official.score_our_cell(rows, 'evalpath', 'vstibench_repr450_v3', 0)
            summary['benchmarks'][benchmark] = dict(overall_score=cell['fuzzy_primary_score'],
                per_task_scores=cell['fuzzy_primary_task_scores'],
                strict_cell_score_diagnostic=cell['primary_score'],
                metric='vstibench-official-5task-v1; fuzzy official_full extraction')
    if records and any('routed' in r for r in records):
        from .routed_types import cells
        summary['routed_types'] = cells(records)
    return summary


def load_request_items(request):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('evalpath/run.py:load_request_items')
    tasks = [task for spec in request['datasets'] for task in load_items(spec, request['roots'])]
    if request.get('preset') == 'routed_types':
        from .routed_types import select
        tasks = select(tasks)
    elif request.get('preset') == 'parity' and request.get('routed_protocol'):
        return []
    if len({key(t) for t in tasks}) != len(tasks):
        raise ValueError('Repeated benchmark/item in request')
    return tasks


def binding_for(request, world_size):
    package = Path(__file__).parent
    return digest({'request': {k: v for k, v in request.items() if k not in ('attempt', 'frame_cache')},
                   'world_size': world_size, 'sources': json.loads(
                       Path(__file__).with_name('SOURCE_PINS.json').read_text()),
                   'evaluator_sources': {p.name: sha256(p) for p in sorted(package.glob('*.py'))}})


def validate_request(request):
    if request.get('preset') == 'vqa_direct':
        from .vqa_direct import validate_request as validate_direct
        return validate_direct(request)
    if 'pose_override' in request:
        from .pose_override import validate_spec
        if request['kind'] != 'routed' or not request.get('routed_protocol') or request.get('preset') == 'heldout_loss':
            raise ValueError('Pose override requires routed generation')
        validate_spec(request['pose_override'])
    if request.get('preset') == 'heldout_loss':
        from .heldout_loss import validate_request as validate_loss
        return validate_loss(request)
    if request.get('preset') == 'pointing_markers':
        from .pointing_markers import validate_request as validate_pointing
        return validate_pointing(request)
    if request['kind'] not in ('base', 'routed'):
        raise ValueError('Unknown model kind')
    if request.get('tool_mode_flag'):
        from student_pilot.carrier_c1_routing import validate_tool_mode_flag
        from student_pilot.p3_provenance import pinned, load
        validate_tool_mode_flag(request['tool_mode_flag'])
        table = load(pinned(request['route_table']))
        if not isinstance(table.get('route'), list):
            raise ValueError('Development prompt override requires a pinned route table')
    if request.get('routed_protocol'):
        from .pointing_candidates import validate_pin
        if (request['routed_protocol'] != 'routed-types-v1' or request['kind'] != 'routed'
                or request['max_new_tokens'] != 16384 or request.get('do_sample') is not False
                or request.get('enable_thinking') is not True or request['cfg'].get('training_mode') != 'final'):
            raise ValueError('Routed protocol differs')
        validate_pin(request['artifact'])
    if request.get('preset') == 'routed_dev':
        from .routed_dev import validate_request as validate_dev
        validate_dev(request)
    if request.get('max_new_tokens') is not None and (
            type(request['max_new_tokens']) is not int or request['max_new_tokens'] < 16384):
        raise ValueError('No explicit cap below 16384')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', request['attempt']):
        raise ValueError('attempt must be a fresh filename-safe job identifier')
    if request['cfg'].get('frame_layout', 'spread') not in ('spread', 'duplicate'):
        raise ValueError('This evaluator supports spread or duplicate layouts')


def run_worker(request, rank, world_size, device=None):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('evalpath/run.py:run_worker')
    try:
        return _run_worker(request, rank, world_size, device)
    except BaseException as exc:
        worker_error(request, rank, exc)
        raise


def _run_worker(request, rank, world_size, device=None):
    """b/v.py calls this in each GPU process after staging and authorization."""
    if request.get('preset') == 'vqa_direct':
        from .vqa_direct import run_worker as run_direct
        return run_direct(request, rank, world_size, device)
    if request.get('preset') == 'heldout_loss':
        from .heldout_loss import run_worker as run_loss
        return run_loss(request, rank, world_size, device)
    if request.get('preset') == 'pointing_markers':
        from .pointing_markers import run_worker as run_pointing
        return run_pointing(request, rank, world_size, device)
    import torch
    if request.get('routed_trainer'):
        from .heldout_loss import install_paths
        from .routed_types import verify_source
        install_paths(request)
        verify_source(request)
    from student_pilot.carrier_c1_run import move
    from .runtime import load_model, prompt_batch, generate
    from .parity import run_suite
    validate_request(request)
    if 'pose_override' in request:
        from .pose_override import load_values, Responder
        override_scenes = load_values(request['pose_override'])
    from student_pilot import rehearsal
    cpu_rehearsal = rehearsal.enabled()
    device = device or ('cpu' if cpu_rehearsal else f'cuda:{rank}')
    if cpu_rehearsal and torch.device(device).type != 'cpu':
        raise ValueError('CPU rehearsal refuses an accelerator worker')
    if torch.device(device).type != 'cuda' and not cpu_rehearsal:
        raise ValueError('GPU worker required')
    if torch.device(device).type == 'cuda':
        torch.cuda.set_device(device)
    output = Path(request['output'])
    output.mkdir(parents=True, exist_ok=True)
    binding = binding_for(request, world_size)
    # Prevent two workers from generating the same shard concurrently.
    lock = (output / f'worker-{rank}.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        dev = request.get('preset') == 'routed_dev'
        def progress(event):
            append_record(output / f"parity-items-{rank}-{request['attempt']}.jsonl",
                dict(event, binding=binding, rank=rank, attempt=request['attempt']), durable=True)
        if dev:
            progress(dict(phase='worker_started'))
        tasks = load_request_items(request)
        assigned = shard_items(tasks, rank, world_size)
        if dev:
            progress(dict(phase='tasks_loaded', count=len(tasks), assigned=len(assigned)))
        journal = output / f'items-{rank}.jsonl'
        latest = read_journal(journal, binding)
        allowed = {key(t) for t in assigned}
        if not set(latest) <= allowed:
            raise ValueError('Journal contains items outside its shard')
        # The trainer builds FP32 host masters and loads initialization exports
        # before replacing them with BF16 milestone weights. Limit that temporary
        # host-memory peak to one worker; release after the model reaches its GPU.
        with (output / 'model-load.lock').open('a') as load_lock:
            if dev:
                progress(dict(phase='model_load_wait'))
            fcntl.flock(load_lock, fcntl.LOCK_EX)
            if dev:
                progress(dict(phase='model_load_started'))
            model, processor, model_info = load_model(request['kind'], request['cfg'],
                artifact_pin=request.get('artifact'), snapshot=request.get('snapshot'), device=device,
                selected_trainer=request.get('routed_trainer'),
                **(dict(on_stage=progress) if dev else {}))
        if dev:
            progress(dict(phase='model_loaded'))
        # Every invocation runs fresh parity, including an otherwise finished resume.
        try:
            if dev:
                from .routed_dev import parity_tasks
                fixed = parity_tasks(tasks)
            elif request.get('routed_protocol'):
                from .routed_types import parity_tasks
                spec = request.get('parity_official') or next(d for d in request['datasets'] if d['benchmark'] == 'official5130')
                fixed = parity_tasks(load_items(spec, request['roots']))
            else:
                vsi = [t for t in tasks if t['benchmark'] == 'vsi500']
                if not vsi and request.get('parity_vsi'):
                    vsi = load_items(request['parity_vsi'], request['roots'])
                fixed = sorted(vsi, key=lambda t: t['example_id'])[:5]
            rows = [trainer_row(task, request['frame_cache']) for task in fixed]
            for row in rows:
                assert_prompt_equal(processor, row)
            parity = run_suite(model, processor, request['cfg'], request['kind'], rows,
                routing_pin=request.get('routing_heldout'), max_new_tokens=request.get('max_new_tokens'),
                routing_roots=request['roots'], strict=bool(request.get('routed_protocol')),
                parity_tasks=fixed, **(dict(dev=True, on_item=progress) if dev else {}))
        except Exception as exc:
            if dev:
                raise
            parity = {'pass': False, 'numbers_status': 'do not count',
                      'error': f'{type(exc).__name__}: {exc}'}
        parity.update(binding=binding, rank=rank, attempt=request['attempt'], model=model_info)
        parity_path = output / f"parity-{rank}-{request['attempt']}.json"
        write_json(parity_path, parity)
        for task in pending_items(assigned, latest):
            started = time.perf_counter()
            record = {k: task[k] for k in ('example_id', 'benchmark', 'dataset', 'scene_name',
                                          'question_type', 'ground_truth', 'options')}
            record.update(key=key(task), binding=binding, rank=rank, attempt=request['attempt'],
                          status='error', response_text='', extract_branch='item_error', score=0.,
                          parse_failed=True, max_new_tokens=request.get('max_new_tokens'))
            if dev:
                record.update(output_tokens=0, sampled_tokens=0, official_fuzzy_pred='',
                              head_call_count=0, routed_calls=[], finish_reason='item_error')
            if request.get('routed_protocol'):
                record.update(routed=False, head_openers=[], frames_used=[], routed_frame_count=0,
                              direction_program='no_head_call', item_identity=digest({k:task[k] for k in
                              ('example_id','dataset','scene_name','question_type','question','options','ground_truth')}))
            responder = None
            if 'pose_override' in request:
                responder = Responder(override_scenes, task, request['pose_override']['types'])
                record.update(responder.fields())
            try:
                row = trainer_row(task, request['frame_cache'])
                if request.get('tool_mode_flag'):
                    from student_pilot.p3_provenance import load, pinned
                    from student_pilot.carrier_c1_routing import tool_mode
                    types = load(pinned(request['route_table']))['route']
                    if task['question_type'] in types:
                        row = tool_mode({**row, 'routing': dict(category='route')}, request['tool_mode_flag'])
                    record['development_tool_mode_flag'] = request['tool_mode_flag']
                if request.get('routed_protocol'):
                    si = row['student_input']
                    record['frame_identity'] = digest(dict(frame_indices=si['frame_indices'], fps=si['fps'],
                        total_num_frames=si['total_num_frames'], frames=[p['sha256'] for p in si['frames']]))
                assert_prompt_equal(processor, row)
                batch = move(prompt_batch(processor, row, request['cfg'], request['kind']), device)
                grounding = {}
                if request['kind'] == 'routed' and getattr(model, 'trace_program_version', None) == '3.14':
                    from student_pilot.s1_grounding import build_backend
                    backend = build_backend({**row, 'question_type': task['question_type']}, batch,
                        request['artifact'], output / 'grounding' / digest(key(task)), request.get('grounding'))
                    grounding = dict(ground_backend=backend, mask_source='mdg')
                decoded = generate(model, processor, batch, request['kind'], request.get('max_new_tokens'),
                                   **grounding,
                                   **(dict(pose_override=responder) if responder is not None else {}))
                if request.get('routed_protocol'):
                    from .routed_types import route_fields
                    record.update(route_fields(decoded))
                scored = score_item(task, decoded)
                think = scored.pop('_think_text')
                record.update(scored, status='complete', decode=decoded,
                    think_tokens=len(processor.tokenizer.encode(think, add_special_tokens=False)),
                    num_frames=64 if request['cfg'].get('frame_layout') == 'duplicate' else 32,
                    input_tokens=decoded['prompt_tokens'], output_tokens=decoded['generated_tokens'],
                    sampled_tokens=decoded['generated_tokens'] - sum(c['forced_tokens'] for c in decoded['calls']),
                    finish_reason=decoded['finish'], frame_receipt=row['student_input'])
            except Exception as exc:
                if dev:
                    raise
                record['error'] = f'{type(exc).__name__}: {exc}'
            record['elapsed_s'] = time.perf_counter() - started
            if responder is not None:
                record.update(responder.fields())
            append_record(journal, record, durable=dev)
            latest[record['key']] = record
        summary = aggregate(list(latest.values()), assigned, parity['pass'])
        summary.update(binding=binding, rank=rank, parity_path=str(parity_path), model=model_info)
        path = output / f"summary-{rank}-{request['attempt']}.json"
        write_json(path, summary)
        return dict(summary=str(path), parity=str(parity_path), journal=str(journal))
    finally:
        lock.close()


def merge(request, world_size):
    """Call after all workers exit; missing/failed parity always invalidates scores."""
    if request.get('preset') == 'vqa_direct':
        from .vqa_direct import merge as merge_direct
        return merge_direct(request, world_size)
    if request.get('preset') == 'heldout_loss':
        from .heldout_loss import merge as merge_loss
        return merge_loss(request, world_size)
    if request.get('preset') == 'pointing_markers':
        from .pointing_markers import merge as merge_pointing
        return merge_pointing(request, world_size)
    validate_request(request)
    tasks = load_request_items(request)
    binding = binding_for(request, world_size)
    output, latest, parities = Path(request['output']), {}, []
    for rank in range(world_size):
        records = read_journal(output / f'items-{rank}.jsonl', binding)
        allowed = {key(t) for t in shard_items(tasks, rank, world_size)}
        if not set(records) <= allowed or set(records) & set(latest):
            raise ValueError('Merged journals have duplicate or misplaced items')
        latest.update(records)
        path = output / f"parity-{rank}-{request['attempt']}.json"
        parity = json.loads(path.read_text()) if path.exists() else {'pass': False, 'missing': str(path)}
        if path.exists() and (parity.get('binding') != binding or parity.get('rank') != rank):
            raise ValueError('Parity report belongs to another run/shard')
        parities.append(parity)
    summary = aggregate(list(latest.values()), tasks, all(p['pass'] for p in parities))
    summary.update(binding=binding, parities=parities, protocol_request=request)
    if request.get('preset') in ('routed_types', 'routed_dev'):
        from .routed_types import comparison_protocol
        summary['comparison_protocol'] = comparison_protocol(request)
    write_json(output / f"summary-{request['attempt']}.json", summary)
    with (output / f"per-item-{request['attempt']}.jsonl").open('x') as f:
        for record in sorted(latest.values(), key=lambda r: r['key']):
            f.write(json.dumps(record, sort_keys=True, allow_nan=False) + '\n')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('request')
    parser.add_argument('--rank', type=int, default=0)
    parser.add_argument('--world-size', type=int, default=1)
    parser.add_argument('--device')
    parser.add_argument('--merge', action='store_true')
    args = parser.parse_args()
    request = json.loads(Path(args.request).read_text())
    if args.merge:
        merge(request, args.world_size)
    else:
        run_worker(request, args.rank, args.world_size, args.device)


if __name__ == '__main__':
    main()
