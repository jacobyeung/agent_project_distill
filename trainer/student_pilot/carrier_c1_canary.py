"""Routing canaries on held-out traces with the production decode loop (SELF_ROUTING_DESIGN 3).

C1 call validity and route/direct policy, C2 injected bytes = shared-layer replay and
prefix readout parity, C3 donor shuffle (different-video head outputs), C7 termination,
and answer agreement with the trace label. Pointing (C4a), VSI-500 (C5) and head_acc
(C6) have their own jobs. One report per milestone artifact.
"""
import argparse
import json
import re
from pathlib import Path

import torch

from . import carrier_c1_data as data
from . import carrier_c1_decode as decode
from . import carrier_c1_routing as routing
from .p3_provenance import load, pinned, write


def prompt_batch(processor, row, cfg):
    """Prompt-only native batch (video, carriers, question, generation prompt ending `<think>\\n`)."""
    layout, gap = data.layout_settings(cfg)
    batch, _, _ = data.encode(processor, {**row, 'target': data.READOUT_TARGET}, {}, 'vqa', cfg['carrier_placement'],
                              'final', layout, gap, **(dict(geometry_online=cfg['geometry_online'])
                                                       if cfg.get('geometry_online') else {}))
    start = int(torch.where(batch['labels'][0] != -100)[0][0])
    return {k: (v[:, :start] if k in ('input_ids', 'attention_mask', 'mm_token_type_ids') else v)
            for k, v in batch.items() if k != 'labels'}


def answer_of(text):
    tail = text.split('</think>')[-1]
    lines = [line.strip() for line in re.sub(r'<\|[^|]*\|>', '', tail).strip().splitlines() if line.strip()]
    return lines[-1] if lines else None


def agree(predicted, label):
    if predicted is None:
        return False
    try:
        a, b = float(predicted), float(label)
        return abs(a - b) <= .1 * max(abs(b), 1e-9) if b else a == 0
    except ValueError:
        return predicted.strip().rstrip('.').upper() == str(label).strip().upper()


def summarize(records):
    route = [r for r in records if r['category'] == 'route' and r['gt_calls']]
    calls = [c for r in records for c in r['own']['calls']]
    n = max(len(records), 1)
    return dict(
        items=len(records),
        c1_route_rows_with_calls=sum(bool(r['own']['calls']) for r in route) / max(len(route), 1),
        c1_parse_valid_calls=sum(c['kind'] != 'error' for c in calls) / max(len(calls), 1),
        # Agreement: the generation uses head/calculator calls exactly when the trace form does.
        c1_policy_agreement=sum(bool(r['own']['calls']) == r['gt_calls'] for r in records) / n,
        c2_byte_equal=sum(r['replay']['byte_equal'] for r in records) / n,
        c2_max_readout_diff=max([r['readout_diff'] for r in records] + [0.]),
        c3_answer_change_under_shuffle=(sum(r['shuffle_changed'] for r in records if r.get('shuffle_changed') is not None)
                                        / max(sum(r.get('shuffle_changed') is not None for r in records), 1)),
        c7_bad_termination=sum(r['own']['finish'] != 'eos' or len(r['own']['calls']) > 20 or r['answer'] is None
                               for r in records) / n,
        answer_agreement=sum(r['agree'] for r in records) / n,
        errors_per_item=sum(r['own']['errors'] for r in records) / n)


def run(cfg, artifact_pin, heldout_pin, report_path, device, limit=None, shuffle=True):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('student_pilot/carrier_c1_canary.py:run')
    from .carrier_c1_run import connect, inference, move
    model, processor, receipt, artifact = inference(cfg, artifact_pin, device)
    heldout = load(pinned(heldout_pin))
    if heldout.get('schema') != routing.ROUTING_SCHEMA or heldout.get('scene_role') != 'heldout':
        raise ValueError('Canaries need a held-out routing stream receipt')
    with connect(heldout['database']) as conn:
        rows = [json.loads(r) for (r,) in conn.execute('SELECT row FROM rows ORDER BY i')]
    rows = rows[:limit] if limit else rows
    records = []
    rows = [routing.tool_mode(row, cfg.get('tool_mode_flag')) for row in rows]
    for i, row in enumerate(rows):
        batch = move(prompt_batch(processor, row, cfg), device)
        own = decode.generate(model, processor, batch, max_new_tokens=16384)
        with torch.no_grad():
            readout = model(batch, {'uv': torch.full((32, 25, 2), 500., device=device)}, stream='readout')
        diff = float((readout['pose'][0].double().cpu() - torch.tensor(own['heads']['pose9'])).abs().max())
        answer = answer_of(own['text'])
        record = dict(qid=row['qid'], question_type=row['routing']['question_type'],
                      category=row['routing']['category'], gt_calls=bool(row['routing']['tool_output_spans']),
                      label=row['routing']['answer'], answer=answer, agree=agree(answer, row['routing']['answer']),
                      own=own, replay=decode.replay(own), readout_diff=diff)
        if shuffle:
            donor = next((r for r in rows[i+1:] + rows[:i] if r['scene'] != row['scene']), None)
            if donor is not None:
                shuffled = decode.generate(model, processor, batch, mode='shuffle', max_new_tokens=16384,
                                           donor_batch=move(prompt_batch(processor, donor, cfg), device))
                record.update(donor=donor['qid'], shuffle_answer=answer_of(shuffled['text']),
                              shuffle_changed=answer_of(shuffled['text']) != answer, shuffle_calls=len(shuffled['calls']))
        records.append(record)
    report = dict(schema='c1-routing-canary-v1', artifact=artifact_pin, heldout=heldout_pin,
                  step=artifact.get('step'), summary=summarize(records), records=records,
                  expectations=dict(c3_answer_change_under_shuffle=(
                      'not expected in v1: own-valued rows keep GT-authored text and answers, so the model is not '
                      'trained to follow printed values; launch-blocking for the final run once the faithful '
                      'materializer lands')),
                  scope='production decode loop; diagnostic only; no benchmark claim')
    write(Path(report_path), report)
    return report['summary']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--artifact', required=True, help='JSON pin of m<step>/artifact.json')
    parser.add_argument('--heldout', required=True, help='JSON pin of a held-out routing stream receipt')
    parser.add_argument('--report', required=True)
    parser.add_argument('--limit', type=int)
    parser.add_argument('--no-shuffle', action='store_true')
    args = parser.parse_args()
    device = torch.device('cuda', 0) if torch.cuda.is_available() else torch.device('cpu')
    if device.type == 'cuda':
        torch.cuda.set_device(0)
    cfg = json.loads(Path(args.config).read_text())
    print(json.dumps(run(cfg, json.loads(args.artifact), json.loads(args.heldout), args.report, device,
                         args.limit, not args.no_shuffle), indent=1))


if __name__ == '__main__':
    main()
