"""User-authorized benchmark diagnostic; targets are not reviewed explanations."""
import argparse
import gc
import json
import os
import random
import re
import socket
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .common import ARTIFACTS, MODEL, REPO, binding, load_json, write_once

OUT = Path('/data2/jjyeung/agent_project_data/student_shakedown_20260918')
FLAGS = dict(benchmark_trained_diagnostic=True, detailed_distillation=False,
             target_type='shakedown_not_reviewed_detailed_explanation', clean_generalization_claim=False)


def now():
    return datetime.now(timezone.utc).isoformat()


def append(path, row):
    with Path(path).open('a') as f:
        f.write(json.dumps(row, allow_nan=False) + '\n')
        f.flush()
        os.fsync(f.fileno())


def heartbeat(step):
    with (OUT / 'HEARTBEAT.log').open('a') as f:
        f.write(f'{now()} | {step}\n')


def sanitize(text, names):
    text = re.sub(r'```.*?```', '', text, flags=re.S)
    text = re.sub(r'`[^`]*`', '', text)
    number = r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?'
    text = re.sub(r'[\[(]\s*' + number + r'\s*,\s*' + number + r'\s*,\s*' + number + r'\s*[\])]', '', text)
    text = re.sub(r'(?:/|\./|~/)[\w./-]+|\b[\w.-]+\.(?:py|json|npy|npz|png|jpg|mp4|txt)\b', '', text)
    for name in sorted(names, key=len, reverse=True):
        text = re.sub(r'\b' + re.escape(name) + r'\b', '', text)
    text = re.sub(r'\b(?:tool|tools|planner)\b', '', text, flags=re.I)
    text = re.sub(r'^.*(?:\bimport\b|\bdef\b|\bprint\s*\(|\w+\s*=|\w+_\w+|\w+\([^)]*\)).*$', '', text, flags=re.M)
    text = re.sub(r'</?ANSWER>.*?(?:</ANSWER>|$)', '', text, flags=re.I)
    return re.sub(r'[ \t]+', ' ', re.sub(r'\n{3,}', '\n\n', text)).strip()


def prepare():
    from .admission import native_final
    from .split import physical_group
    index = load_json(ARTIFACTS / 'data/detailed_audit_v1/index.json')
    packet_pin = index['review_packets']
    binding(packet_pin['path'], packet_pin['sha256'])
    packets = load_json(packet_pin['path'])['rows']
    split = load_json(ARTIFACTS / 'data/split.json')
    heldout_path = ARTIFACTS / 'data/diagnostic_heldout_v1.json'
    heldout = load_json(heldout_path)
    for pin in heldout['bindings'].values(): binding(pin['path'], pin['sha256'])
    rows = []
    exclusions = []
    for packet in packets:
        for pin in packet['sources'].values(): binding(pin['path'], pin['sha256'])
        raw = load_json(packet['sources']['raw']['path'])
        qid = str(packet['qid'])
        scene = raw['scene_name']
        inference = load_json(heldout['bindings']['inference_dataset']['path'])
        item = next(x for x in inference if str(x['id']) == qid)
        group = physical_group(item['dataset'], scene)
        assert qid in split['train_candidate_qids'] and group in split['train_group_ids']
        assert group not in split['heldout_group_ids'] and qid not in split['heldout_qids']
        trace = raw['trace']
        if isinstance(trace, dict): trace = trace['messages']
        summaries = [(i, m['tool_calls'][0]['args']['execution_summary']) for i,m in enumerate(trace)
                     if m.get('tool_calls') and isinstance(m['tool_calls'][0].get('args'), dict)
                     and 'execution_summary' in m['tool_calls'][0]['args']]
        if not summaries:
            exclusions.append(dict(qid=qid, reason="No archived final execution_summary at required pointer"))
            continue
        i, summary = summaries[-1]
        names = {c['name'] for m in trace for c in (m.get('tool_calls') or []) if c.get('name')}
        summary = sanitize(summary, names)
        if not summary:
            exclusions.append(dict(qid=qid, reason="Empty summary after required sanitization"))
            continue
        assert not re.search(r'\b(tool|planner)\b', summary, re.I), qid
        answer = native_final(raw)['native_answer_block']
        answer = re.sub(r'<(/?)answer>', lambda m: '<' + m[1] + 'ANSWER>', answer, flags=re.I)
        inputs = packet['student_input']
        for pin in inputs['frames']: binding(pin['path'], pin['sha256'])
        rows.append(dict(qid=qid, scene=scene, dataset=item['dataset'], group=group,
                         category=item['question_type'], student_input=inputs,
                         answer_only=answer, summary_plus_answer=summary + '\n' + answer,
                         sources=packet['sources'], summary_pointer=f'/trace/{i}/tool_calls/0/args/execution_summary'))
    proof = dict(training_questions=len(rows), training_scenes=len({r['group'] for r in rows}),
                 training_groups=sorted({r['group'] for r in rows}), heldout_groups=split['heldout_group_ids'],
                 scene_intersection=[], qid_intersection=[], heldout_questions=63, heldout_scenes=18,
                 category_counts=dict(Counter(r['category'] for r in rows)))
    write_once(OUT/'data.json', dict(**FLAGS, rows=rows, split_proof=proof, packets=packet_pin,
                                   heldout_manifest=binding(heldout_path)))
    write_once(OUT/'split_proof.json', proof)
    write_once(OUT/'exclusions.json', exclusions)
    write_once(OUT/'heldout.json', {**heldout, **FLAGS})
    print(json.dumps(proof), flush=True)


