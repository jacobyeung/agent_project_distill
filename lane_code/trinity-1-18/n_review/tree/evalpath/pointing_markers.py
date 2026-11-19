"""HF video pointing: trainer duplicate encode, optional per-view text markers."""
from copy import deepcopy
import fcntl
import hashlib
import io
import json
import math
from pathlib import Path
import re
import time

from .items import digest, pinned, sha256

MEMBERSHIP_SHA = '1705f02366bfc1c54e66f85b08dfede79d0f2c3151e08c31111703e4a1f01b50'
VIDEO_ROOT = '/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/67de41a9'
CONDITIONS = ['markers_off', 'markers_on']
EMPTY_THINK = '<think>\n\n</think>\n\n'
QUESTION = ('Point to the {obj} in frame {k}. Output the point as JSON {{"point_2d": [x, y]}} with integer '
            'coordinates on a 0-1000 grid of that frame. If there is no {obj} in frame {k}, output {{"point_2d": null}}.')


def make_request(args, remote, snapshot_manifest):
    request = dict(preset='pointing_markers', kind='base', cfg=dict(frame_layout='duplicate'), artifact=None,
        snapshot=args.snapshot, snapshot_manifest=snapshot_manifest,
        datasets=[dict(benchmark='pointing_markers', rows=dict(
            path=remote+'/o/'+MEMBERSHIP_SHA[:24]+'/0.jsonl', sha256=MEMBERSHIP_SHA))],
        roots=dict(pointing_video_root=VIDEO_ROOT), conditions=CONDITIONS, variants=['A'],
        enable_thinking=False, do_sample=False, max_new_tokens=64,
        frame_cache='$TK_JOBDIR/f', attempt='$SLURM_JOB_ID', output='')
    if args.kind == 'candidate':
        from .pointing_candidates import parse_candidates
        request.update(kind='candidate', candidates=parse_candidates(args.candidate), with_base=args.with_base)
    token = digest(request)[:24]
    request['output'] = remote+'/o/'+token
    return request


def validate_request(request):
    if (request.get('preset') != 'pointing_markers' or request.get('kind') not in ('base', 'candidate') or
            request.get('cfg') != dict(frame_layout='duplicate') or request.get('artifact') is not None or
            request.get('conditions') != CONDITIONS or request.get('variants') != ['A'] or
            request.get('enable_thinking') is not False or request.get('do_sample') is not False or
            type(request.get('max_new_tokens')) is not int or request['max_new_tokens'] != 64 or
            not re.fullmatch(r'[A-Za-z0-9_-]+', request['attempt'])):
        raise ValueError('Pointing marker protocol differs')
    from .pointing_candidates import model_specs
    model_specs(request)
    specs = request['datasets']
    if (len(specs) != 1 or specs[0].get('benchmark') != 'pointing_markers' or
            specs[0]['rows']['sha256'] != MEMBERSHIP_SHA or
            request['roots'] != dict(pointing_video_root=VIDEO_ROOT)):
        raise ValueError('Pointing membership/video binding differs')


def load_tasks(request):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('evalpath/pointing_markers.py:load_tasks')
    value = json.loads(pinned(request['datasets'][0]['rows']).read_text())
    rows = value['items']
    if (len(rows) != 1000 or len({r['id'] for r in rows}) != 1000 or value['seed'] != 17 or
            value.get('count') != 1000):
        raise ValueError('Require fixed 1000-item seed-17 membership')
    result = []
    for r in rows:
        indices, k = r['frame_indices'], r['frame']
        if (type(k) is not int or not 1 <= k <= 32 or len(indices) != 32 or indices != sorted(indices) or
                indices[k-1] != r['source_index'] or not math.isfinite(r['fps']) or r['fps'] <= 0 or
                any(type(i) is not int or not 0 <= i < r['total_num_frames'] for i in indices)):
            raise ValueError('Invalid pointing source selection')
        result.append(dict(benchmark='pointing_video', example_id=r['id']+':A', membership_id=r['id'],
            variant='A', scene=r['scene'], obj=r['obj'], frame=k, source_index=r['source_index'],
            source_frame_indices=indices, fps=r['fps'], total_num_frames=r['total_num_frames'],
            video_path=str(Path(request['roots']['pointing_video_root'])/Path(r['video_rel']).name),
            question=QUESTION.format(obj=r['obj'], k=k), options=[]))
    return sorted(result, key=lambda t: t['example_id'])


def pixel_digest(arrays):
    import numpy as np
    raw = io.BytesIO()
    np.save(raw, arrays, allow_pickle=False)
    return hashlib.sha256(raw.getbuffer()).hexdigest()


