"""Aggregate per-capture R0 question files: split files per layout, counts per type, answer histograms, the
no-information constants table, and comparison histograms against the D0 v5 training rows (benchmark items are never
opened, so the reference distribution is the trained one; in/d0v5_templates.jsonl line 1).
Constants: numeric types use the median answer of R0-rl (train side), scored on R0-dev with VSI MRA; multiple choice
uses the most frequent correct option text on R0-rl and the letter-chance rate.
usage: aggregate.py QDIR OUTDIR
"""
import collections, glob, hashlib, json, os, sys
import numpy as np

NUM = {'object_counting', 'object_size_estimation', 'object_abs_distance', 'room_size_estimation'}


def mra(pred, gt):
    if gt == 0:
        return float(pred == 0)
    r = abs(pred - gt) / abs(gt)
    return float(np.mean([r < 1 - t for t in np.arange(0.5, 0.96, 0.05)]))


def main(qdir, outdir):
    os.makedirs(outdir, exist_ok=True)
    items = []
    for p in sorted(glob.glob(os.path.join(qdir, '*.jsonl'))):
        items += [json.loads(l) for l in open(p)]
    for lay in (32, 64):
        for split in ('R0-dev', 'R0-rl'):
            with open(os.path.join(outdir, 'R0_QUESTIONS_%s_f%d.jsonl' % (split.replace('R0-', ''), lay)), 'w') as f:
                for it in items:
                    if it['r0_split'] != split:
                        continue
                    o = {k: v for k, v in it.items() if not k.startswith(('answer_f', 'frame_indices_f'))}
                    o['answer'] = it['answer_f%d' % lay]; o['frame_indices'] = it['frame_indices_f%d' % lay]; o['num_frames'] = lay
                    f.write(json.dumps(o, sort_keys=True) + '\n')
    counts = collections.Counter((it['r0_split'], it['question_type'], it['subtype']) for it in items)
    diff = collections.Counter(it['question_type'] for it in items if it['answer_f32'] != it['answer_f64'])
    hist = collections.defaultdict(collections.Counter)
    for it in items:
        a = it['answer_f32']
        if it['question_type'] in NUM:
            v = float(a); b = {'object_counting': lambda v: str(int(v)) if v < 10 else '10+',
                               'object_size_estimation': lambda v: '%d-%d' % (v // 25 * 25, v // 25 * 25 + 25) if v < 300 else '300+',
                               'object_abs_distance': lambda v: '%.1f-%.1f' % (v // 0.5 * 0.5, v // 0.5 * 0.5 + 0.5) if v < 6 else '6+',
                               'room_size_estimation': lambda v: '%d-%d' % (v // 10 * 10, v // 10 * 10 + 10) if v < 100 else '100+'}[it['question_type']](v)
        else:
            b = dict(zip('ABCD', [o.split('. ', 1)[1] for o in it['options']]))[a] if it['question_type'].startswith('object_rel_direction') else 'letter ' + a
        hist[it['r0_split'] + '|' + it['question_type']][b] += 1
    const = {}
    for qt in sorted({it['question_type'] for it in items}):
        tr = [it for it in items if it['question_type'] == qt and it['r0_split'] == 'R0-rl']
        dv = [it for it in items if it['question_type'] == qt and it['r0_split'] == 'R0-dev']
        if not dv:
            continue
        if qt in NUM:
            c = float(np.median([float(i['answer_f32']) for i in tr])) if tr else float('nan')
            const[qt] = dict(kind='median of R0-rl', value=c, n_dev=len(dv),
                             dev_mra_f32=float(np.mean([mra(c, float(i['answer_f32'])) for i in dv])) * 100 if tr else None,
                             dev_mra_f64=float(np.mean([mra(c, float(i['answer_f64'])) for i in dv])) * 100 if tr else None)
        else:
            txt = collections.Counter(dict(zip('ABCD', [o.split('. ', 1)[1] for o in i['options']]))[i['answer_f32']] for i in tr)
            top = txt.most_common(1)[0][0] if txt else None
            hit = [dict(zip('ABCD', [o.split('. ', 1)[1] for o in i['options']]))[i['answer_f32']] == top for i in dv]
            const[qt] = dict(kind='most frequent correct option text on R0-rl', value=top, n_dev=len(dv),
                             dev_acc=100 * float(np.mean(hit)), chance=100 * float(np.mean([1 / len(i['options']) for i in dv])),
                             letter_counts_dev=dict(collections.Counter(i['answer_f32'] for i in dv)))
    ref = json.loads(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'in', 'd0v5_templates.jsonl')).readline())
    refh = {}
    for qt in NUM & set(ref['answers']):
        vals = [(float(k), n) for k, n in ref['answers'][qt].items()]
        tot = sum(n for _, n in vals)
        refh[qt] = dict(median=float(np.median(np.repeat([v for v, _ in vals], [n for _, n in vals]))), n=tot)
    summary = dict(n_items=len(items), counts={'|'.join(k): v for k, v in sorted(counts.items())},
                   per_type_split={'%s|%s' % k: v for k, v in sorted(collections.Counter((i['r0_split'], i['question_type']) for i in items).items())},
                   layout_label_differs=dict(diff), histograms={k: dict(sorted(v.items())) for k, v in sorted(hist.items())},
                   constants=const, d0v5_reference=refh,
                   scenes=len({i['scene'] for i in items}))
    json.dump(summary, open(os.path.join(outdir, 'R0_QUESTIONS_SUMMARY.json'), 'w'), indent=1, sort_keys=True)
    for p in sorted(glob.glob(os.path.join(outdir, 'R0_QUESTIONS_*.jsonl'))):
        print(os.path.basename(p), hashlib.sha256(open(p, 'rb').read()).hexdigest(), sum(1 for _ in open(p)))
    print(json.dumps(summary['per_type_split'], indent=0)); print(json.dumps(const, indent=0)[:3000])


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