def runtime_receipt(arm):
    stat = Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(')',1)[1].split()
    result = dict(**FLAGS, arm=arm, host=socket.gethostname(), uid=os.getuid(), pid=os.getpid(),
                  start_ticks=int(stat[19]), started_at=now(), gpu=os.environ['CUDA_VISIBLE_DEVICES'],
                  model=str(MODEL), seed=17, learning_rate=1e-5, microbatch_size=1, effective_batch=1,
                  epochs=3, max_steps=300, greedy=True, max_new_tokens=1024,
                  glue=binding(Path(__file__)))
    write_once(OUT/arm/'runtime.json', result)
    return result


def train(arm):
    import torch
    from transformers import set_seed
    from .adapters import attach_adapters, trainable_groups
    from .batches import load_processor
    from .diagnostic_data import encode_training
    from .runner import load_base, forward_loss, group_gradients, memory_measurement
    started = time.monotonic()
    receipt = runtime_receipt(arm)
    set_seed(17)
    processor = load_processor()
    data = load_json(OUT/'data.json')
    model, report = attach_adapters(load_base())
    write_once(OUT/arm/'adapters.json', report)
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
    groups = trainable_groups(model, report['targets'])
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(params, lr=1e-5, weight_decay=0)
    model.train()
    step = 0
    rng = random.Random(17)
    for epoch in range(3):
        order = list(data['rows']); rng.shuffle(order)
        for row in order:
            if step >= 300: break
            row = {**row, 'target':row[arm]}
            batch, audit = encode_training(processor, row)
            batch = {k:v.to('cuda:0') for k,v in batch.items()}
            optimizer.zero_grad(set_to_none=True)
            loss, logits = forward_loss(model, batch)
            assert torch.isfinite(loss), 'Nonfinite loss'
            loss.backward()
            if step == 0: write_once(OUT/arm/'first_gradients.json', group_gradients(groups))
            norm = torch.nn.utils.clip_grad_norm_(params, 1.0, error_if_nonfinite=True)
            optimizer.step(); step += 1
            record = dict(**FLAGS, step=step, epoch=epoch+1, qid=row['qid'], loss=loss.item(),
                          gradient_norm=float(norm), elapsed_seconds=time.monotonic()-started, timestamp=now(),
                          assistant_tokens=audit['assistant_tokens_including_eos'])
            append(OUT/arm/'loss.jsonl', record); print(json.dumps(record), flush=True)
            del batch, loss, logits
        model.save_pretrained(OUT/arm/f'adapter_epoch{epoch+1}', safe_serialization=True, save_embedding_layers=False)
    result = dict(**receipt, steps=step, final_loss=record['loss'], wall_seconds=time.monotonic()-started,
                  adapter=str(OUT/arm/'adapter_epoch3'), memory=memory_measurement(), completed_at=now())
    write_once(OUT/arm/'training_result.json', result)


