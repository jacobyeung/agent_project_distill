"""GPU gates P1/P2/P3. Failures invalidate numbers without stopping scoring."""
import json
import re
import sqlite3
import time

from .items import pinned


class LogitTap:
    """Store only top two logits at sampled positions, never vocabulary-sized histories."""
    def __init__(self):
        self.positions = {}

    def __call__(self, ids, logits):
        values, indices = logits[0].float().topk(2)
        self.positions[len(ids)] = dict(token=int(indices[0]), top2=indices.tolist(),
                                        logits=values.tolist(), margin=float(values[0] - values[1]))
        return logits


def injected_positions(record):
    positions = set()
    for call in record['calls']:
        positions.update(range(call['at_token'], call['at_token'] + call['forced_tokens']))
    return positions


def transcript_target(processor, record):
    """The prompt already opens <think>; restore it for training_text's full assistant."""
    tail = record['text']
    # Only generated terminal controls are removed. The trainer itself appends both
    # required stops; their lengths remain part of the strict full-sequence check.
    tail = re.sub(r'(?:<\|(?:im_end|endoftext)\|>)+$', '', tail)
    return '<think>\n' + tail


def compare_logits(record, teacher, cached, prompt_length, project, chunk_size=32):
    """project(position list) returns uncached logits, bounded to a small chunk."""
    injected = injected_positions(record)
    positions = [i for i in range(len(record['tokens'])) if i not in injected]
    mismatches, exact, checked = [], 0, 0
    for offset in range(0, len(positions), chunk_size):
        chunk = positions[offset:offset + chunk_size]
        valid = [i for i in chunk if prompt_length + i - 1 < len(teacher)]
        if not valid:
            continue
        logits = project([prompt_length + i - 1 for i in valid]).float()
        values, indices = logits.topk(2, dim=-1)
        for j, i in enumerate(valid):
            checked += 1
            token = record['tokens'][i]
            best = int(indices[j, 0])
            exact += best == token
            if best != token:
                margin = float(values[j, 0] - values[j, 1])
                cached_path = cached.get(i)
                mismatches.append(dict(generated_position=i, generated_token=token,
                    uncached_top2=indices[j].tolist(), uncached_logits=values[j].tolist(),
                    uncached_margin=margin, cached=cached_path,
                    fails_margin=(margin > .05 or cached_path is None or cached_path['margin'] > .05)))
    complete = checked == len(positions) and all(i in cached for i in positions)
    return dict(pass_=complete and not any(m['fails_margin'] for m in mismatches),
                sampled_positions=len(positions), checked=checked, argmax_exact=exact,
                argmax_mismatches=len(mismatches), mismatches=mismatches,
                margin_threshold=.05, cached_positions_complete=complete)


def p1(model, processor, row, cfg, kind, batch, record, tap, strict=False):
    import torch
    from student_pilot.carrier_c1_run import move
    from .runtime import teacher_batch
    target = transcript_target(processor, record)
    teacher = teacher_batch(processor, {**row, 'target': target}, cfg, kind)
    teacher = move(teacher, batch['input_ids'].device)
    live = int(teacher['attention_mask'].sum())
    ids = teacher['input_ids'][0, :live].tolist()
    decoded = batch['input_ids'][0].tolist() + record['tokens']
    differences = [i for i, (a, b) in enumerate(zip(ids, decoded)) if a != b]
    # The decode loop stops at its first EOS. Tokens the trainer appends after that EOS (its training
    # stop token) never reach inference, so they are reported and must be stop tokens only.
    stops = {processor.tokenizer.eos_token_id, processor.tokenizer.convert_tokens_to_ids('<|endoftext|>'),
             processor.tokenizer.convert_tokens_to_ids('<|im_end|>')}
    tail_ok = (record.get('finish') == 'eos' and all(t in stops for t in ids[len(decoded):]))
    sequence_equal = ids == decoded or (ids[:len(decoded)] == decoded and tail_ok)
    sequence = dict(exact=sequence_equal, teacher_tokens=len(ids), decode_tokens=len(decoded),
                    equal_positions=sum(a == b for a, b in zip(ids, decoded)),
                    mismatch_count=len(differences) + abs(len(ids) - len(decoded)),
                    first_mismatch=(differences[0] if differences else min(len(ids), len(decoded)))
                                   if not sequence_equal else None,
                    teacher_extra_tail=ids[len(decoded):])
    for key in ('input_ids', 'attention_mask', 'mm_token_type_ids', 'labels'):
        if key in teacher:
            teacher[key] = teacher[key][:, :live]
    with torch.no_grad():
        if kind == 'routed':
            hidden = model.hidden(teacher, carriers=True)
        else:
            inputs = {k: teacher[k] for k in ('input_ids', 'attention_mask', 'mm_token_type_ids',
                        'pixel_values_videos', 'video_grid_thw') if k in teacher}
            hidden = model.model(**inputs, use_cache=False, return_dict=True).last_hidden_state
        def project(positions):
            logits = model.lm_head(hidden[0, positions])
            if strict and kind == 'routed':
                reserved = [processor.tokenizer.convert_tokens_to_ids(t) for t in ('<tool_response>', '</tool_response>')]
                logits[:, reserved+[model.carrier_id]] = -float('inf')
            return logits
        comparison = compare_logits(record, ids, tap.positions, batch['input_ids'].shape[1], project)
    logits_pass = comparison.pop('pass_')
    if strict:
        logits_pass = logits_pass and comparison['argmax_mismatches'] == 0
    return {'pass': sequence_equal and logits_pass, 'sequence': sequence, **comparison}


