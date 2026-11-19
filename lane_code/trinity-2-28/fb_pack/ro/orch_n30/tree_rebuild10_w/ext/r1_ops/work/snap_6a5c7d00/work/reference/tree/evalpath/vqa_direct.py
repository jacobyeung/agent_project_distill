"""Direct VQA through the pinned trainer processor, encode, and native generation."""
import fcntl
import io
import json
from pathlib import Path
import re
import time

from .items import digest, load_items, pinned, read_rows, sha256, trainer_row as anchor_row
from .pointing_candidates import validate_pin

COMMIT = '7ab550d4b022c7ac84d34942a5bb3f6dd23899e7'
POOL_SHA = '9f923ba410a5765231131a241675c585cf7841a207fee4a05f3e29d0855483df'
PLACEMENT = 'append_after_temporal_group_video_tokens_v1'


def validate_request(request):
    cfg = request['cfg']
    if (request.get('preset') != 'vqa_direct' or request.get('kind') not in ('candidate','routed-off')
            or request.get('direct_protocol') != 'trainer-vqa-direct-v1'
            or type(request.get('frames')) is not int or request['frames'] not in (32,64)
            or request.get('max_new_tokens') != 16384 or request.get('enable_thinking') is not True
            or request.get('do_sample') is not False or request.get('truncation_views') != [4096]
            or cfg.get('training_mode') != 'final' or cfg.get('frame_layout') != 'duplicate'
            or cfg.get('frame_markers') is not True or cfg.get('carrier_placement') != PLACEMENT
            or any(k in request for k in ('pose_override','routed_protocol','routing_heldout'))):
        raise ValueError('Direct trainer VQA protocol differs')
    attempt = request.get('attempt','')
    if attempt != '$SLURM_JOB_ID' and not re.fullmatch(r'[A-Za-z0-9_-]+',attempt):
        raise ValueError('attempt must be a filename-safe job identifier')
    specs = model_specs(request)
    if request['kind'] == 'routed-off' and request.get('artifact') != specs[0]['artifact']:
        raise ValueError('routed-off artifact differs')
    datasets = request['datasets']
    from .items import MEMBERSHIP_SHA256
    if (len(datasets) not in (1,2) or datasets[0].get('benchmark') != 'dev858'
            or datasets[0]['rows']['sha256'] != POOL_SHA or (len(datasets) == 2 and (
                datasets[1].get('benchmark') != 'vsi500'
                or datasets[1]['membership']['sha256'] != MEMBERSHIP_SHA256))):
        raise ValueError('Direct VQA population differs')
    for spec in datasets:
        validate_pin(spec['rows'])
    if len(datasets) == 2:
        validate_pin(datasets[1]['membership'])
    if 'dev_subset' in request:
        validate_pin(request['dev_subset'])
    if 'direct_trainer' in request:
        spec = request['direct_trainer']
        if (not re.fullmatch('[0-9a-f]{40}', spec.get('commit',''))
                or not spec.get('closure') or not spec.get('sources')):
            raise ValueError('Direct trainer pin differs')
        validate_pin(spec['archive']); validate_pin(spec['inventory'])


def model_specs(request):
    specs = request.get('candidates')
    if not isinstance(specs, list) or not specs:
        raise ValueError('Require candidate artifact pins')
    names = set()
    for spec in specs:
        if (set(spec) != {'name','artifact'} or not isinstance(spec['name'],str)
                or not re.fullmatch('[A-Za-z0-9_-]{1,80}',spec['name']) or spec['name'] in names):
            raise ValueError('Candidate labels differ')
        validate_pin(spec['artifact']); names.add(spec['name'])
    if request['kind'] == 'routed-off' and (len(specs) != 1 or specs[0]['name'] != 'routed-off'):
        raise ValueError('routed-off requires one artifact')
    return specs


def subset_ids(value):
    ids = value.get('ids') if isinstance(value, dict) else value
    if (not isinstance(ids, list) or not ids or any(type(i) not in (str,int) for i in ids)
            or len({str(i) for i in ids}) != len(ids)):
        raise ValueError('Development selection requires unique IDs')
    return [str(i) for i in ids]


