"""Step-544 direct read on K1 items (UNCLAIMED: vLLM 0.23.0 on trinity-1-18, not the accepted 0.32.0 runtime).

Protocol copied from the accepted reader (trin_read root .../reader/evaluator): parity.prompt (build_prompt_context 'ours',
thinking on), duplicate layout of the 32 K1 student anchors, media.kwargs, greedy, max_new_tokens 16384, seed 17,
prefix caching off; budget arm B2048 by budget.classify/continuation (force-close after 2048 thinking tokens, 64 answer
tokens); scoring.score_item. Frames come from the K1 capture's student_input PNGs (sha-checked), not the reader cache.
Prompt parity: parity.compare on the first 16 items (pixels on the first 2), as the reader does.
Journal: out/direct/journal.jsonl, one row per item, each bound (binding sha) to cell, checkpoint files, item and frames;
resume accepts only complete rows with the current binding, repairs a torn final line (kept in journal.torn.<epoch>),
and rejects malformed interior lines. Parity runs on the first 16 selected items on every invocation.
"""
import argparse, hashlib, json, sys, time
from pathlib import Path
import numpy as np

LANE = Path('/scratch/jjyeung/orch_n30/b11_presence')
READER = Path('/scratch/jjyeung/orch_n30/trin_read/root/sj/apb59bef09f3/p/reader/evaluator')
sys.path.insert(0, str(READER))
sys.path.insert(0, str(Path(__file__).parent))
CELL = dict(benchmarks=['k1rows'], decoding='greedy', frames=32, layout='duplicate', max_tokens=16384,
            model='m544', name='k1_direct_m544_vllm023', thinking=True)
BUDGET = 2048


def sha_json(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()


def file_sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 24), b''):
            h.update(b)
    return h.hexdigest()


def model_identity(model):
    """sha256 of every config/tokenizer file and of every weight shard named by the index (contents, not names)."""
    m = Path(model)
    ident = {n: file_sha(m / n) for n in ('config.json', 'model.safetensors.index.json', 'tokenizer.json',
                                          'chat_template.jinja', 'preprocessor_config.json', 'video_preprocessor_config.json')}
    shards = sorted(set(json.loads((m / 'model.safetensors.index.json').read_text())['weight_map'].values()))
    ident.update({n: file_sha(m / n) for n in shards})
    return ident


def binding_for(item, cap, ident):
    return sha_json(dict(cell=CELL, budget=BUDGET, model=ident, item=item, frames=cap['frame_sha256'],
                         frame_indices=cap['frame_indices'], fps=cap['fps'], total=cap['total_num_frames']))


def read_journal(journal):
    """Complete rows by id. A malformed final line is moved aside; a malformed interior line is an error."""
    rows = {}
    if not journal.exists():
        return rows
    raw = journal.read_bytes()
    lines = raw.split(b'\n')
    if lines and lines[-1] == b'':
        lines = lines[:-1]
    good = []
    unterminated = bool(raw) and not raw.endswith(b'\n')
    for i, line in enumerate(lines):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            if i != len(lines) - 1:
                raise SystemExit(f'malformed interior journal line {i + 1} in {journal}')
            torn = journal.with_name(f'journal.torn.{int(time.time())}')
            torn.write_bytes(line)
            tmp = journal.with_suffix('.repair')
            tmp.write_bytes(b''.join(g + b'\n' for g in good))
            import os
            os.replace(tmp, journal)
            print('repaired torn tail ->', torn, flush=True)
            break
        good.append(line)
        if r.get('status') == 'complete':
            rows[r['example_id']] = r
    else:
        if unterminated:
            with open(journal, 'ab') as f:
                f.write(b'\n')
            print('terminated an unterminated final record', flush=True)
    return rows


def task_for(item):
    return dict(benchmark='k1rows', example_id=item['id'], question=item['question'], options=item['options'],
                question_type=item['type'], ground_truth=str(item['answer']), thinking=True,
                capture=item['capture'], room=item['room'], split=item['split'])


def media(cap):
    from scorer import Scorer
    anchors = Scorer.load_frames(cap)
    arrays = np.repeat(anchors, 2, axis=0)
    meta = dict(fps=cap['fps'], frames_indices=[i for i in cap['frame_indices'] for _ in range(2)],
                total_num_frames=cap['total_num_frames'], height=int(arrays.shape[1]), width=int(arrays.shape[2]))
    return arrays, meta