def p2(model, batch, record, kind, strict=False):
    if kind == 'base':
        return {'pass': True, 'not_applicable': 'native base: no injected responses or heads'}
    import numpy as np
    import torch
    from student_pilot import carrier_c1_decode as decode, carrier_c1_routing as routing
    from student_pilot.p3_printed_calculator import PrintedPointRegistry
    replay = decode.replay(record)
    prefix = routing.prefix_batch(batch)
    with torch.no_grad():
        hidden = model.hidden(prefix, carriers=True)
        heads = model.readout_heads(hidden, prefix, None)
    pose = heads['pose'][0].double().cpu().numpy()
    gravity = None if heads['gravity'] is None else heads['gravity'][0].double().cpu().numpy()
    queries = []

    def depth(frame, points):
        uv = torch.full((32, len(points), 2), 500., device=hidden.device)
        uv[frame - 1] = torch.as_tensor(points, dtype=torch.float32, device=hidden.device)
        with torch.no_grad():
            values = model.readout_heads(hidden, prefix, uv)['depth']
        if values is None:
            raise routing.RenderError('own depth head unavailable')
        result = values[frame - 1].double().cpu().numpy()
        queries.append(dict(frame=frame, depth=result.tolist()))
        return result

    try:
        geometry = routing.OwnGeometry(pose, gravity, depth)
    except routing.RenderError:
        geometry = None
    registry = PrintedPointRegistry()
    mismatches = []
    # Include typed errors as well; trainer replay currently skips those records.
    for i, call in enumerate(record['calls']):
        response, _ = decode.respond(call['call'], registry, geometry)
        if response.encode() != call['response'].encode():
            mismatches.append(dict(call_index=i, expected=call['response'], independent=response))
    diff = float(np.abs(pose - np.asarray(record['heads']['pose9'])).max())
    raw_equal = pose.tobytes() == np.asarray(record['heads']['pose9'], dtype=np.float64).tobytes()
    raw_equal &= ((gravity is None and record['heads']['gravity'] is None) or
                  (gravity is not None and gravity.tobytes() == np.asarray(record['heads']['gravity'], dtype=np.float64).tobytes()))
    raw_equal &= len(queries) == len(record['heads']['depth_queries']) and all(
        a['frame'] == b['frame'] and np.asarray(a['depth'], dtype=np.float64).tobytes() ==
        np.asarray(b['depth'], dtype=np.float64).tobytes() for a,b in zip(queries, record['heads']['depth_queries']))
    return {'pass': replay['byte_equal'] and not mismatches and (raw_equal if strict else diff <= 1e-3),
            'replay': replay, 'independent_calls': len(record['calls']),
            'independent_byte_equal': not mismatches, 'mismatches': mismatches,
            'max_pose9_abs_diff': diff, 'pose_tolerance': 0. if strict else 1e-3, 'head_values_byte_equal': bool(raw_equal),
            'question_independent': True, 'depth_queries': queries}