def load_tasks(request):
    validate_request(request)
    rows = read_rows(request['datasets'][0]['rows'])
    if (len(rows) != 858 or len({str(r['id']) for r in rows}) != 858
            or any(r['dataset'] != 'scannet' or not re.fullmatch(r'scene\d{4}_\d{2}', r['scene_name']) for r in rows)):
        raise ValueError('Development population differs')
    if 'dev_subset' in request:
        path = Path(request['dev_subset']['path'])
        if path.stat().st_size > 1 << 20:
            raise ValueError('Development selection exceeds budget')
        pinned(request['dev_subset'])
        ids = set(subset_ids(json.loads(path.read_text())))
        if not ids <= {str(r['id']) for r in rows}:
            raise ValueError('Development selection has unknown IDs')
        rows = [r for r in rows if str(r['id']) in ids]
    from .official import build_prompt_context
    tasks = []
    for row in sorted(rows, key=lambda r:str(r['id'])):
        task = {**row, 'example_id':str(row['id']), 'benchmark':'dev858', 'options':row.get('options') or [],
                'video_path':request['roots']['video_root'].rstrip('/')+'/scannet/'+row['scene_name']+'.mp4'}
        build_prompt_context(task, 'ours')
        tasks.append(task)
    if len(request['datasets']) == 2:
        tasks.extend(load_items(request['datasets'][1], request['roots']))
    if len(tasks) != len(rows) + (500 if len(request['datasets']) == 2 else 0):
        raise ValueError('Full direct VQA population differs')
    return tasks


