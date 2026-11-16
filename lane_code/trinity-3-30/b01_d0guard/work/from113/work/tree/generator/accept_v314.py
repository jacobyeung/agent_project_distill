"""Acceptance for a dose_t0.py run: counts per type, refusals, the renderer's own replay checks, answers against the
pool's v0 answer and the released label, histograms against VSI-Bench, the hand-reading sheet, and the first batch on
every rank through the trainer tree's routing encoder (c1mix_v313 = 31b57cf, read-only; placeholder pixels).
usage: accept_v314.py RUN_DIR SHEET.md"""
import collections
import glob
import gzip
import hashlib
import json
import sys

import numpy as np

L = '/scratch/jjyeung/orch_cd/dose_pool'
TREE = '/scratch/jjyeung/orch_cd/orchard_cp2/work/c1mix_v313'
BENCH = '/scratch/jjyeung/orch_cd/weak_data/inputs/VSIBENCH_meta_5130.jsonl'
TO_M = {'mm': 0.001, 'cm': 0.01, 'm': 1.0, 'in': 0.0254, 'ft': 0.3048}


def main(run, sheet):
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent/'derivgen_v7'))
    sys.path.insert(0, f'{L}/work/dosepool')
    import common as C
    pool = {}
    for l in gzip.open(f'{L}/out/pool_v0/ROWS_ALL.jsonl.gz', 'rt'):
        r = json.loads(l)
        pool[r['qid']] = r
    rows, packed, checks = [], [], collections.Counter()
    runs = run.split(',')
    for d in [x for r_ in runs for x in glob.glob(f'{r_}/scans/*/*/DONE.json')]:
        done = json.load(open(d))
        checks.update(done['checks'])
        base = d.rsplit('/', 1)[0]
        rows += [json.loads(l) for l in open(base + '/admitted.jsonl')]
        packed += [json.loads(l) for l in open(base + '/packed.jsonl')]
    items, refused = collections.Counter(), collections.Counter()
    for r_ in runs:
        s_ = json.load(open(f'{r_}/SUMMARY.json'))
        items.update(s_['items']); refused.update({k: v for k, v in s_['agg'].items() if k.startswith(('refused', 'scene_error'))})
    out = dict(admitted=len(rows), checks=dict(checks), items_built=dict(items), refusals=dict(refused))
    by = collections.defaultdict(list)
    for r in rows:
        by[r['type']].append(r)
    agree, hist = {}, {}
    for t, rs in by.items():
        a = collections.Counter()
        for r in rs:
            p = pool[r['qid']]
            if t == 'object_abs_distance':
                rel = C.num(p['released_answer']) * TO_M[C.question_unit(p['student_input']['question'])]
                v0 = float(p['answer']) * TO_M[C.question_unit(p['student_input']['question'])]
                g = float(r['answer'])
                a['released_within10'] += abs(g - rel) <= 0.1 * rel
                a['v0_within10_released'] += abs(v0 - rel) <= 0.1 * rel
                a['answer_changed_vs_v0_2dp'] += round(g, 2) != round(v0, 2)
            elif t == 'absolute_direction_object':
                from derivgen.gaps_v314 import circular_error
                a['released_within15deg'] += circular_error(r['answer'],p['released_answer']) <= 15
                a['pool_within15deg'] += circular_error(r['answer'],p['answer']) <= 15
            elif t == 'object_counting':
                a['released_count_equal'] += int(r['answer']) == int(p['released_answer'])
                a['pool_count_equal'] += int(r['answer']) == int(p['answer'])
            else:
                content = C.option_texts(r['options'])[r['answer']]
                a['released_content_equal'] += content == p['answer_content']
                a['answer_changed_vs_v0'] += content != p['answer_content']
            a['n'] += 1
        agree[t] = dict(a)
        if t == 'object_abs_distance':
            hist[t] = dict(collections.Counter(min(int(float(r['answer'])), 6) for r in rs))
        elif t == 'object_counting':
            hist[t] = dict(collections.Counter(str(int(r['answer'])) if int(r['answer']) < 10 else '10+' for r in rs))
        elif t == 'absolute_direction_object':
            hist[t] = dict(collections.Counter(30*(int(r['answer'])%360//30) for r in rs))
        else:
            hist[t] = dict(letters=dict(collections.Counter(r['answer'] for r in rs)),
                           content=dict(collections.Counter(C.option_texts(r['options'])[r['answer']] for r in rs)) if 'direction' in t else None)
    B = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for b in map(json.loads, open(BENCH)):
        if b['question_type'] in by:
            if b['options']:
                B[b['question_type']]['letters'][b['ground_truth']] += 1
                if 'direction' in b['question_type']:
                    B[b['question_type']]['content'][C.option_texts(b['options'])[b['ground_truth']]] += 1
            elif b['question_type'] == 'object_counting':
                value=int(b['ground_truth'])
                B[b['question_type']]['count'][str(value) if value<10 else '10+'] += 1
            else:
                B[b['question_type']]['m'][min(int(float(b['ground_truth'])), 6)] += 1
    out.update(agreement=agree, histograms_pool=hist, histograms_bench={k: {kk: dict(vv) for kk, vv in v.items()} for k, v in B.items()})
    # hand-reading sheet: five rows per type, seeded
    lines = ['# Head-backed v3.14 rows to read: %s (5 per type, seeded)' % run, '']
    for t, rs in sorted(by.items()):
        lines += ['## ' + t, '']
        for r in sorted(rs, key=lambda r: hashlib.sha256(('read' + r['qid']).encode()).hexdigest())[:5]:
            p = pool[r['qid']]
            lines += ['### `%s` %s, released %s (%s), program v0 %s' % (r['qid'], r['canonical'], p['released_answer'], p['answer_content'], p['answer']),
                      '- VSI-590K question: ' + p['student_input']['question'].replace('\n', ' '),
                      '- Row question: ' + r['question'].replace('\n', ' / '), '- Options: ' + ' / '.join(r['options'] or []),
                      '- Answer %s, GT %s' % (r['answer'], r['gt_answer']), '', '```', r['suffix'], '```', '']
    open(sheet, 'w').write('\n'.join(lines))
    # first batch through the tree's routing encoder
    sys.path.insert(0, TREE)
    fb = []
    try:
        import student_pilot.carrier_c1_routing as R
        import student_pilot.carrier_c1_data as Dd
        import student_pilot.pose_samples as PS
        from transformers import AutoProcessor
        proc = AutoProcessor.from_pretrained('/scratch/jjyeung/orch_cd/integ_v3/out/acceptance_inputs/T0_BIND_REPRO_R6/hf')
        proc._student_pilot_student = 'qwen35'
        R.add_routing_tokens(proc, grounding=True)
        PS.load_frames = lambda inputs: np.full((len(inputs['frames']), 480, 640, 3), 128, np.uint8)
        mix = ['pose'] * 4 + ['vqa'] * 8 + ['pointing'] * 4 + ['routing'] * 4
        for world in (4, 8):
            plan = next(Dd.mixed_indices({'pose': 202884, 'vqa': 57033, 'pointing': 205635, 'routing': len(packed)}, 1,
                                         seed=17, training_mode='final', mix=mix, world=world))
            for rank, i in enumerate([ix for s, ix in plan if s == 'routing'][0]):
                pr = packed[i]
                rec = dict(world=world, rank=rank, qid=pr.get('qid'), form=pr.get('form'))
                try:
                    pr['provenance'].setdefault('source_row_sha256', pr['provenance'].get('cp2_row_sha256'))  # rows from runs before the fix
                    fi = pr['provenance']['frame_indices']
                    rgb = dict(frames=[dict(path='/placeholder/%d.png' % k, sha256='0' * 64, source_index=k) for k in fi],
                               fps=30.0, total_num_frames=max(fi) + 1)
                    row = R.c1_row(pr, rgb)
                    batch, audit = R.encode(proc, row, 'append_after_temporal_group_video_tokens_v1', 'final', 'duplicate', None)
                    rec.update(ok=True, tokens=int(batch['input_ids'].shape[1]))
                except Exception as ex:  # noqa: BLE001 - the refusal is the finding
                    rec.update(ok=False, error=repr(ex)[:300])
                fb.append(rec)
    except Exception as ex:  # noqa: BLE001
        fb.append(dict(ok=False, error='setup: ' + repr(ex)[:300]))
    out['first_batch_tree_31b57cf'] = fb
    json.dump(out, open(f'{runs[0]}/ACCEPT.json', 'w'), indent=1, default=str)
    print(json.dumps({k: out[k] for k in ('admitted', 'checks', 'agreement')}, indent=1))
    print(json.dumps(fb[:3], indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