def request(processor, task, arrays, meta):
    from parity import prompt
    from media import kwargs
    return dict(prompt=prompt(processor, task, CELL),
                multi_modal_data={'video': [(arrays, {**meta, 'do_sample_frames': False})]},
                mm_processor_kwargs=kwargs(len(arrays)))


def select(split, types, limit):
    items = [json.loads(l) for l in open(LANE / 'out/prep/ITEMS.jsonl')]
    items = [i for i in items if (split == 'all' or i['split'] == split) and i['type'] in types]
    items.sort(key=lambda i: i['id'])
    return items[:limit] if limit else items


def cpu_check(a):
    """Prompt bytes and token ids: reader prompt + HF processor vs the trainer's own encode (parity.trainer_encode)."""
    from transformers import AutoProcessor
    from transformers.video_utils import VideoMetadata
    from parity import trainer_encode
    from media import kwargs
    processor = AutoProcessor.from_pretrained(a.model, local_files_only=True)
    processor._student_pilot_student = 'qwen35'
    caps = {c['canonical']: c for c in map(json.loads, open(LANE / 'out/prep/CAPTURES.jsonl'))}
    items = select(a.split, a.types.split(','), 0)
    picks = [next(i for i in items if i['type'] == t) for t in a.types.split(',')]
    out = []
    for it in picks:
        task = task_for(it)
        arrays, meta = media(caps[it['capture']])
        req = request(processor, task, arrays, meta)
        hf = processor(text=[req['prompt']], videos=[arrays], video_metadata=[VideoMetadata(**meta)],
                       **kwargs(len(arrays)), return_tensors='pt')
        batch, audit = trainer_encode(processor, task, arrays, meta, CELL)
        exp = batch['input_ids'][0, :audit['prompt_tokens']].tolist()
        out.append(dict(id=it['id'], prompt_tail=req['prompt'][-400:], equal=hf['input_ids'][0].tolist() == exp,
                        tokens=len(exp), grid=hf['video_grid_thw'].tolist()))
        print(json.dumps(out[-1]), flush=True)
    (LANE / 'out/tests').mkdir(parents=True, exist_ok=True)
    (LANE / 'out/tests/DIRECT_CPU_PROMPT.json').write_text(json.dumps(out, indent=1) + '\n')
    print('PASS' if all(o['equal'] for o in out) else 'FAIL')


