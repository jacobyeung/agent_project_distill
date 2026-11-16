"""Step-544 direct read on K1 items (UNCLAIMED: vLLM 0.23.0 on trinity-1-18, not the accepted 0.32.0 runtime).

Protocol copied from the accepted reader (trin_read root .../reader/evaluator): parity.prompt (build_prompt_context 'ours',
thinking on), duplicate layout of the 32 K1 student anchors, media.kwargs, greedy, max_new_tokens 16384, seed 17,
prefix caching off; budget arm B2048 by budget.classify/continuation (force-close after 2048 thinking tokens, 64 answer
tokens); scoring.score_item. Frames come from the K1 capture's student_input PNGs (sha-checked), not the reader cache.
Prompt parity: parity.compare on the first 16 items (pixels on the first 2), as the reader does.
Journal: out/direct/journal.jsonl, one row per item; resume skips complete ids.
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
    done = set()
    if journal.exists():
        done = {json.loads(l)['example_id'] for l in open(journal) if json.loads(l).get('status') == 'complete'}
    todo = [i for i in items if i['id'] not in done]
    llm = LLM(model=a.model, dtype='bfloat16', max_model_len=a.max_model_len, gpu_memory_utilization=0.90,
              max_num_seqs=a.max_seqs, max_num_batched_tokens=8192, tensor_parallel_size=1,
              limit_mm_per_prompt={'video': 1, 'image': 0}, seed=17, enable_prefix_caching=False)
    params = SamplingParams(temperature=0, max_tokens=CELL['max_tokens'])
    close_params = SamplingParams(temperature=0, max_tokens=64)
    probe = SamplingParams(temperature=0, max_tokens=1)
    tasks = [task_for(i) for i in todo]
    t0 = time.monotonic()
    loaded = {}
    reqs = []
    for t in tasks:
        arrays, meta = media(caps[t['capture']])
        loaded[t['example_id']] = (arrays, meta)
        reqs.append(request(processor, t, arrays, meta))
    parity = []
    if not done:
        first = llm.generate(reqs[:16], probe)
        for i, (t, r) in enumerate(zip(tasks[:16], first)):
            arrays, meta = loaded[t['example_id']]
            parity.append(compare(processor, llm.llm_engine, t, arrays, meta, r.prompt_token_ids, pixels=i < 2, cell=CELL))
        (out / 'PARITY.json').write_text(json.dumps(dict(checks=parity, vllm_version=vllm.__version__), default=str) + '\n')
        if not all(c['prompt_equal'] for c in parity) or not all(c['pixels']['pass'] for c in parity if 'pixels' in c):
            raise SystemExit('PARITY FAIL: see PARITY.json')
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
            row.update(status='complete', model=CELL['model'], cell=CELL['name'], vllm_version=vllm.__version__,
                       raw_generation=c.text, token_ids_sha256=hashlib.sha256(json.dumps(ids).encode()).hexdigest(),
                       prompt_tokens=len(o.prompt_token_ids), finish_reason=c.finish_reason)
            row['full'] = score_item(t, c.text, len(ids), cap=CELL['max_tokens'], finish=c.finish_reason)
            meta = classify(tok, ids, BUDGET)
            row['B2048_meta'] = meta
            if meta['forced_close']:
                creq, _ = continuation(tok, r, ids, BUDGET)
                cont_idx.append(j); cont_req.append((creq, ids[:BUDGET]))
                row['B2048'] = None
            else:
                row['B2048'] = row['full']
            rows.append(row)
        if cont_req:
            cres = llm.generate([q for q, _ in cont_req], close_params)
            for j, (q, pre), o in zip(cont_idx, cont_req, cres):
                c = o.outputs[0]
                text = tok.decode(pre, skip_special_tokens=False) + '\n</think>\n\n' + c.text
                rows[j]['B2048'] = score_item(chunk_t[j], text, BUDGET + len(c.token_ids), cap=BUDGET + 64,
                                              finish=c.finish_reason)
                rows[j]['B2048_answer_text'] = c.text
        with open(journal, 'a') as f:
            for row in rows:
                row['score'] = row['B2048']['score']
                row['score_full'] = row['full']['score']
                f.write(json.dumps(row, default=str) + '\n')
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
