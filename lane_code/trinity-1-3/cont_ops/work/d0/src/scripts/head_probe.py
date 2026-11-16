"""Teacher-forced readout of the student's perception heads on packed prompts.

Each probe row appends a think prefix to the exact packed prompt ids; the value
after every query token in that prefix is ground truth. One forward per
question reads the matching head at each query position. When the checkpoint
has count or object heads, the same forward also reads them for each named
category span of the question. Output: one JSONL record per question and a
summary of accuracy by kind.

Probe file (JSONL), one row per qid:
  {"qid": str, "prefix": str (alias "think_prefix"),
   "categories": [{"name": str, "span": [start, end] (optional; else the first
                   case-insensitive match in the question), "group_count": [16]
                   (optional GT), "group_count_mask": [16] (optional),
                   "scene_count": number (optional GT), "object": [6] (optional GT:
                   centroid xyz m, log extent xyz)}]  (optional)}

Summary: COUNT exact and within-one rates; TIME temporal-group hit rate;
DIST/SIZE/DEPTH mean relative accuracy over thresholds 0.50:0.05:0.95 and
median relative error; ANGLE median absolute error in degrees and label
agreement, where the label is the 90-degree sector (front |a| <= 45, left
45 < a <= 135, right -135 <= a < -45, back otherwise; counterclockwise is
positive, so left is positive), plus left/right side agreement; COORD mean and
median absolute error in meters, the rate within 0.5 m, and sign agreement where
the ground truth is at least 0.1 m from zero.
"""
import argparse
import json
import math
import statistics
import sys
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS.parent))
sys.path.insert(0, str(SCRIPTS))

import reason_generate as shared  # noqa: E402
from student_pilot import auxiliary_reason as reason  # noqa: E402

THRESHOLDS = [0.50 + 0.05 * step for step in range(10)]
METRIC_KINDS = ('DIST', 'SIZE', 'DEPTH')


def category_spans(question, categories):
    """Explicit spans, else the first case-insensitive occurrence of the name; None when absent."""
    spans = []
    for category in categories:
        span = category.get('span')
        if span is None:
            start = question.lower().find(category['name'].lower())
            span = [start, start + len(category['name'])] if start >= 0 and category['name'] else None
        spans.append(span)
    return spans


def probe(heads, hidden, view, prompt_length, table, times, categories=(), category_tokens=(),
          video_token_id=None, merge_size=None):
    """Pure readout from the final-norm states [1,L,H] of one teacher-forced sequence."""
    import torch

    with torch.no_grad():
        return readout(heads, hidden, view, prompt_length, table, times, categories, category_tokens,
                       video_token_id, merge_size)


def readout(heads, hidden, view, prompt_length, table, times, categories, category_tokens, video_token_id, merge_size):
    import torch
    from student_pilot.auxiliary_losses import category_queries, video_features

    ids = view['input_ids'][0].tolist()
    labels = [reason.IGNORE] * prompt_length + ids[prompt_length:]
    found = reason.parse_tokens(ids, labels, table)
    features, tokens, token_mask = video_features(hidden, view, video_token_id, merge_size, tokens=True)
    frames = features.float().mean(dim=(2, 3))
    queries = []
    if found and heads.has_reason:
        positions = torch.tensor([[position for position, *_ in found]], device=hidden.device)
        outputs, scores = heads.reason_outputs(hidden, frames, positions)
        for q, (position, kind_id, value, _) in enumerate(found):
            kind = reason.KINDS[kind_id]
            text = heads.format(kind, outputs[0, q], scores[0, q], times)
            entry = {'kind': kind, 'gt': value, 'pred': float(text), 'pred_text': text, 'position': position}
            if kind == 'TIME':
                entry.update(gt_group=reason.time_class(value, times), pred_group=int(scores[0, q].argmax()))
            queries.append(entry)
    elif found:
        queries = [{'kind': reason.KINDS[kind_id], 'gt': value, 'pred': None, 'position': position,
                    'skipped': 'checkpoint has no query-token heads'} for position, kind_id, value, _ in found]
    readings = []
    if categories and (hasattr(heads, 'count_group') or hasattr(heads, 'object')):
        mask = torch.zeros(1, len(categories), hidden.shape[1], dtype=torch.bool, device=hidden.device)
        for slot, positions in enumerate(category_tokens):
            if positions:
                mask[0, slot, positions] = True
        query, present = category_queries(hidden, mask)
        if hasattr(heads, 'count_group'):
            group, scene = heads.count_outputs(frames, query)
        if hasattr(heads, 'object'):
            placed = heads.object_readout(tokens, token_mask, query)
        for slot, category in enumerate(categories):
            entry = {'name': category['name'], 'span': category.get('span')}
            if not bool(present[0, slot]):
                entry['skipped'] = 'category name not found in the question tokens'
                readings.append(entry)
                continue
            if hasattr(heads, 'count_group'):
                entry['group_count_pred'] = torch.expm1(group[0, slot, :, 0]).clamp_min(0).tolist()
                entry['scene_count_pred'] = float(torch.expm1(scene[0, slot, 0]).clamp_min(0))
            if hasattr(heads, 'object'):
                values = placed[0, slot].tolist()
                entry['object_pred'] = {'centroid_m': values[:3], 'log_extent': values[3:],
                                        'extent_m': [math.exp(min(v, 50.0)) for v in values[3:]]}
            for key in ('group_count', 'group_count_mask', 'scene_count', 'object'):
                if key in category:
                    entry[key] = category[key]
            readings.append(entry)
    return {'queries': queries, 'categories': readings}


