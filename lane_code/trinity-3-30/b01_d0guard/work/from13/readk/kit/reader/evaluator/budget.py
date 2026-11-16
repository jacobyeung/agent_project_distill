"""Exact token-prefix continuations and resumable, byte-preserving derived journals."""
import asyncio
import json
import time
from pathlib import Path
from evalpath.items import digest
from scoring import score_item
from think_settings import validate

BUDGETS = (2048, 4096)
CLOSE = '\n</think>\n\n'


def close_index(tokenizer, ids):
    closing = tokenizer.encode('</think>', add_special_tokens=False)
    if len(closing) != 1:
        raise ValueError('Require a single </think> token')
    return ids.index(closing[0]) if closing[0] in ids else None


def validate_source(row, cell, binding):
    validate(cell)
    if not cell['thinking'] or row.get('status') != 'complete':
        raise ValueError('Budget source must be complete ON16k')
    for k, v in dict(thinking=True, model=cell['model'], decoding='greedy', frames=32,
                     layout='duplicate', max_new_tokens=16384, binding=binding).items():
        if row.get(k) != v:
            raise ValueError('Budget source protocol differs: '+k)


def generated_ids(tokenizer, source):
    """Recover legacy text only when its stored count and text round-trip agree."""
    ids = source.get('token_ids')
    rebuilt = ids is None
    if rebuilt:
        text = source.get('token_text', source.get('raw_generation'))
        count = source.get('output_tokens')
        if not isinstance(text, str) or type(count) is not int:
            raise ValueError('retokenize_equal=false: legacy row needs text and output_tokens')
        ids = tokenizer.encode(text, add_special_tokens=False)
        if len(ids) != count or tokenizer.decode(ids, skip_special_tokens=False) != text:
            raise ValueError('retokenize_equal=false: legacy text/count mismatch')
    if not isinstance(ids, list) or any(type(i) is not int or i < 0 for i in ids):
        raise ValueError('Invalid generated token_ids')
    if source.get('token_ids_sha256') and digest(ids) != source['token_ids_sha256']:
        raise ValueError('retokenize_equal=false: stored token digest mismatch')
    return ids, rebuilt


def classify(tokenizer, ids, budget):
    close = close_index(tokenizer, ids)
    reuse = close is not None and close < budget
    stopped = close is None and len(ids) < budget
    return dict(forced_close=not reuse and not stopped, stopped_unclosed=stopped,
                think_tokens=close if reuse else min(len(ids), budget))


def continuation(tokenizer, request, ids, budget):
    prefix = ids[:budget]
    decoded = tokenizer.decode(prefix, skip_special_tokens=False)
    equal = tokenizer.encode(decoded, add_special_tokens=False) == prefix
    if not equal:
        raise ValueError('retokenize_equal=false: thinking prefix does not round-trip')
    suffix = tokenizer.encode(CLOSE, add_special_tokens=False)
    # TokensPrompt prevents BPE merges across the budget boundary. The engine still
    # processes the original multimodal placeholders and identical media arguments.
    original = tokenizer.encode(request['prompt'], add_special_tokens=False)
    req = {k:v for k,v in request.items() if k != 'prompt'}
    req['prompt_token_ids'] = original + prefix + suffix
    return req, prefix + suffix


def source_lines(path, *, latest=False, strict=False):
    from journal import records, retain
    rows={};raws={}
    for row,raw in records(path):
        if row.get('status')!='complete':continue
        retain(rows,row)
        raws.setdefault(row['key'],raw)
    return {key:(row,raws[key]) for key,row in rows.items()}


class Journal:
    """Raw rows preserve ON bytes; companion receipts bind every row to its arm."""
    def __init__(self, path, binding, sources):
        self.path = Path(path)
        self.meta = self.path.with_suffix('.meta.jsonl')
        self.binding = binding
        self.sources = sources
        self.done = source_lines(self.path)
        # Receipts use content-addressed keys. An orphan receipt from a crash
        # before its row can coexist with a newly computed receipt for that item.
        candidates=source_lines(self.meta)
        self.receipts={}
        for _,(meta,_) in candidates.items():
            key=meta['source_key']
            if meta['binding'] != binding:
                raise ValueError('Budget resume binding differs')
            if key not in sources or meta['source_sha256'] != digest(sources[key][0]):
                raise ValueError('Budget resume source differs')
            if key in self.done and meta['record_sha256']==digest(self.done[key][1]):
                if key in self.receipts and self.receipts[key][0]!=meta:
                    raise ValueError('Conflicting complete receipt rows: '+key)
                self.receipts[key]=(meta,'')
        for key,(row,raw) in self.done.items():
            if key not in self.receipts:
                raise ValueError('Budget resume receipt differs')

    def write(self, source, record, raw, meta):
        from worker import append
        key = source['key']
        if key in self.done:
            return
        receipt = dict(meta, key=key+':'+digest(raw), source_key=key, binding=self.binding,
                       source_sha256=digest(source), record_sha256=digest(raw), status='complete',
                       score=record['score'], parse_failed=record['parse_failed'],
                       raw_answer=record.get('raw_answer',record['response_text']), frames=32, layout='duplicate')
        # Receipt first: interruption before the row is safe to recompute. A valid
        # row never exists without its binding and immutable-source evidence.
        append(self.meta, receipt)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open('a') as stream:
            stream.write('\n\n' + raw + '\n')
            stream.flush()
            __import__('os').fsync(stream.fileno())
        self.done[key] = (record, raw)
        self.receipts[key] = (receipt, '')