def evaluate(arm):
    import torch
    from transformers import set_seed
    from .batches import load_processor
    from .diagnostic import generation_config
    from .diagnostic_data import encode_prompt
    from .runner import load_base
    set_seed(17)
    output = OUT/arm
    processor = load_processor()
    model = load_base()
    if arm != 'base':
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, OUT/arm/'adapter_epoch3', is_trainable=False)
    model.eval(); model.requires_grad_(False)
    model.config.use_cache = True; model.config.text_config.use_cache = True
    config = generation_config(model.generation_config, processor, 1024)
    write_once(output/'generation_config.json', config.to_dict())
    manifest = load_json(OUT/'heldout.json')
    assert len(manifest['rows']) == 63
    for row in manifest['rows']:
        trace = dict(**FLAGS, qid=row['qid'], question_id=row['qid'], category=row['category'], arm=arm,
                     frame_hashes=row['student_input']['frames'] if row['student_input'] else [],
                     parsed_answer=None, raw_generation=None, status='error', timestamp=now())
        try:
            if row['student_input'] is None: raise ValueError(row.get('media_failure','Original_RGB_source_admission_failed'))
            batch,audit = encode_prompt(processor,row)
            batch = {k:v.to('cuda:0') for k,v in batch.items()}
            with torch.inference_mode(): generated = model.generate(**batch,generation_config=config)
            tokens = generated.sequences[0,audit['prompt_tokens']:].cpu().tolist()
            text = processor.tokenizer.decode(tokens,skip_special_tokens=True)
            answers = re.findall(r'<answer>(.*?)</answer>',text,re.I|re.S)
            trace.update(status='ok',raw_generation=text,raw_generation_with_special_tokens=processor.tokenizer.decode(tokens,skip_special_tokens=False),
                         parsed_answer=answers[-1].strip() if answers else None,generated_tokens=len(tokens),
                         generated_token_ids=tokens,input_audit=audit,
                         trace={'messages':[{'role':'ai','content':text,'tool_calls':[]}]})
            del batch,generated
        except (ValueError,OSError,RuntimeError) as e:
            trace.update(error=str(e),error_type=type(e).__name__)
            torch.cuda.empty_cache()
        append(output/'generations.jsonl',trace)
        print(json.dumps({k:trace[k] for k in ('qid','arm','status')}),flush=True)
        gc.collect()
    write_once(output/'evaluation_complete.json',dict(**FLAGS, arm=arm,questions=63,completed_at=now()))


def score():
    from .admission import authorities,load_scorer,resolve_answer_key
    from .diagnostic_data import score_trace
    contract,_,_,_ = authorities()
    scorer,pins = load_scorer(contract)
    key = resolve_answer_key()
    heldout = load_json(OUT/'heldout.json')
    labels = {str(x['id']):x for x in load_json(key['path']) if str(x['id']) in heldout['heldout_qids']}
    assert len(labels)==63
    reports = {}
    for arm in ('base','answer_only','summary_plus_answer'):
        path = OUT/arm/'generations.jsonl'
        if not (OUT/arm/'evaluation_complete.json').exists():continue
        traces = [json.loads(x) for x in path.read_text().splitlines()]
        assert len(traces)==63 and {x['qid'] for x in traces} == set(labels)
        records=[]; cats={}
        for trace in traces:
            record,full = score_trace(trace,labels[trace['qid']],scorer)
            records.append(record)
            cat = cats.setdefault(trace['category'],dict(count=0,credit=0,full_credit=0,generated=0))
            cat['count']+=1;cat['credit']+=record.get('accuracy',record.get('MRA',0));cat['full_credit']+=int(full);cat['generated']+=int(trace['status']=='ok')
        report=dict(**FLAGS,arm=arm,scorer=pins,cohort_size=63,mean_final_answer_credit=sum(r.get('accuracy',r.get('MRA',0)) for r in records)/63,
                    per_category=cats,pinned_summary=dict(scorer.aggregate_records(records)),records=records,
                    raw_generations=binding(path),generated=sum(t['status']=='ok' for t in traces))
        write_once(OUT/arm/'score.json',report);reports[arm]=report
    write_once(OUT/f'comparison_{len(reports)}arms.json',reports)
    print(json.dumps({a:{k:r[k] for k in ('mean_final_answer_credit','generated','per_category')} for a,r in reports.items()}),flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','train','evaluate','score']);p.add_argument('--arm')
    a=p.parse_args()
    if a.mode=='prepare':prepare()
    elif a.mode=='train':train(a.arm)
    elif a.mode=='evaluate':evaluate(a.arm)
    else:score()