def gpu_read(a):
    from transformers import AutoProcessor
    from vllm import LLM, SamplingParams
    from parity import compare
    from budget import classify, continuation
    from scoring import score_item
    import vllm
    processor = AutoProcessor.from_pretrained(a.model, local_files_only=True)
    processor._student_pilot_student = 'qwen35'
    tok = processor.tokenizer
    caps = {c['canonical']: c for c in map(json.loads, open(LANE / 'out/prep/CAPTURES.jsonl'))}
    items = select(a.split, a.types.split(','), a.limit)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    journal = out / 'journal.jsonl'
    ident = model_identity(a.model)
    bind = {i['id']: binding_for(i, caps[i['capture']], ident) for i in items}
    prior = read_journal(journal)
    stale = [k for k, r in prior.items() if k in bind and r.get('binding') != bind[k]]
    if stale:
        raise SystemExit(f'{len(stale)} journal rows carry another binding (e.g. {stale[0]}); use a new --out')
    done = {k for k in prior if k in bind}
    todo = [i for i in items if i['id'] not in done]
    llm = LLM(model=a.model, dtype='bfloat16', max_model_len=a.max_model_len, gpu_memory_utilization=0.90,
              max_num_seqs=a.max_seqs, max_num_batched_tokens=8192, tensor_parallel_size=1,
              limit_mm_per_prompt={'video': 1, 'image': 0}, seed=17, enable_prefix_caching=False)
    params = SamplingParams(temperature=0, max_tokens=CELL['max_tokens'])
    close_params = SamplingParams(temperature=0, max_tokens=64)
    probe = SamplingParams(temperature=0, max_tokens=1)
    t0 = time.monotonic()
    ptasks = [task_for(i) for i in items[:16]]
    preqs, parity = [], []
    for t in ptasks:
        arrays, meta = media(caps[t['capture']])
        preqs.append((request(processor, t, arrays, meta), arrays, meta))
    first = llm.generate([q for q, _, _ in preqs], probe)
    for i, (t, (q, arrays, meta), r) in enumerate(zip(ptasks, preqs, first)):
        parity.append(compare(processor, llm.llm_engine, t, arrays, meta, r.prompt_token_ids, pixels=i < 2, cell=CELL))
    del preqs
    ok = all(c['prompt_equal'] for c in parity) and all(c['pixels']['pass'] for c in parity if 'pixels' in c)
    (out / f'PARITY_{time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())}.json').write_text(
        json.dumps(dict(checks=parity, ok=ok, vllm_version=vllm.__version__, model=ident,
                        ids=[t['example_id'] for t in ptasks]), default=str) + '\n')
    if not ok:
        raise SystemExit('PARITY FAIL: see PARITY_*.json')
    tasks = [task_for(i) for i in todo]
    reqs = []
    for t in tasks:
        arrays, meta = media(caps[t['capture']])
        reqs.append(request(processor, t, arrays, meta))
    for s in range(0, len(tasks), a.chunk):
        chunk_t, chunk_r = tasks[s:s + a.chunk], reqs[s:s + a.chunk]
        started = time.monotonic()
        res = llm.generate(chunk_r, params)
        cont_idx, cont_req = [], []
        rows = []
        for j, (t, r, o) in enumerate(zip(chunk_t, chunk_r, res)):
            c = o.outputs[0]
            ids = list(c.token_ids)
            row = {k: v for k, v in t.items()}
            row.update(status='complete', binding=bind[t['example_id']], model=CELL['model'], cell=CELL['name'], vllm_version=vllm.__version__,
                       raw_generation=c.text, token_ids_sha256=hashlib.sha256(json.dumps(ids).encode()).hexdigest(),
                       prompt_tokens=len(o.prompt_token_ids), finish_reason=c.finish_reason)
            row['full'] = score_item(t, c.text, len(ids), cap=CELL['max_tokens'], finish=c.finish_reason)
            meta = classify(tok, ids, BUDGET)
            row['B2048_meta'] = meta
            if meta['forced_close'] or meta['stopped_unclosed']:
                creq, tail = continuation(tok, r, ids, BUDGET)
                cont_idx.append(j); cont_req.append((creq, ids[:BUDGET], tail))
                row['B2048'] = None
            else:
                row['B2048'] = row['full']
            rows.append(row)
        if cont_req:
            cres = llm.generate([q for q, _, _ in cont_req], close_params)
            for j, (q, pre, tail), o in zip(cont_idx, cont_req, cres):
                if list(o.prompt_token_ids)[-len(tail):] != tail:
                    raise SystemExit('Continuation prompt token IDs differ from exact prefix + close: ' + chunk_t[j]['example_id'])
                c = o.outputs[0]
                if len(c.token_ids) > 64:
                    raise SystemExit('continuation exceeded 64 tokens')
                text = tok.decode(pre, skip_special_tokens=False) + '\n</think>\n\n' + c.text
                rows[j]['B2048'] = score_item(chunk_t[j], text, len(c.token_ids), cap=64, finish=c.finish_reason)
                rows[j]['B2048_answer_text'] = c.text
                rows[j]['B2048_meta']['answer_tokens'] = len(c.token_ids)
        with open(journal, 'a') as f:
            for row in rows:
                row['score'] = row['B2048']['score']
                row['score_full'] = row['full']['score']
                f.write(json.dumps(row, default=str) + '\n')
            f.flush()
            import os
            os.fsync(f.fileno())
        print(f'{s + len(rows)}/{len(tasks)} chunk {time.monotonic() - started:.0f}s total {time.monotonic() - t0:.0f}s',
              time.strftime('%H:%M:%SZ', time.gmtime()), flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['cpu-check', 'read'])
    ap.add_argument('--model', default=str(LANE / 'work/model_m544'))
    ap.add_argument('--split', default='heldout')
    ap.add_argument('--types', default='obj_appearance_order,object_counting')
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--chunk', type=int, default=64)
    ap.add_argument('--max-seqs', type=int, default=32)
    ap.add_argument('--max-model-len', type=int, default=24576)
    ap.add_argument('--out', default=str(LANE / 'out/direct'))
    a = ap.parse_args()
    cpu_check(a) if a.mode == 'cpu-check' else gpu_read(a)