def p3(processor, row, cfg, batch, strict=False):
    import numpy as np
    import torch
    from transformers.video_utils import VideoMetadata
    from student_pilot.carrier_c1_data import layout_inputs, READOUT_TARGET
    from student_pilot.pose_samples import load_frames, encode_frames, DEFAULT_PIXELS
    layout = cfg.get('frame_layout', 'spread')
    inputs = layout_inputs(row, layout, cfg.get('frame_pair_gap_seconds'))
    arrays = load_frames(row['student_input'] if layout == 'duplicate' else inputs)
    if layout == 'duplicate':
        arrays = np.repeat(arrays, 2, axis=0)
    meta = VideoMetadata(total_num_frames=inputs['total_num_frames'], fps=inputs['fps'],
        frames_indices=inputs['frame_indices'], width=arrays.shape[2], height=arrays.shape[1])
    expected, audit = encode_frames(processor, inputs['question'], inputs.get('options') or [],
                                   arrays, meta, READOUT_TARGET, DEFAULT_PIXELS, 16384)
    actual = batch['pixel_values_videos'].cpu()
    wanted = expected['pixel_values_videos'].cpu()
    grid_equal = torch.equal(batch['video_grid_thw'].cpu(), expected['video_grid_thw'].cpu())
    count = len(arrays)
    grid_count = int(batch['video_grid_thw'][0, 0]) * processor.video_processor.temporal_patch_size
    equal = actual.shape == wanted.shape and actual.dtype == wanted.dtype and torch.equal(actual, wanted)
    expected_count = 64 if layout == 'duplicate' else 32
    prompt_check, prompt_ok = {}, True
    if strict:
        from .runtime import teacher_batch
        encoded = teacher_batch(processor, {**row, 'target': READOUT_TARGET}, cfg, 'routed')
        start = int(torch.where(encoded['labels'][0] != -100)[0][0])
        ids_equal = torch.equal(batch['input_ids'].cpu(), encoded['input_ids'][:, :start].cpu())
        text = processor.tokenizer.decode(batch['input_ids'][0].tolist(), skip_special_tokens=False)
        markers = [text.count(f'Frame {k}: ') for k in range(1,33)]
        markers_equal = all(n == 1 for n in markers) if cfg.get('frame_markers') else not any(markers)
        prompt_check = dict(prompt_ids_equal=ids_equal, trainer_prompt_ids=encoded['input_ids'][0,:start].tolist(),
                            prompt_ids=batch['input_ids'][0].tolist(), marker_counts=markers, markers_equal=markers_equal)
        prompt_ok = ids_equal and markers_equal
    return {'pass': equal and grid_equal and grid_count == count and count == expected_count and prompt_ok, **prompt_check,
            'pixel_equal': equal, 'shape': list(actual.shape), 'dtype': str(actual.dtype),
            'grid_equal': grid_equal, 'video_grid_thw': batch['video_grid_thw'].tolist(),
            'input_frame_count': count, 'expected_frame_count': expected_count,
            'size_budget': {'shortest_edge': count * DEFAULT_PIXELS[0],
                            'longest_edge': count * DEFAULT_PIXELS[1]}, 'trainer_audit': audit}


def heldout_rows(pin, roots=None):
    """Five fixed rows, ordered by DB index; receipt and database both authenticated."""
    receipt = json.loads(pinned(pin).read_text())
    if receipt.get('schema') != 'c1-routing-stream-v1' or receipt.get('scene_role') != 'heldout':
        raise ValueError('Routing parity requires a held-out routing receipt')
    from .kit_inputs import map_path
    roots = roots or {}
    database = pinned({**receipt['database'], 'path': map_path(receipt['database']['path'], roots)})
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as connection:
        rows = [json.loads(r[0]) for r in connection.execute('SELECT row FROM rows ORDER BY i LIMIT 5')]
    if len(rows) != 5:
        raise ValueError('Routing parity needs five held-out rows')
    def remap(value):
        if isinstance(value, dict):
            return {k: map_path(v, roots) if k == 'path' and isinstance(v, str) and v.startswith('/')
                    else remap(v) for k,v in value.items()}
        if isinstance(value, list):
            return [remap(v) for v in value]
        return value
    return [remap(row) for row in rows]


