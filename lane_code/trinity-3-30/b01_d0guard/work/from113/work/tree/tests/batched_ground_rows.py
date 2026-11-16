"""Replay eight archived v3.12.2 rows per type through B=1 and B=4.

The real tokenizer and production decode scheduler run. Model numerics and tool
bodies are stubbed with archived values. This proves insertion bytes and per-row
scheduling, not model accuracy, native numeric parity or GPU throughput.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

import numpy as np
import torch
from transformers import PreTrainedTokenizerFast
from transformers.cache_utils import DynamicCache

from student_pilot import carrier_c1_decode as D
from student_pilot.carrier_c1_routing import add_routing_tokens
from student_pilot.carrier_c1_batch_benchmark import TYPES, compare_records


def run(rows_path, tokenizer_path):
    chosen = {kind: [] for kind in TYPES}
    for line in Path(rows_path).read_text().splitlines():
        row = json.loads(line)
        if row['type'] in chosen and len(chosen[row['type']]) < 8:
            chosen[row['type']].append(row)
    counts = {kind: len(rows) for kind, rows in chosen.items()}
    if any(n != 8 for n in counts.values()):
        raise ValueError(f'Need eight per routed type: {counts}')
    rows = [chosen[kind][i] for i in range(8) for kind in TYPES]
    tokenizer = PreTrainedTokenizerFast(tokenizer_file=str(tokenizer_path))
    processor = NS(tokenizer=tokenizer)
    add_routing_tokens(processor, include_ground=True)
    tokenizer.eos_token_id = tokenizer.convert_tokens_to_ids('<|im_end|>')
    model = NS(training=False, carrier_id=5, model=NS(rope_deltas=None))
    native = NS(generation_config=NS(eos_token_id=tokenizer.eos_token_id))
    logits = torch.zeros(1, 1, len(tokenizer))
    batches = [dict(input_ids=torch.full((1, 5+i%4), 6), attention_mask=torch.ones((1, 5+i%4), dtype=torch.long),
                    oracle=row) for i, row in enumerate(rows)]
    def prepare(model, processor, batch, **kwargs):
        length = batch['input_ids'].shape[1]
        cache = DynamicCache([(torch.zeros(1, 1, length, 1), torch.zeros(1, 1, length, 1))])
        heads = NS(pose9=np.zeros((32, 9)), gravity=None, queries=[], grounding_head=None,
                   mdg_backend=NS(query=lambda name: None, gap=None, queries=[], gap_queries=[], query_passes=[]))
        model.model.rope_deltas = torch.zeros(1, 1, dtype=torch.long)
        return NS(native=native, output=NS(logits=logits, past_key_values=cache), heads=heads,
                  geometry=iter(batch['oracle']['events']), geometry_error=None, prompt_length=length,
                  cap=32768-length, tokenizer=tokenizer, openers=set(processor._routing_tokens['ids'].values()),
                  mdg=True, stream=None, ground_backend=None, rereader=None, verify_session=None, tool_context=NS())
    def respond(call, registry, events, *args):
        event = next(events)
        assert event['call'] == call, (event['call'], call)
        text = event['response']
        assert text.startswith('<tool_response>\n') and text.endswith('\n</tool_response>')
        kind = 'ground' if call.startswith('<ground') else 'gap' if call.startswith('<gap') else 'calculator'
        return text[len('<tool_response>\n'):-len('\n</tool_response>')], dict(kind=kind)
    def consume(native, ids, attention, cache, **kwargs):
        n = ids.shape[1] - cache.get_seq_length()
        value = torch.zeros(ids.shape[0], 1, n, 1)
        cache.update(value, value.clone(), 0)
        return NS(logits=logits.expand(ids.shape[0], -1, -1), past_key_values=cache), cache
    targets = [tokenizer.encode(r['suffix'], add_special_tokens=False) + [tokenizer.eos_token_id] for r in rows]
    def force(expected):
        def select(ids, values):
            assert ids == expected[:len(ids)], ('injected prefix differs', len(ids))
            return NS(argmax=lambda dim: torch.tensor(expected[len(ids)]))
        return select
    with mock.patch.object(D, '_prepare_decode', side_effect=prepare), \
         mock.patch.object(D, 'respond', side_effect=respond), mock.patch.object(D, 'consume_cache_tokens', side_effect=consume):
        single = [D.generate(model, processor, b, logits_processor=force(target)) for b, target in zip(batches, targets)]
        batched = []
        for start in range(0, 32, 4):
            batched.extend(D.generate(model, processor, batches[start:start+4],
                                     logits_processor=[force(t) for t in targets[start:start+4]]))
    assert [r['tokens'] for r in single] == targets
    assert single == batched
    report = dict(status='PASS', items=32, per_type=counts, records_equal=True,
                  tokenizer_sha256=hashlib.sha256(Path(tokenizer_path).read_bytes()).hexdigest(),
                  rows_sha256=hashlib.sha256(Path(rows_path).read_bytes()).hexdigest(),
                  scope='archived-row token replay with stubbed model numerics and tool bodies',
                  items_detail=[dict(qid=row['qid'], type=row['type'], **comparison)
                                for row, comparison in zip(rows, compare_records(single, batched))])
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rows', required=True)
    parser.add_argument('--tokenizer', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    report = run(args.rows, args.tokenizer)
    Path(args.out).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'items_detail'}, indent=2))


if __name__ == '__main__':
    main()
