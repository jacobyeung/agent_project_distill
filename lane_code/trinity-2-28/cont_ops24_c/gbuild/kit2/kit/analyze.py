"""Inventory the two routed reads without mistaking diagnostics for GT identity."""
import gzip
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from funnel import summarize, sample_indices

ROOT = Path(__file__).resolve().parents[1]


def load(step):
    with gzip.open(ROOT / ('work/step%d.jsonl.gz' % step), 'rt') as f:
        return [json.loads(x) for x in f]


def names(question):
    text = question.strip().rstrip('?.')
    text = re.sub(r'\s*\([^)]*\)\s*$', '', text)
    text = re.sub(r',?\s+(?:(?:expressed|measured)\s+)?in (?:meters?|centimeters?|millimeters?|feet|foot|inches)\s*$', '', text, flags=re.I)
    text = re.sub(r'\s+using their (?:closest|nearest) points,?\s*$', '', text, flags=re.I)
    text = re.sub(r'\s+are\s*$', '', text, flags=re.I)
    patterns = [r'(?:between|separating|separate) (?:the (?:nearest|closest) points of )?(?:the )?(.+?) and (?:the )?(.+)$',
                r'how far apart (?:are )?(?:the closest points of )?(?:the )?(.+?) and (?:the )?(.+)$',
                r'from (?:the (?:nearest|closest) point on )?(?:the )?(.+?) to (?:the (?:nearest|closest) point on )?(?:the )?(.+)$',
                r'(?:separation of|separating) (?:the )?(.+?) from (?:the )?(.+)$']
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return [x.strip().lower() for x in m.groups()]
    raise ValueError('cannot parse names: ' + question)


def factor(q):
    for p, v in [(r'\b(?:centimeters?|cm)\b', 100.), (r'\b(?:feet|foot|ft)\b', 1/.3048),
                 (r'\b(?:inches|inch)\b', 1/.0254), (r'\b(?:meters?|metres?)\b', 1.)]:
        if re.search(p, q, re.I):
            return v
    raise ValueError('unit missing')


def mra(pred, truth):
    if truth == 0:
        return 100. if pred == 0 else 0.
    relative = abs(pred - truth) / abs(truth)
    # Preserve evalpath.official.official_mra's floating-point thresholds.
    start, end, interval = .5, .95, .05
    n = int((end - start) / interval + 2)
    thresholds = [start + i * (end - start) / (n - 1) for i in range(n)]
    return 100. * sum(relative <= 1. - t for t in thresholds) / n


