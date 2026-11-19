"""B10: compare B=4 with B=1 on eight prompt-only items per routed type.

Run only in an orchestrator-authorized one-A6000 allocation. Input rows use the
native student_input schema (32 hashed RGB frames, their indices/timestamps,
question and options). No label or tool response enters prompt construction.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

import torch

from . import carrier_c1_decode as decode

TYPES = ('object_rel_direction_medium', 'object_rel_direction_hard',
         'object_rel_distance', 'object_abs_distance')


def select_rows(path):
    """Choose the first eight distinct ids per type without inspecting labels."""
    selected = {kind: [] for kind in TYPES}
    seen = set()
    with Path(path).open() as handle:
        for line in handle:
            row = json.loads(line)
            kind = row.get('question_type', row.get('type', (row.get('routing') or {}).get('question_type')))
            if kind not in selected or len(selected[kind]) == 8:
                continue
            qid = str(row.get('qid', row.get('id', '')))
            if not qid or qid in seen:
                raise ValueError('Rows need distinct nonempty qid/id values')
            seen.add(qid)
            inputs = row['student_input']
            allowed = ('frames', 'frame_indices', 'timestamps', 'fps', 'total_num_frames', 'question', 'options',
                       'partner_frames', 'anchor_slots', 'video_sha256')
            clean = {k: inputs[k] for k in allowed if k in inputs}
            required = ('frames', 'frame_indices', 'timestamps', 'fps', 'total_num_frames', 'question')
            if any(k not in clean for k in required) or len(clean['frames']) != 32:
                raise ValueError('Rows require 32 hashed frames and native timing metadata')
            selected[kind].append(dict(qid=qid, question_type=kind, student_input=clean,
                                       routing=dict(category='route', question_type=kind),
                                       **({'reference_trace':row['reference_trace']} if 'reference_trace' in row else {})))
    counts = {kind: len(rows) for kind, rows in selected.items()}
    if any(n != 8 for n in counts.values()):
        raise ValueError(f'Need eight items of each routed type: {counts}')
    # Mixed-type batches exercise different route lengths in the same forward.
    return [selected[kind][i] for i in range(8) for kind in TYPES]


def compare_records(single, batched):
    if len(single) != len(batched):
        raise ValueError('Record counts differ')
    result = []
    for a, b in zip(single, batched):
        index = next((i for i, (x, y) in enumerate(zip(a['tokens'], b['tokens'])) if x != y), None)
        if index is None and len(a['tokens']) != len(b['tokens']):
            index = min(len(a['tokens']), len(b['tokens']))
        result.append(dict(tokens_equal=index is None, first_differing_token=index,
                           text_equal=a['text'] == b['text'], calls_equal=a['calls'] == b['calls'],
                           finish_equal=a['finish'] == b['finish']))
    return result


def benchmark(model, processor, rows, make_batch, *, device, max_new_tokens=16384):
    """Time decoding, including video prefills, tool queries and forced tokens.

    Encode only four CPU prompts at a time. Both arms reuse the same tensors.
    Alternate arm order per group; synchronize CUDA at every timing boundary.
    """
    device = torch.device(device)
    def sync():
        if device.type == 'cuda':
            torch.cuda.synchronize(device)
    from .carrier_c1_run import move
    outputs, seconds, peaks = {1: [], 4: []}, {1: 0., 4: 0.}, {1: 0, 4: 0}
    for start in range(0, len(rows), 4):
        batches = [move(make_batch(row), device) for row in rows[start:start+4]]
        if start == 0:
            # Warm both batch shapes; warmups are excluded from timing.
            decode.generate(model, processor, batches[0], max_new_tokens=max_new_tokens)
            decode.generate(model, processor, batches, max_new_tokens=max_new_tokens)
            sync()
        for size in ((1, 4) if (start // 4) % 2 == 0 else (4, 1)):
            sync()
            if device.type == 'cuda':
                torch.cuda.reset_peak_memory_stats(device)
            begin = time.perf_counter()
            if size == 1:
                records = [decode.generate(model, processor, b, max_new_tokens=max_new_tokens) for b in batches]
            else:
                records = decode.generate(model, processor, batches, max_new_tokens=max_new_tokens)
            sync()
            seconds[size] += time.perf_counter() - begin
            if device.type == 'cuda':
                peaks[size] = max(peaks[size], torch.cuda.max_memory_allocated(device))
            outputs[size].extend(records)
    comparisons = compare_records(outputs[1], outputs[4])
    equal = all(all(r[k] for k in ('tokens_equal', 'text_equal', 'calls_equal', 'finish_equal')) for r in comparisons)
    routed = {size: Counter(row['question_type'] for row, rec in zip(rows, records)
                           if any(call['kind'] in ('ground', 'gap', 'head', 'calculator') for call in rec['calls']))
              for size, records in outputs.items()}
    coverage = all(routed[size][kind] == 8 for size in (1, 4) for kind in TYPES)
    eos = all(rec['finish'] == 'eos' for records in outputs.values() for rec in records)
    report = dict(schema='b10-routed-batch-parity-v1',
        status='PASS' if equal and coverage and eos else 'FAIL', tokens_and_calls_equal=equal,
        eight_routed_per_type=coverage, all_eos=eos,
        items=[dict(qid=row['qid'], question_type=row['question_type'], **comparison)
               for row, comparison in zip(rows, comparisons)],
        arms={str(size): dict(seconds=seconds[size], items_per_hour=len(rows)*3600/seconds[size],
                             peak_cuda_bytes=peaks[size], routed_per_type=dict(routed[size]),
                             emitted_tokens=sum(len(r['tokens']) for r in outputs[size])) for size in (1, 4)},
        speedup=seconds[1]/seconds[4], timing_scope='video prefill + tools + token decode; excludes model load, prompt encoding and warmup',
        device=str(device), device_name=torch.cuda.get_device_name(device) if device.type == 'cuda' else 'CPU',
        torch_version=torch.__version__)
    return report, outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--artifact', required=True)
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--mdg', help='Optional separately exported MDG artifact; omit for an integrated stage-B export')
    parser.add_argument('--rows', required=True, help='Prompt-ready JSONL; eight rows per routed type')
    parser.add_argument('--out', required=True)
    parser.add_argument('--max-new-tokens', type=int, default=16384)
    args = parser.parse_args()
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise SystemExit('Expose exactly one orchestrator-authorized A6000')
    device = torch.device('cuda', 0)
    if 'A6000' not in torch.cuda.get_device_name(device):
        raise SystemExit('B10 throughput requires an A6000')
    if args.max_new_tokens < 16384:
        raise SystemExit('Explicit caps must be at least 16384')
    torch.set_num_threads(1)
    rows = select_rows(args.rows)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    from .p3_provenance import file_pin
    from .carrier_c1_canary import prompt_batch
    from .carrier_c1_routing import tool_mode
    from .mdg_runtime import load_runtime
    cfg = json.loads(Path(args.config).read_text())
    pins = {key: file_pin(getattr(args, key)) for key in ('config', 'artifact', 'bundle', 'rows')}
    if args.mdg:
        from .mdg_eval import load_runtime as load_mdg
        model, processor, _ = load_mdg(pins['config'], pins['artifact'], args.mdg, device, pins['bundle'])
        pins['mdg'] = file_pin(Path(args.mdg) / 'mdg.json')
    else:
        model, processor, _ = load_runtime(dict(c1_config=pins['config'], base_artifact=pins['artifact'], bundle=pins['bundle']), device)
    report, records = benchmark(model, processor, rows,
        lambda row: prompt_batch(processor, tool_mode(row, cfg.get('tool_mode_flag')), cfg),
        device=device, max_new_tokens=args.max_new_tokens)
    report['inputs'] = pins
    report['source_sha256'] = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                               for name in ('carrier_c1_decode.py', 'carrier_c1_batch_decode.py', Path(__file__).name)}
    for size, data in records.items():
        (out / f'b{size}.json').write_text(json.dumps(data) + '\n')
    (out / 'RESULT.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    if report['status'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