def trainer_row(task, cache, frames):
    """Keep CP1's official 32 anchors; CP2 bisects gaps without changing anchors."""
    from student_pilot import carrier_c1_data as data
    row = anchor_row(task, cache)
    si = row['student_input']
    if 'anchor_slots' in si or len(si['frames']) != 32:
        raise ValueError('CP1 anchor row must omit anchor_slots')
    if frames == 32:
        return row
    if frames != 64:
        raise ValueError('frames must be 32 or 64')
    indices, slots = data.nested_indices(si['frame_indices'])
    identity = dict(anchor_receipt=si, indices=indices, anchor_slots=slots, protocol='nested-vqa-v1')
    directory = Path(cache)/digest(identity)
    directory.mkdir(parents=True, exist_ok=True)
    receipt = directory/'frames.json'
    from .run import write_json
    with (directory/'fill.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if receipt.exists():
            saved = json.loads(receipt.read_text())
            if saved['identity'] != identity:
                raise ValueError('Nested video identity differs')
        else:
            import av
            from PIL import Image
            pins = dict(zip(si['frame_indices'], si['frames']))
            needed = set(indices)-pins.keys()
            with av.open(task['video_path']) as container:
                for ordinal, frame in enumerate(container.decode(video=0)):
                    if ordinal not in needed:
                        continue
                    buffer = io.BytesIO()
                    Image.fromarray(frame.to_ndarray(format='rgb24')).save(buffer, format='PNG')
                    path = directory/f'{ordinal}.png'; raw = buffer.getvalue()
                    if path.exists():
                        if path.read_bytes() != raw:
                            raise ValueError('Interrupted nested PNG differs')
                    else:
                        with path.open('xb') as stream:
                            stream.write(raw)
                    pins[ordinal] = dict(path=str(path.resolve()), sha256=sha256(path))
            if not set(indices) <= pins.keys():
                raise ValueError('Source video omitted a nested frame')
            saved = dict(identity=identity, frames=[pins[k] for k in indices])
            write_json(receipt, saved)
        for pin in saved['frames']:
            pinned(pin)
    return {**row, 'student_input':{**si, 'frames':saved['frames'], 'frame_indices':indices,
                                  'timestamps':[k/si['fps'] for k in indices], 'anchor_slots':slots}}


def encode_prompt(processor, row, cfg, frames):
    """Call the trainer's VQA encode, then cut only the supervised suffix/padding."""
    import torch
    from student_pilot import carrier_c1_data as data
    from .items import assert_prompt_equal
    si = row['student_input']
    if (len(si['frames']) != frames or (frames == 32 and 'anchor_slots' in si)
            or (frames == 64 and (len(si.get('anchor_slots',[])) != 32
                or data.nested_indices([si['frame_indices'][k] for k in si['anchor_slots']]) !=
                   (si['frame_indices'],si['anchor_slots'])))):
        raise ValueError('VQA frame/anchor contract differs')
    if getattr(processor.tokenizer,'_c1_frame_markers',False) is not True:
        raise ValueError('processor_for_receipt must enable frame markers')
    assert_prompt_equal(processor, row)
    layout, gap = data.layout_settings(cfg)
    batch, _, audit = data.encode(processor, {**row,'target':data.READOUT_TARGET}, {}, 'vqa',
        cfg['carrier_placement'], cfg['training_mode'], layout, gap)
    start = int(torch.where(batch['labels'][0] != -100)[0][0])
    prompt = {k:(v[:,:start] if k in ('input_ids','attention_mask','mm_token_type_ids') else v)
              for k,v in batch.items() if k != 'labels'}
    if not processor.tokenizer.decode(prompt['input_ids'][0].tolist(),skip_special_tokens=False).endswith('<think>\n'):
        raise ValueError('Trainer generation prefix must leave thinking open')
    return prompt, {**audit, **encoding_evidence(processor,prompt,si,frames),
                    'input_tokens':start, 'prompt_ids_sha256':digest(prompt['input_ids'][0].tolist())}


def encoding_evidence(processor, batch, si, frames):
    from student_pilot.camera_targets import carrier_id, VIDEO_TOKEN
    tok = processor.tokenizer
    ids = batch['input_ids'][0].tolist()
    visual = tok.convert_tokens_to_ids(VIDEO_TOKEN)
    starts = [i for i,v in enumerate(ids) if v == visual and (i == 0 or ids[i-1] != visual)]
    ends = [i for i,v in enumerate(ids) if v == visual and (i+1 == len(ids) or ids[i+1] != visual)]
    groups = int(batch['video_grid_thw'][0,0])
    if groups != frames or len(starts) != groups:
        raise ValueError('Trainer temporal groups differ')
    vision = tok.convert_tokens_to_ids('<|vision_start|>')
    for k, pos in enumerate(starts,1):
        marker = tok.encode(f'Frame {k}: ', add_special_tokens=False)
        if ids[pos-1] != vision or ids[pos-1-len(marker):pos-1] != marker:
            raise ValueError('Trainer frame marker differs')
    slots = si.get('anchor_slots', list(range(32)))
    positions = batch['aux_camera_positions'][0].tolist()
    if (positions != [ends[k]+1 for k in slots] or len(positions) != 32
            or ids.count(carrier_id(tok)) != 32 or any(ids[k] != carrier_id(tok) for k in positions)
            or any(k >= len(ids) for k in batch['aux_camera_rope_sources'][0].tolist())):
        raise ValueError('Trainer anchor carrier placement differs')
    return dict(groups=groups, markers=list(range(1,groups+1)), carrier_count=32, anchor_slots=slots,
                decoded_rgb_frames=frames, temporal_input_frames=2*frames)


def verify_source(request):
    from student_pilot import p3_provenance as p, carrier_c1_run as trainer
    from .runtime import verify_trainer
    spec = request['direct_trainer']
    verify_trainer(spec)
    root = Path(trainer.__file__).resolve().parent.parent
    inventory = p.load(p.pinned(spec['inventory']))
    if inventory != {str(f.relative_to(root)):sha256(f) for f in root.rglob('*') if f.is_file()}:
        raise ValueError('Direct trainer inventory differs')
    seal = p.load(p.pinned(request['cfg']['code']))
    closure = {str(f.relative_to(root)):sha256(f) for f in p.source_files([Path(trainer.__file__)])}
    if (seal.get('schema') != 'c1-clean-source-v1' or seal.get('clean') is not True
            or seal.get('commit') != spec['commit']
            or seal.get('sources') != spec['closure'] or closure != spec['closure']):
        raise ValueError('Direct trainer config/closure differs')


def native_generate(model, processor, batch):
    """CarrierC1.generate owns prefix embeddings; HF owns the decode/cache."""
    import torch
    from transformers import GenerationConfig
    start = batch['input_ids'].shape[1]
    context = model.config.text_config.max_position_embeddings
    cap = min(16384, context-start)
    if cap < 1:
        raise ValueError('Prompt exhausts context')
    config = GenerationConfig.from_model_config(model.config)
    with torch.no_grad():
        result = model.generate(batch, generation_config=config, do_sample=False, num_beams=1,
            temperature=None, top_p=None, top_k=None, min_p=None, repetition_penalty=1.0,
            length_penalty=1.0, no_repeat_ngram_size=0, min_new_tokens=None,
            early_stopping=False, max_new_tokens=cap, use_cache=True,
            return_dict_in_generate=True, output_scores=False)
    tokens = result.sequences[0,start:].tolist()
    eos = config.eos_token_id
    eos = set(eos if isinstance(eos,(list,tuple)) else [eos])
    finish = 'eos' if tokens and tokens[-1] in eos else ('max_new_tokens' if cap == 16384 else 'context_exhaustion')
    return dict(tokens=tokens, text=processor.tokenizer.decode(tokens,skip_special_tokens=False),
        calls=[], errors=0, finish=finish, prompt_tokens=start, generated_tokens=len(tokens), actual_cap=cap)


def score_views(task, decoded, tokenizer):
    from .run import score_item
    def view(tokens, text, finish, cap):
        scored = score_item(task, dict(text=text,finish=finish))
        scored.pop('_think_text')
        return dict(scored, extracted_answer=scored['response_text'], output_tokens=len(tokens),
                    max_new_tokens=cap, finish_reason=finish)
    main = view(decoded['tokens'],decoded['text'],decoded['finish'],16384)
    short = decoded['tokens'][:4096]
    truncated = len(decoded['tokens']) > 4096
    main['at_4096'] = view(short, tokenizer.decode(short,skip_special_tokens=False),
                          'max_new_tokens' if truncated else decoded['finish'],4096)
    main['at_4096']['truncated'] = truncated
    return main


def record_key(task, model):
    return model+':'+task['benchmark']+':'+task['example_id']


def check_records(records, tasks, specs):
    expected = {record_key(t,s['name']) for t in tasks for s in specs}
    if not set(records) <= expected:
        raise ValueError('Journal contains an item outside its model/shard')
    for key,row in records.items():
        if (key != record_key(row,row['model']) or row.get('status') not in ('complete','error')):
            raise ValueError('Journal item identity/status differs')


def summarize(records, tasks, specs):
    from .official import score_official_vsibench
    expected = {record_key(t,s['name']) for t in tasks for s in specs}
    complete = {k for k,r in records.items() if r.get('status') == 'complete'}
    models = {}
    for spec in specs:
        views = {}
        for view in ('at_16384','at_4096'):
            reports = {}
            for benchmark in ('dev858','vsi500'):
                rows = [({**r,**r.get('at_4096',{})} if view == 'at_4096' else r)
                        for r in records.values() if r['model'] == spec['name'] and r['benchmark'] == benchmark]
                report = score_official_vsibench(rows, expected_count=0)
                report.pop('scored_records')
                report.update(benchmark=benchmark,
                    metric='official EM/MRA on four development types' if benchmark == 'dev858' else report['metric'],
                    completed=sum(r['status']=='complete' for r in rows),
                    expected_count=sum(t['benchmark']==benchmark for t in tasks),
                    hit_token_cap=sum(r.get('hit_token_cap',False) for r in rows),
                    output_tokens=sum(r.get('output_tokens',0) for r in rows))
                reports[benchmark] = report
            views[view] = reports
        models[spec['name']] = views
    coverage = set(records) == expected and complete == expected
    return dict(expected_count=len(expected), completed=len(complete), coverage_complete=coverage,
        errors=sum(r.get('status') != 'complete' for r in records.values()),
        numbers_status='eligible' if coverage else 'do not count', models=models,
        scoring_protocol='official extraction and fuzzy EM/MRA; task macro; at_4096 token-prefix truncation')


def run_worker(request, rank, world_size, device=None):
    import torch
    from student_pilot.carrier_c1_run import move
    from .runtime import load_model
    from .run import append_record, binding_for, read_journal, shard_items, write_json
    validate_request(request)
    verify_source(request)
    device = device or f'cuda:{rank}'
    if torch.device(device).type != 'cuda':
        raise ValueError('GPU worker required')
    torch.cuda.set_device(device)
    output = Path(request['output']); output.mkdir(parents=True,exist_ok=True)
    binding = binding_for(request, world_size)
    with (output/f'worker-{rank}.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        tasks = load_tasks(request); assigned = shard_items(tasks,rank,world_size)
        specs = model_specs(request); journal = output/f'items-{rank}.jsonl'
        records = read_journal(journal,binding); check_records(records,assigned,specs)
        for spec in specs:
            pending = [t for t in assigned if records.get(record_key(t,spec['name']),{}).get('status') != 'complete']
            if not pending:
                continue
            def progress(event):
                append_record(output/f"startup-{rank}-{request['attempt']}.jsonl",
                    dict(event,binding=binding,rank=rank,model=spec['name'],attempt=request['attempt']),durable=True)
            model,processor,info = load_model('routed', request['cfg'], artifact_pin=spec['artifact'],
                snapshot=request['snapshot'],device=device,selected_trainer=request['direct_trainer'],on_stage=progress)
            write_json(output/f"model-{rank}-{spec['name']}-{request['attempt']}.json",info)
            for task in pending:
                started = time.perf_counter()
                record = {k:task[k] for k in ('benchmark','example_id','dataset','scene_name','question_type','ground_truth','options')}
                record.update(key=record_key(task,spec['name']),model=spec['name'],binding=binding,rank=rank,
                    attempt=request['attempt'],status='error',output_tokens=0,extracted_answer='',response_text='',
                    hit_token_cap=False,max_new_tokens=16384,frames=request['frames'])
                try:
                    row = trainer_row(task,request['frame_cache'],request['frames'])
                    batch,audit = encode_prompt(processor,row,request['cfg'],request['frames'])
                    decoded = native_generate(model,processor,move(batch,device))
                    record.update(score_views(task,decoded,processor.tokenizer),status='complete',decode=decoded,
                        encoding=audit,frame_identity=digest(row['student_input']),elapsed_s=time.perf_counter()-started)
                except Exception as exc:
                    record.update(error=f'{type(exc).__name__}: {exc}',elapsed_s=time.perf_counter()-started)
                append_record(journal,record,durable=True); records[record['key']] = record
            del model,processor
        summary = summarize(records,assigned,specs)
        summary.update(binding=binding,rank=rank)
        write_json(output/f"summary-{rank}-{request['attempt']}.json",summary)
        return summary


def merge(request, world_size):
    from .run import binding_for, read_journal, shard_items, write_json
    tasks = load_tasks(request); specs = model_specs(request); binding = binding_for(request,world_size)
    output = Path(request['output']); records = {}
    for rank in range(world_size):
        shard = read_journal(output/f'items-{rank}.jsonl',binding)
        check_records(shard,shard_items(tasks,rank,world_size),specs)
        if set(shard) & set(records):
            raise ValueError('Merged journals contain duplicate items')
        records.update(shard)
    summary = summarize(records,tasks,specs)
    summary.update(binding=binding,protocol_request=request)
    write_json(output/f"summary-{request['attempt']}.json",summary)
    with (output/f"per-item-{request['attempt']}.jsonl").open('x') as stream:
        for key in sorted(records):
            stream.write(json.dumps(records[key],sort_keys=True,allow_nan=False)+'\n')
    return summary