def analyze(step):
    all_rows = load(step)
    rows = [r for r in all_rows if r['question_type'] == 'object_abs_distance']
    objects, items = [], []
    status, support, sam, nulls, candidate_shapes = Counter(), Counter(), Counter(), Counter(), Counter()
    observed_other_types = Counter()
    for r in all_rows:
        if r['question_type'] != 'object_abs_distance':
            for c in r['arms']['tower']['tool_calls']:
                if c.get('family') == 'ground':
                    observed_other_types[r['question_type']] += 1
    call_total = sum(sum(c.get('family') == 'ground' for c in r['arms']['tower']['tool_calls']) for r in rows)
    timings = Counter()
    for r in rows:
        a = r['arms']['tower']
        raw = r['raw']['arms']['tower']['output']
        timings['total_s'] += raw['seconds']
        for k, v in raw.get('timings', {}).items():
            if k != 'total_s':
                timings[k] += v
        calls = a['tool_calls']
        operands = names(r['question'])
        recs = []
        for operand, name in enumerate(operands):
            matches = [c for c in calls if c.get('family') == 'ground' and
                       re.search(r'obj="([^"]+)"', c.get('call', '')) and
                       re.search(r'obj="([^"]+)"', c['call']).group(1).strip().lower() == name and
                       'mode="box"' in c['call']]
            # First valid diagnostic call; retain retries separately in raw corpus.
            c = next((c for c in matches if c.get('stage1')), matches[0] if matches else {})
            d = c.get('stage1') or {}
            idx = d.get('chosen_index')
            cand = d.get('candidates', [])
            chosen = cand[idx] if idx is not None and 0 <= idx < len(cand) else None
            response = c.get('response', '')
            m = re.search(r': frames ([\d,]+) \(best', response)
            nframes = len(set(m.group(1).split(','))) if m else None
            if not c:
                state = 'no_valid_ground_call'
            elif not d:
                state = 'missing_diagnostics'
            elif not d['linked_candidates']:
                state = 'empty_linked_pool'
            elif idx == -1:
                state = 'selected_null'
            elif nframes is not None:
                state = 'printed_lt3' if nframes < 3 else 'printed_ge3'
            else:
                state = 'no_printed_box'
            status[state] += 1
            if d:
                sam['raw_empty' if not sum(d['sam3']['kept_per_frame']) else 'raw_nonempty'] += 1
                nulls[str(d.get('null_would_win'))] += 1
                candidate_shapes['pool_gt_logged_candidates'] += d['linked_candidates'] > len(cand)
                if chosen:
                    support[len(set(chosen['frames']))] += 1
            rec = dict(step=step, item_id=r['item_id'], room=r['room'], scene=r['scene'],
                       operand=operand, name=name, stage='U', missing='visibility_and_instance_binding',
                       state=state, candidate_count=d.get('linked_candidates'), chosen_index=idx,
                       selected_frame_count=nframes, logged_candidate_frames=chosen.get('frames') if chosen else None,
                       raw_masks_available=False, candidate_masks_available=False,
                       gt_visibility=None, selected_identity_correct=None,
                       null_would_win=d.get('null_would_win'),
                       sam_kept=d.get('sam3', {}).get('kept_per_frame'),
                       lift_reasons=d.get('lift_reasons'))
            objects.append(rec)
            recs.append(rec)
        if all(x['state'] == 'no_valid_ground_call' for x in recs):
            group = 'no_call'
        elif all(x['selected_frame_count'] is not None for x in recs):
            group = 'printed_lt3' if min(x['selected_frame_count'] for x in recs) < 3 else 'printed_ge3'
        else:
            group = 'no_pair_of_boxes'
        gaps = [re.search(r'\bdistance\s+([\d.]+)\s+m', c.get('response', ''))
                for c in calls if c.get('family') == 'gap']
        gaps = [float(m.group(1)) for m in gaps if m]
        gap_score = mra(gaps[-1] * factor(r['question']), float(r['truth']['scored'])) if gaps else None
        gap_canonical_score = mra(gaps[-1] * factor(r['question']), float(r['raw']['input']['answer'])) if gaps else None
        items.append(dict(item_id=r['item_id'], room=r['room'], scene=r['scene'], group=group,
                          stage='U', score=100*a['score'], gap_score=gap_score,
                          gap_canonical_score=gap_canonical_score,
                          called=any(c.get('family') == 'ground' for c in calls),
                          source_frame_indices=r['raw']['input']['source_frame_indices'],
                          total_num_frames=r['raw']['input']['total_num_frames'], names=operands))
    out = dict(step=step, items=len(rows), rooms=len(set(r['room'] for r in rows)),
               captures=len(set(r['scene'] for r in rows)), objects=len(objects),
               unique_capture_names=len(set((r['scene'], r['name']) for r in objects)),
               ground_calls_including_retries=call_total, object_states=dict(status),
               raw_presence=dict(sam), null_would_win=dict(nulls), candidate_logging=dict(candidate_shapes),
               chosen_support=dict(support), timings=dict(timings),
               other_types_with_ground_calls=dict(observed_other_types),
               formal_stages={s: None for s in ('S0','S1','S2','S3','S4','S5')},
               unknown_inventory_objects=len(objects),
               unknown_called_objects=sum(o['state']!='no_valid_ground_call' for o in objects),
               outside_funnel_objects=sum(o['state']=='no_valid_ground_call' for o in objects),
               observed_object_counts=summarize([dict(room=o['room'],group=o['state'],score=0.) for o in objects],
                                                 reference='not_a_stage'),
               answer_proxy=summarize(items, reference='printed_ge3'),
               overall=summarize([dict(r,group='all') for r in items], reference='all'),
               gap_proxy=summarize([dict(r,score=r['gap_score'] if r['gap_score'] is not None else 0.) for r in items],
                                   reference='printed_ge3'),
               gap_canonical_proxy=summarize([dict(r,score=r['gap_canonical_score']) for r in items if r['gap_canonical_score'] is not None],
                                             reference='printed_ge3'))
    for label, data in [('objects',objects),('items',items)]:
        (ROOT/'work'/('%s%d.jsonl'%(label,step))).write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in data))
    return out, items


def main():
    result = {}
    tasks = []
    for step in (544,400):
        result[str(step)], items = analyze(step)
        tasks.extend(dict(x, step=step) for x in items if x['called'])
    plan = []
    for t in tasks:
        plan.append(dict(step=t['step'], item_id=t['item_id'], room=t['room'], scene=t['scene'],
                         names=t['names'], answer_indices=t['source_frame_indices'],
                         ground_indices={str(n): sample_indices(t['total_num_frames'], n, t['source_frame_indices'])
                                         for n in (32,64,96)}))
    (ROOT/'work/summary.json').write_text(json.dumps(result,indent=2)+'\n')
    (ROOT/'kit/tasks.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps({k:{f:v[f] for f in ('items','rooms','objects','object_states','raw_presence','null_would_win','timings')}
                      for k,v in result.items()},indent=2))


if __name__ == '__main__':
    main()