def decode_anchors(task):
    """aws_vl media.decode_pointing's exact PyAV ordinal/RGB24 selection."""
    import av
    import numpy as np
    indices = task['source_frame_indices']
    got, want = {}, set(indices)
    with av.open(task['video_path']) as container:
        stream = container.streams.video[0]
        stream.thread_type = 'AUTO'
        for n, frame in enumerate(container.decode(stream)):
            if n in want:
                got[n] = frame.to_ndarray(format='rgb24')
            if n >= indices[-1]:
                break
    if want-set(got):
        raise ValueError('Pointing frames not decoded: '+str(sorted(want-set(got))))
    return np.stack([got[i] for i in indices])


def trainer_row(task, cache):
    """One decode per video selection; authenticate aws_vl's lossless PNG bytes."""
    import numpy as np
    from PIL import Image
    root = Path(cache)
    root.mkdir(parents=True, exist_ok=True)
    stat = Path(task['video_path']).stat()
    identity = dict(path=task['video_path'], size=stat.st_size, mtime_ns=stat.st_mtime_ns,
        indices=task['source_frame_indices'], fps=task['fps'], total=task['total_num_frames'])
    key = digest(identity)
    directory = root/key
    with (root/(key+'.lock')).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        directory.mkdir(exist_ok=True)
        receipt = directory/'0.json'
        if receipt.exists():
            saved = json.loads(receipt.read_text())
            if saved['identity'] != identity:
                raise ValueError('Frame selection changed')
        else:
            arrays = decode_anchors(task)
            frames, pins = [], {}
            for index, array in zip(task['source_frame_indices'], arrays):
                if index not in pins:
                    path = directory/(str(index)+'.png')
                    raw = io.BytesIO()
                    Image.fromarray(array).save(raw, format='PNG', compress_level=1)
                    payload = raw.getvalue()
                    # Keep interrupted fills; changed bytes must never be reused.
                    if path.exists():
                        if path.read_bytes() != payload:
                            raise ValueError('Interrupted PNG differs')
                    else:
                        with path.open('xb') as stream:
                            stream.write(payload)
                    pins[index] = dict(path=str(path.resolve()), sha256=sha256(path), index=index)
                frames.append(pins[index])
            saved = dict(identity=identity, frames=frames, anchor_pixel_sha256=pixel_digest(arrays),
                         duplicate_pixel_sha256=pixel_digest(np.repeat(arrays, 2, axis=0)))
            from .run import write_json
            write_json(receipt, saved)
        arrays = []
        for pin in saved['frames']:
            with Image.open(pinned({k: pin[k] for k in ('path', 'sha256')})) as image:
                if image.mode != 'RGB' or image.format != 'PNG':
                    raise ValueError('Require lossless RGB PNG')
                arrays.append(np.array(image))
        if pixel_digest(np.stack(arrays)) != saved['anchor_pixel_sha256']:
            raise ValueError('Decoded anchor pixels differ')
    return dict(qid=task['example_id'], target=EMPTY_THINK+'{"point_2d": null}', student_input=dict(
        frames=[{k: p[k] for k in ('path', 'sha256')} for p in saved['frames']],
        frame_indices=task['source_frame_indices'], timestamps=[i/task['fps'] for i in task['source_frame_indices']],
        fps=task['fps'], total_num_frames=task['total_num_frames'], question=task['question'], options=[])), saved


def video_prompt(processor, task):
    """aws_vl pointing_video.video_prompt, using the pinned trainer instruction."""
    from student_pilot.trace_contract import ANSWER_FORMAT_INSTRUCTION
    text = task['question']+'\n\n'+ANSWER_FORMAT_INSTRUCTION
    messages = [{'role': 'user', 'content': [{'type': 'video'}, {'type': 'text', 'text': text}]}]
    value = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    if not value.endswith(EMPTY_THINK):
        raise ValueError('Empty think generation prefix changed')
    return value


class ThinkingOff:
    """Change only the generation-prefix flag passed by trainer.training_text."""
    def __init__(self, processor):
        self.processor = processor

    def __getattr__(self, key):
        return getattr(self.processor, key)

    def __call__(self, *args, **kwargs):
        return self.processor(*args, **kwargs)

    def apply_chat_template(self, messages, **kwargs):
        if kwargs.get('add_generation_prompt'):
            kwargs['enable_thinking'] = False
        return self.processor.apply_chat_template(messages, **kwargs)