def angle_error(pred, gt):
    return abs((pred - gt + 180.0) % 360.0 - 180.0)


def angle_label(degrees):
    degrees = (degrees + 180.0) % 360.0 - 180.0
    if abs(degrees) <= 45:
        return 'front'
    if 45 < degrees <= 135:
        return 'left'
    if -135 <= degrees < -45:
        return 'right'
    return 'back'


def angle_side(degrees):
    degrees = (degrees + 180.0) % 360.0 - 180.0
    return 'left' if 0 < degrees < 180 else 'right' if -180 < degrees < 0 else None


def relative_accuracy(pred, gt):
    error = abs(pred - gt) / gt
    return sum(error < 1 - threshold for threshold in THRESHOLDS) / len(THRESHOLDS)


def rate(values):
    return sum(values) / len(values) if values else None


def summarize(records):
    entries = [q for record in records for q in record.get('queries', []) if q.get('pred') is not None]
    by_kind = {kind: [q for q in entries if q['kind'] == kind] for kind in reason.KINDS}
    summary = {'questions': len(records), 'errors': sum('error' in record for record in records), 'kinds': {}}
    count = by_kind['COUNT']
    summary['kinds']['COUNT'] = {'n': len(count), 'exact': rate([q['pred'] == q['gt'] for q in count]),
                                 'within_1': rate([abs(q['pred'] - q['gt']) <= 1 for q in count])}
    timing = by_kind['TIME']
    summary['kinds']['TIME'] = {'n': len(timing), 'group_hit': rate([q['pred_group'] == q['gt_group'] for q in timing])}
    for kind in METRIC_KINDS:
        usable = [q for q in by_kind[kind] if q['gt'] > 0]
        errors = [abs(q['pred'] - q['gt']) / q['gt'] for q in usable]
        summary['kinds'][kind] = {'n': len(usable), 'excluded_zero_gt': len(by_kind[kind]) - len(usable),
                                  'mean_relative_accuracy': rate([relative_accuracy(q['pred'], q['gt']) for q in usable]),
                                  'median_relative_error': statistics.median(errors) if errors else None}
    turns = by_kind['ANGLE']
    sides = [q for q in turns if angle_side(q['gt']) is not None]
    summary['kinds']['ANGLE'] = {'n': len(turns),
                                 'median_abs_error_deg': statistics.median([angle_error(q['pred'], q['gt']) for q in turns]) if turns else None,
                                 'label_agreement': rate([angle_label(q['pred']) == angle_label(q['gt']) for q in turns]),
                                 'side_agreement': rate([angle_side(q['pred']) == angle_side(q['gt']) for q in sides])}
    offsets = by_kind['COORD']
    errors = [abs(q['pred'] - q['gt']) for q in offsets]
    signed = [q for q in offsets if abs(q['gt']) >= 0.1]
    summary['kinds']['COORD'] = {'n': len(offsets), 'mean_abs_error_m': rate(errors),
                                 'median_abs_error_m': statistics.median(errors) if errors else None,
                                 'within_0.5m': rate([error <= 0.5 for error in errors]),
                                 'sign_agreement': rate([(q['pred'] > 0) == (q['gt'] > 0) for q in signed])}
    readings = [c for record in records for c in record.get('categories', []) if 'skipped' not in c]
    scenes = [c for c in readings if 'scene_count' in c and 'scene_count_pred' in c]
    groups = [(p, g) for c in readings if 'group_count' in c and 'group_count_pred' in c
              for p, g, m in zip(c['group_count_pred'], c['group_count'], c.get('group_count_mask', [True] * 16)) if m]
    objects = [c for c in readings if 'object' in c and 'object_pred' in c]
    summary['categories'] = {
        'n': len(readings),
        'scene_count': {'n': len(scenes), 'exact': rate([round(c['scene_count_pred']) == c['scene_count'] for c in scenes]),
                        'within_1': rate([abs(round(c['scene_count_pred']) - c['scene_count']) <= 1 for c in scenes])},
        'group_count_mae': rate([abs(p - g) for p, g in groups]),
        'object': {'n': len(objects),
                   'median_centroid_error_m': statistics.median([math.dist(c['object_pred']['centroid_m'], c['object'][:3])
                                                                 for c in objects]) if objects else None,
                   'median_log_extent_error': statistics.median([abs(p - g) for c in objects
                                                                 for p, g in zip(c['object_pred']['log_extent'], c['object'][3:])])
                   if objects else None}}
    return summary