def run_suite(model, processor, cfg, kind, vqa_rows, *, routing_pin=None, max_new_tokens=None, routing_roots=None,
              strict=False, parity_tasks=None, dev=False, on_item=None):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('evalpath/parity.py:run_suite')
    import torch
    from student_pilot.carrier_c1_run import move
    from .runtime import generate, prompt_batch
    if next(model.parameters()).device.type != 'cuda':
        raise ValueError('Parity is GPU only')
    streams = {'vqa': list(vqa_rows)}
    report = {'schema': 'evalpath-parity-v1', 'streams': {}, 'pass': True}
    if dev and not strict:
        raise ValueError('Development parity requires strict P1/P2/P3')
    required = 2 if dev else 6 if strict else 5
    if len(streams['vqa']) != required:
        report['pass'] = False
        report['vqa_error'] = f'Exactly {required} fixed parity rows are required'
    if strict:
        report['routing'] = ('Production head calls tested on dev-only prompts and camera probe' if dev
                             else 'Production head calls tested on the fixed VSI prompts and camera probe')
    elif routing_pin:
        try:
            streams['routing'] = heldout_rows(routing_pin, routing_roots)
        except Exception as exc:
            report.update({'pass': False, 'routing_error': f'{type(exc).__name__}: {exc}'})
    else:
        report['routing'] = 'not pinned; routing stream not tested'
    for stream, rows in streams.items():
        records = []
        for index, row in enumerate(rows):
            started = time.perf_counter()
            result = dict(qid=row['qid'])
            if strict:
                task = parity_tasks[index]
                result.update(example_id=task['example_id'], question_type=task['question_type'],
                              prompt=task['question'], camera_probe=task['question_type'] == 'camera_pose_probe')
            try:
                batch = move(prompt_batch(processor, row, cfg, kind), next(model.parameters()).device)
                tap = LogitTap()
                record = generate(model, processor, batch, kind, max_new_tokens, tap)
                result['decode'] = record
                if on_item:
                    on_item(dict(result, phase='decode_complete', elapsed_s=time.perf_counter()-started))
                for name, check in [('P1', lambda: p1(model, processor, row, cfg, kind, batch, record, tap, strict)),
                                    ('P2', lambda: p2(model, batch, record, kind, strict)),
                                    ('P3', lambda: p3(processor, row, cfg, batch, strict))]:
                    try:
                        result[name] = check()
                    except Exception as exc:
                        if dev:
                            raise
                        result[name] = {'pass': False, 'error': f'{type(exc).__name__}: {exc}'}
                result['pass'] = all(result[name]['pass'] for name in ('P1', 'P2', 'P3'))
            except Exception as exc:
                if dev:
                    raise
                result.update({'pass': False, 'error': f'{type(exc).__name__}: {exc}'})
            if on_item:
                on_item(dict(result, phase='item_complete', elapsed_s=time.perf_counter()-started))
            records.append(result)
        report['streams'][stream] = records
        report['pass'] &= len(records) == required and all(r['pass'] for r in records)
    if strict:
        from .routed_types import TYPES
        rows = report['streams']['vqa']
        routed_rows = [r for r in rows if any(c.get('kind') == 'head' for c in r.get('decode', {}).get('calls', []))]
        routed = sum(r.get('question_type') in TYPES[:3] for r in routed_rows)
        distance = any(r.get('question_type') == 'object_abs_distance' for r in routed_rows)
        direction = any(r.get('question_type') in TYPES[:2] for r in routed_rows)
        camera = any(r.get('camera_probe') and any(c.get('kind') == 'head' and c['call'].startswith(('<pose ', '<move ', '<turn '))
                     for c in r.get('decode', {}).get('calls', [])) for r in rows)
        report['route_coverage'] = (dict(routed_items=len(routed_rows), required=1, camera_call=camera) if dev else
            dict(routed_target_items=routed, required=2, camera_call=camera,
                 distance_routed=distance, direction_routed=direction))
        report['pass'] &= (camera if dev else routed >= 2 and camera and distance and direction)
    report['numbers_status'] = 'eligible' if report['pass'] else 'do not count'
    all_rows = [r for rows in report['streams'].values() for r in rows]
    report['counts'] = dict(items=len(all_rows), passed=sum(r['pass'] for r in all_rows),
        sequence_exact=sum(r.get('P1', {}).get('sequence', {}).get('exact', False) for r in all_rows),
        argmax_exact=sum(r.get('P1', {}).get('argmax_exact', 0) for r in all_rows),
        argmax_checked=sum(r.get('P1', {}).get('checked', 0) for r in all_rows),
        injected_byte_equal=sum(r.get('P2', {}).get('independent_byte_equal', False) for r in all_rows),
        pixel_exact=sum(r.get('P3', {}).get('pixel_equal', False) for r in all_rows))
    return report