def encode_prompt(processor, row):
    from student_pilot.carrier_c1_data import encode_layout_row
    batch, audit = encode_layout_row(ThinkingOff(processor), row, 'duplicate', None)
    # The trainer labels start at the JSON answer. The empty think block is prompt text.
    start = audit['prompt_tokens']
    if not bool((batch['labels'][0, :start] == -100).all()) or int(batch['labels'][0, start]) == -100:
        raise ValueError('Trainer answer boundary differs')
    prompt = {k: (v[:, :start] if k in ('input_ids', 'attention_mask', 'mm_token_type_ids') else v)
              for k, v in batch.items() if k != 'labels'}
    if (int(prompt['video_grid_thw'][0, 0]) != 32 or 'position_ids' in prompt or
            any(k.startswith('aux_') for k in prompt)):
        raise ValueError('Require 32 native temporal groups without carriers')
    return prompt, audit, batch['input_ids'][0, :start].tolist()


def marker_pair(processor, batch):
    from student_pilot.carrier_c1_data import insert_frame_markers
    if 'labels' in batch:
        raise ValueError('Markers require a prompt-only batch')
    return dict(markers_off=batch, markers_on=insert_frame_markers(batch, processor.tokenizer, 'duplicate'))


def group_evidence(tokenizer, pair):
    start_id = tokenizer.convert_tokens_to_ids('<|vision_start|>')
    video_id = tokenizer.convert_tokens_to_ids('<|video_pad|>')
    evidence, stripped = {}, []
    off = pair['markers_off']['input_ids'][0].tolist()
    for condition, batch in pair.items():
        ids = batch['input_ids'][0].tolist()
        # The processor may retain an outer video wrapper. Match the trainer's
        # temporal groups: each begins with vision_start immediately before video_pad.
        visual = [i for i, token in enumerate(ids) if token == video_id]
        starts = [i-1 for n, i in enumerate(visual) if n == 0 or visual[n-1] != i-1]
        if len(starts) != 32 or any(i < 0 or ids[i] != start_id for i in starts):
            raise AssertionError('Expected 32 temporal-group vision starts')
        if condition == 'markers_off' and re.search(r'Frame [0-9]+: ', tokenizer.decode(ids, skip_special_tokens=False)):
            raise AssertionError('Unexpected marker in control prompt')
        windows, removed, previous = [], [], 0
        for k, cut in enumerate(starts, 1):
            marker = tokenizer.encode(f'Frame {k}: ', add_special_tokens=False)
            found = ids[max(0, cut-len(marker)):cut] == marker
            if found != (condition == 'markers_on'):
                raise AssertionError('Frame marker presence/order differs')
            if condition == 'markers_on':
                removed.extend(ids[previous:cut-len(marker)])
                previous = cut
            lo, hi = max(0, cut-len(marker)-8), min(len(ids), cut+9)
            windows.append(dict(group=k, vision_start_position=cut, marker_ids=marker, marker_present=found,
                                window_start=lo, token_ids=ids[lo:hi], text=tokenizer.decode(ids[lo:hi], skip_special_tokens=False)))
        if condition == 'markers_on':
            removed.extend(ids[previous:])
            stripped = removed
        evidence[condition] = dict(input_tokens=len(ids), groups=windows,
            non_group_vision_start_positions=[i for i, token in enumerate(ids) if token == start_id and i not in starts])
    if stripped != off:
        raise AssertionError('Removing only marker ids did not recover trainer prompt')
    # Markers alter text fields only; native visual tensors retain the trainer bytes.
    import torch
    for key in ('pixel_values_videos', 'video_grid_thw'):
        if not torch.equal(pair['markers_off'][key], pair['markers_on'][key]):
            raise AssertionError('Marker insertion altered visual tensors')
    return evidence