def read_states(model, feed, ids):
    """One teacher-forced forward; returns the final language-norm states [1,L,H]."""
    import torch
    from student_pilot.auxiliary_losses import final_norm

    batch = shared.sequence_feed(feed, ids)
    captured = []
    handle = final_norm(model).register_forward_hook(lambda module, args, output: captured.append(output))
    try:
        with torch.inference_mode():
            model(**batch, logits_to_keep=1, use_cache=False, return_dict=True)
    finally:
        handle.remove()
    if len(captured) != 1:
        raise ValueError('The forward must run the final norm exactly once')
    view = {**batch, 'labels': torch.full_like(batch['input_ids'], -100)}
    return captured[0], view


def load_results(out):
    return [json.loads(line) for path in sorted(Path(out).glob('results_*.jsonl')) for line in open(path) if line.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pack', required=True)
    ap.add_argument('--probe', required=True)
    ap.add_argument('--cohort_dir', required=True)
    ap.add_argument('--adapter', required=True, help='trainer checkpoint adapters.pt or a published PEFT adapter directory')
    ap.add_argument('--heads', default='', help='auxiliary_heads.pt (settings from the sibling .json)')
    ap.add_argument('--head-settings', default='', help='run.json or auxiliary_heads.json when heads come from adapters.pt')
    ap.add_argument('--snapshot', default='')
    ap.add_argument('--lora-config', default='')
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--shards', type=int, default=1)
    ap.add_argument('--out', required=True)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--summary-only', action='store_true', help='summarize every results_*.jsonl already in --out')
    args = ap.parse_args()
    out = Path(args.out)
    if args.summary_only:
        (out / 'summary.json').write_text(json.dumps(summarize(load_results(out)), indent=1) + '\n')
        return
    shared.setup_env()
    import glob
    import torch
    from transformers import AutoProcessor
    from student_pilot.auxiliary_targets import category_positions

    torch.manual_seed(17)
    probes = {}
    for line in open(args.probe):
        if line.strip():
            item = json.loads(line)
            probes[str(item['qid'])] = item
    rows = [json.loads(line) for line in open(args.pack) if line.strip()]
    rows = [r for r in rows if str(r['qid']) in probes]
    rows = [r for i, r in enumerate(rows) if i % args.shards == args.shard]
    if args.limit:
        rows = rows[:args.limit]
    out.mkdir(parents=True, exist_ok=True)
    res_path = out / f'results_{args.shard:02d}.jsonl'
    done = {json.loads(line)['qid'] for line in open(res_path) if line.strip()} if res_path.exists() else set()
    snapshot = Path(args.snapshot) if args.snapshot else shared.first_match('models/models--*/snapshots/*')
    processor = AutoProcessor.from_pretrained(str(snapshot), local_files_only=True)
    tok = processor.tokenizer
    model, head_weights = shared.load_model(args)
    heads = shared.load_heads(args, model, head_weights, tok, require_reason=False)
    table = heads.reason_table or reason.token_table(tok)
    settings = model.get_base_model().config if hasattr(model, 'get_base_model') else model.config
    cohort_dir = Path(sorted(glob.glob(args.cohort_dir))[0])
    with open(res_path, 'a') as w:
        for row in rows:
            if row['qid'] in done:
                continue
            t0 = time.time()
            item = probes[str(row['qid'])]
            rec = {'qid': row['qid'], 'type': row.get('type')}
            try:
                feed, check = shared.build_inputs(processor, row, cohort_dir)
                rec['check'] = check
                if not check['ids_match']:
                    raise ValueError('Processor prompt ids differ from the packed prompt ids')
                prompt_ids = row['input_token_ids']
                prefix = item.get('prefix', item.get('think_prefix', ''))
                ids = prompt_ids + tok.encode(prefix, add_special_tokens=False)
                categories = [dict(c) for c in item.get('categories', [])]
                spans = category_spans(row['question'], categories)
                positions = []
                for category, span in zip(categories, spans):
                    category['span'] = span
                    positions.append(category_positions(tok, prompt_ids, row['question'], [span])[0] if span else [])
                hidden, view = read_states(model, feed, ids)
                rec.update(probe(heads, hidden, view, len(prompt_ids), table, shared.group_times(tok, prompt_ids, row),
                                 categories, positions, settings.video_token_id, settings.vision_config.spatial_merge_size))
            except Exception as exc:  # recorded, never retried silently
                rec.update(error=f'{type(exc).__name__}: {exc}')
            rec['seconds'] = round(time.time() - t0, 2)
            w.write(json.dumps(rec) + '\n')
            w.flush()
    results = [json.loads(line) for line in open(res_path) if line.strip()]
    (out / f'summary_{args.shard:02d}.json').write_text(json.dumps(summarize(results), indent=1) + '\n')
    (out / f'DONE_{args.shard:02d}').write_text('ok\n')


if __name__ == '__main__':
    main()