def zero_record(source, cell, binding, meta, exc, stage):
    record = dict(source)
    for name in ('token_ids_sha256', 'token_text'):
        record.pop(name, None)
    record.update(meta, binding=binding, source_key=source['key'], status='complete',
                  thinking=True, model=cell['model'], decoding='greedy', frames=32,
                  layout='duplicate', raw_generation='', raw_answer='', response_text='',
                  scoring_text='', extracted_answer='', extract_branch='derivation_error',
                  score=0.0, parse_failed=True, empty_think=meta['think_tokens'] == 0,
                  hit_token_cap=False, output_tokens=0, max_new_tokens=64, token_ids=[],
                  finish_reason='error', derivation_error=True, error_stage=stage,
                  error_type=type(exc).__name__, error=str(exc)[:2000])
    record['at_4096'] = {k:record[k] for k in ('raw_generation','response_text','score',
        'extracted_answer','extract_branch','parse_failed','empty_think','hit_token_cap',
        'output_tokens','max_new_tokens')}
    return record


async def derive(*, sources, cell, source_binding, request_binding, cell_index, budgets,
                 tokenizer, engine, params, request_for, path_for, inflight=4):
    if params.max_tokens != 64 or params.temperature != 0:
        raise ValueError('Budget continuations require greedy decoding and a 64-token cap')
    if not set(budgets) <= set(BUDGETS) or len(set(budgets)) != len(budgets):
        raise ValueError('Only distinct B2048 and B4096 arms are allowed')
    validate(cell)
    if inflight < 1:
        raise ValueError('inflight must be positive')
    for key, (row, _) in sources.items():
        if row.get('key') != key:
            raise ValueError('Broken source journal key')
    semaphore = asyncio.Semaphore(inflight)
    for budget in budgets:
        binding = digest(dict(request=request_binding, cell=cell_index, budget=budget))
        journal = Journal(path_for(budget), binding, sources)

        async def one(source, source_raw):
            if source['key'] in journal.done:
                return
            async with semaphore:
                meta = dict(arm=f'B{budget}', budget=budget, forced_close=False,
                            stopped_unclosed=False, think_tokens=None, answer_tokens=0,
                            retokenize_equal=None, retokenized_source=False, derivation_error=False)
                stage = 'source'
                try:
                    ids, rebuilt = generated_ids(tokenizer, source)
                    meta.update(classify(tokenizer, ids, budget), retokenized_source=rebuilt)
                    validate_source(source, cell, source_binding)
                    if not meta['forced_close'] and not meta['stopped_unclosed']:
                        meta.update(answer_tokens=len(ids)-meta['think_tokens']-1, retokenize_equal=True,
                                    answer_cap_policy='reuse_full_on_answer')
                        record, raw = source, source_raw
                        # Validate fields used by the receipt before leaving the item guard.
                        source['score']; source['parse_failed']; source['response_text']
                    else:
                        stage = 'request'
                        request, audit = await request_for(source)
                        if audit != source['media']:
                            raise ValueError('Continuation frame-cache receipt differs')
                        if 'prompt_text' in source and request['prompt'] != source['prompt_text']:
                            raise ValueError('Original prompt text differs')
                        stage = 'retokenize'
                        req, tail = continuation(tokenizer, request, ids, budget)
                        meta['retokenize_equal'] = True
                        stage = 'continuation'
                        final = None
                        started = time.monotonic()
                        async for value in engine.generate(req, params, request_id=f'B{budget}:'+source['key']):
                            final = value
                        if final is None:
                            raise RuntimeError('No terminal continuation')
                        if list(final.prompt_token_ids)[-len(tail):] != tail:
                            raise ValueError('Continuation prompt token IDs differ from exact prefix + close')
                        answer = final.outputs[0]
                        answer_ids = list(answer.token_ids)
                        if len(answer_ids) > 64:
                            raise ValueError('Continuation exceeded 64-token answer cap')
                        meta['answer_tokens'] = len(answer_ids)
                        meta['answer_cap_policy'] = 'continuation_64'
                        scoring_text = tokenizer.decode(ids[:budget], skip_special_tokens=False) + CLOSE + answer.text
                        stage = 'score'
                        scored = score_item(source, scoring_text, len(answer_ids), cap=64, finish=answer.finish_reason)
                        record = dict(source)
                        for name in ('at_4096','token_ids_sha256','token_text'):
                            record.pop(name, None)
                        record.update(meta, binding=binding, source_key=source['key'],
                                      raw_generation=answer.text, raw_answer=answer.text, scoring_text=scoring_text,
                                      token_ids=answer_ids, finish_reason=answer.finish_reason,
                                      prompt_tokens=len(final.prompt_token_ids), seconds=time.monotonic()-started,
                                      continuation_suffix_ids=tokenizer.encode(CLOSE, add_special_tokens=False),
                                      **scored)
                        record['at_4096'] = dict(raw_generation=scoring_text, **scored)
                        raw = json.dumps(record, allow_nan=False)
                except Exception as exc:
                    if 'retokenize_equal=false' in str(exc) or stage == 'retokenize':
                        meta['retokenize_equal'] = False
                    meta.update(derivation_error=True, error_stage=stage,
                                error_type=type(exc).__name__, error=str(exc)[:2000])
                    record = zero_record(source, cell, binding, meta, exc, stage)
                    raw = json.dumps(record, allow_nan=False)
                # Persistence errors indicate a broken journal and must fail the run.
                journal.write(source, record, raw, meta)
        await asyncio.gather(*(one(row, raw) for row, raw in sources.values()))
        if set(journal.done) != set(sources):
            raise ValueError('Budget derivation count mismatch')