def parity_item(processor, task, cache):
    import numpy as np
    import torch
    from transformers.video_utils import VideoMetadata
    from student_pilot.pose_samples import load_frames, DEFAULT_PIXELS
    row, receipt = trainer_row(task, cache)
    batch, audit, trainer_ids = encode_prompt(processor, row)
    arrays = np.repeat(load_frames(row['student_input']), 2, axis=0)
    if pixel_digest(arrays) != receipt['duplicate_pixel_sha256']:
        raise AssertionError('Trainer duplicate pixels differ from aws_vl decode')
    metadata = VideoMetadata(fps=task['fps'], total_num_frames=task['total_num_frames'],
        frames_indices=[i for i in task['source_frame_indices'] for _ in range(2)],
        height=arrays.shape[1], width=arrays.shape[2])
    direct = processor(text=[video_prompt(processor, task)], videos=[arrays], video_metadata=[metadata],
        do_sample_frames=False, size=dict(shortest_edge=64*DEFAULT_PIXELS[0], longest_edge=64*DEFAULT_PIXELS[1]),
        return_tensors='pt', return_metadata=True)
    ids = batch['input_ids'][0].tolist()
    if ids != trainer_ids or ids != direct['input_ids'][0].tolist():
        raise AssertionError('Trainer / no-marker / aws_vl thinking-off prompt ids differ')
    for key in ('pixel_values_videos', 'video_grid_thw'):
        if not torch.equal(batch[key], direct[key]):
            raise AssertionError('Trainer / direct processor pixels or grid differ')
    evidence = group_evidence(processor.tokenizer, marker_pair(processor, batch))
    return dict(example_id=task['example_id'], membership_id=task['membership_id'],
        no_marker_equals_trainer_encode=True, no_marker_equals_aws_vl_prompt=True,
        trainer_prompt_ids=trainer_ids, no_marker_prompt_ids=ids,
        trainer_prompt_ids_sha256=digest(trainer_ids), conditions=evidence, audit=audit,
        anchor_pixel_sha256=receipt['anchor_pixel_sha256'], duplicate_pixel_sha256=receipt['duplicate_pixel_sha256'],
        png_pins=receipt['frames'], **{'pass': True})


def native_generate(model, processor, batch):
    import torch
    config = deepcopy(model.generation_config)
    config.do_sample = False
    config.num_beams = 1
    config.num_return_sequences = 1
    config.temperature = config.top_p = config.top_k = None
    config.min_p = config.min_new_tokens = None
    config.repetition_penalty = config.length_penalty = 1.0
    config.no_repeat_ngram_size = 0
    config.early_stopping = False
    start = batch['input_ids'].shape[1]
    if start+64 > model.config.text_config.max_position_embeddings:
        raise ValueError('Prompt exhausts native context')
    with torch.inference_mode():
        result = model.generate(**batch, generation_config=config, max_new_tokens=64, use_cache=True,
                                return_dict_in_generate=True, output_scores=False)
    tokens = result.sequences[0, start:].tolist()
    eos = config.eos_token_id
    eos = eos if isinstance(eos, (list, tuple)) else [eos]
    return dict(raw_generation=processor.tokenizer.decode(tokens, skip_special_tokens=True),
        raw_generation_with_special_tokens=processor.tokenizer.decode(tokens, skip_special_tokens=False),
        output_token_ids=tokens, output_tokens=len(tokens), input_tokens=start,
        input_token_count=start, hit_token_cap=len(tokens) == 64 and (not tokens or tokens[-1] not in eos),
        finish_reason='eos' if tokens and tokens[-1] in eos else 'max_new_tokens')


def record_key(task, condition):
    return 'pointing_video:'+task['example_id']+':'+condition


def expected_keys(tasks):
    return {record_key(t, c) for t in tasks for c in CONDITIONS}


def summarize(records, tasks, parity_pass):
    complete = {k for k, r in records.items() if r.get('status') == 'complete'}
    coverage = complete == expected_keys(tasks) and set(records) <= expected_keys(tasks)
    return dict(expected_count=2*len(tasks), completed=len(complete), coverage_complete=coverage,
        parity_pass=parity_pass, numbers_status='eligible' if coverage and parity_pass else 'do not count',
        scoring_protocol='Trinity score_pointing_video.score_rows per condition, variant A',
        conditions={c: dict(expected=len(tasks), completed=sum(r.get('status') == 'complete' and
            r['condition'] == c for r in records.values())) for c in CONDITIONS})


def run_worker(request, rank, world_size, device=None):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('evalpath/pointing_markers.py:run_worker')
    if request.get('kind') == 'candidate':
        from .pointing_candidates import run_worker as candidate_worker
        return candidate_worker(request, rank, world_size, device)
    import torch
    from student_pilot.carrier_c1_run import move
    from .runtime import load_model
    from .run import append_record, binding_for, read_journal, shard_items, write_json
    validate_request(request)
    device = device or f'cuda:{rank}'
    if torch.device(device).type != 'cuda':
        raise ValueError('GPU worker required')
    output = Path(request['output'])
    output.mkdir(parents=True, exist_ok=True)
    binding = binding_for(request, world_size)
    with (output/f'worker-{rank}.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        tasks = load_tasks(request)
        assigned = shard_items(tasks, rank, world_size)
        journal = output/f'items-{rank}.jsonl'
        records = read_journal(journal, binding)
        if not set(records) <= expected_keys(assigned):
            raise ValueError('Journal has items outside shard')
        model, processor, info = load_model('base', request['cfg'], snapshot=request['snapshot'], device=device)
        fixed = tasks[:5]
        parity = dict(binding=binding, rank=rank, attempt=request['attempt'], model=info, items=[], **{'pass': False})
        try:
            for task in fixed:
                parity['items'].append(parity_item(processor, task, request['frame_cache']))
            parity['pass'] = len(parity['items']) == 5
        except Exception as exc:
            parity['error'] = f'{type(exc).__name__}: {exc}'
        parity_path = output/f"parity-{rank}-{request['attempt']}.json"
        write_json(parity_path, parity)
        for task in assigned:
            pending = [c for c in CONDITIONS if records.get(record_key(task, c), {}).get('status') != 'complete']
            if not pending:
                continue
            started = time.perf_counter()
            try:
                row, receipt = trainer_row(task, request['frame_cache'])
                batch, audit, trainer_ids = encode_prompt(processor, row)
                pair = marker_pair(processor, batch)
                # Every generated prompt satisfies the same group checks as the five-item receipt.
                group_evidence(processor.tokenizer, pair)
                error = None
            except Exception as exc:
                error = f'{type(exc).__name__}: {exc}'
            for condition in pending:
                record = {k: task[k] for k in ('benchmark', 'example_id', 'membership_id', 'variant',
                                               'scene', 'obj', 'frame', 'source_index')}
                record.update(item_id=task['membership_id'], condition=condition, key=record_key(task, condition),
                    model='base',
                    binding=binding, rank=rank, attempt=request['attempt'], status='error', raw_generation='',
                    max_new_tokens=64)
                try:
                    if error:
                        raise ValueError(error)
                    record.update(native_generate(model, processor, move(pair[condition], device)),
                        status='complete', processed_height_width=audit['processed_height_width'],
                        trainer_prompt_ids_sha256=digest(trainer_ids), anchor_pixel_sha256=receipt['anchor_pixel_sha256'],
                        duplicate_pixel_sha256=receipt['duplicate_pixel_sha256'], num_frames=64, num_viewpoints=32)
                except Exception as exc:
                    record['error'] = f'{type(exc).__name__}: {exc}'
                record['elapsed_s'] = time.perf_counter()-started
                append_record(journal, record)
                records[record['key']] = record
        summary = summarize(records, assigned, parity['pass'])
        summary.update(binding=binding, rank=rank, parity_path=str(parity_path), model=info)
        write_json(output/f"summary-{rank}-{request['attempt']}.json", summary)
        return summary


def merge(request, world_size):
    if request.get('kind') == 'candidate':
        from .pointing_candidates import merge as candidate_merge
        return candidate_merge(request, world_size)
    from .run import binding_for, read_journal, shard_items, write_json
    validate_request(request)
    tasks = load_tasks(request)
    binding = binding_for(request, world_size)
    output, records, parities = Path(request['output']), {}, []
    for rank in range(world_size):
        shard = read_journal(output/f'items-{rank}.jsonl', binding)
        if not set(shard) <= expected_keys(shard_items(tasks, rank, world_size)) or set(shard) & set(records):
            raise ValueError('Merged journals have duplicate or misplaced items')
        records.update(shard)
        path = output/f"parity-{rank}-{request['attempt']}.json"
        parity = json.loads(path.read_text()) if path.exists() else {'pass': False, 'missing': str(path)}
        if path.exists():
            if (parity.get('binding') != binding or parity.get('rank') != rank or
                    parity.get('attempt') != request['attempt']):
                raise ValueError('Parity belongs to another run/shard')
            if parity.get('pass') and [it['example_id'] for it in parity.get('items', [])] != [t['example_id'] for t in tasks[:5]]:
                raise ValueError('Parity items differ from fixed five')
        parities.append(parity)
    summary = summarize(records, tasks, all(p['pass'] for p in parities))
    summary.update(binding=binding, parities=parities, protocol_request=request)
    write_json(output/f"summary-{request['attempt']}.json", summary)
    for condition in [None, *CONDITIONS]:
        name = 'per-item' if condition is None else condition
        with (output/f"{name}-{request['attempt']}.jsonl").open('x') as stream:
            for _, record in sorted(records.items()):
                if condition is None or record['condition'] == condition:
                    stream.write(json.dumps(record, sort_keys=True, allow_nan=False)+'\n')
    return summary
