"""Facing gate and toward protected outcome: R1 export vs step 544 (e193, job 169526) on the away and forward twins, paired by item.
Pairing is refused unless id, question, options and ground truth agree on every item. Room bootstrap over physical rooms
(room field), 10,000 draws, seed 20261118, percentile intervals at 95% and at the H1 level of the look (99.29% at step 200, 99.82% later; cont_ops20 face_look.py).
usage: face.py --x <fetched/x of the facing read> [--out face.json]"""
import argparse, collections, json, random, re
BASE = '/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/%s/results/budget_2048/0/items_leg_m544_%s.jsonl'
H1 = None  # set from --step: 99.29% at step 200, 99.82% at later looks (PRELAUNCH_CARD_R1.md line 19, "at H1's level")
def rows(p): return {r['id']: r for r in map(json.loads, open(p)) if r.get('id')}
def boot(pairs, n=10000, seed=20261118):
    by = collections.defaultdict(list)
    for room, d in pairs: by[room].append(d)
    rooms = sorted(by); rng = random.Random(seed); ms = []
    for _ in range(n):
        s = c = 0
        for _ in rooms:
            v = by[rooms[rng.randrange(len(rooms))]]; s += sum(v); c += len(v)
        ms.append(100.0 * s / c)
    ms.sort(); q = lambda p: round(ms[min(n - 1, max(0, int(p * n)))], 2)
    return dict(delta=round(100.0 * sum(d for _, d in pairs) / len(pairs), 2), ci95=[q(0.025), q(0.975)], ci_h1=[q((1 - H1) / 2), q((1 + H1) / 2)], rooms=len(rooms))
def opt_text(r, letter):
    m = re.search(r"'%s\. ([^']*)'" % re.escape(str(letter or '')), str(r.get('options')))
    return m.group(1) if m else None
a = argparse.ArgumentParser(); a.add_argument('--x', required=True); a.add_argument('--out'); a.add_argument('--step', type=int, required=True, choices=(200, 400, 600, 800)); a = a.parse_args()
H1 = 0.9929 if a.step == 200 else 0.9982
import os
STEP = json.load(open(os.path.join(a.x, 'SPEC.json')))['step'] if os.path.exists(os.path.join(a.x, 'SPEC.json')) else None
if STEP is not None and STEP != a.step: raise SystemExit('SPEC.json step %s differs from --step %s' % (STEP, a.step))
LABEL = ('m%d' % STEP) if STEP else 'read'
out = {'export_step': STEP}; lines = []
for fam in ('away', 'forward'):
    b = rows(BASE % (fam, fam)); e = rows('%s/%s/a0/results/budget_2048/0/items_a0.jsonl' % (a.x, fam))
    assert set(b) == set(e) and len(b) == 150, (fam, len(b), len(e), len(set(b) ^ set(e)))
    for i in b:
        for k in ('question', 'options', 'ground_truth', 'question_type'):
            assert str(b[i][k]) == str(e[i][k]), (fam, i, k)
    for band in ('all', 'easy', 'medium', 'hard'):
        ids = sorted(i for i in b if band == 'all' or b[i]['question_type'].endswith(band))
        pairs = [(b[i]['room'], float(e[i]['score']) - float(b[i]['score'])) for i in ids]
        r = dict(n=len(ids), base=round(100 * sum(float(b[i]['score']) for i in ids) / len(ids), 2),
                 export=round(100 * sum(float(e[i]['score']) for i in ids) / len(ids), 2), **boot(pairs))
        if fam == 'away':
            r['back_share_export'] = round(100 * sum('back' in (opt_text(e[i], e[i].get('extracted_answer')) or '') for i in ids) / len(ids), 1)
            r['back_share_544'] = round(100 * sum('back' in (opt_text(b[i], b[i].get('extracted_answer')) or '') for i in ids) / len(ids), 1)
            r['back_share_truth'] = round(100 * sum('back' in (opt_text(b[i], b[i]['ground_truth']) or '') for i in ids) / len(ids), 1)
        out['%s/%s' % (fam, band)] = r
        lines.append('%-8s %-6s n%4d r%3d  544 %6.2f  %s %6.2f  d %+6.2f 95%% [%+.2f,%+.2f] H1 [%+.2f,%+.2f]%s' % (
            fam, band, r['n'], r['rooms'], r['base'], LABEL, r['export'], r['delta'], *r['ci95'], *r['ci_h1'],
            ('  back: %s %.1f%% 544 %.1f%% truth %.1f%%' % (LABEL, r['back_share_export'], r['back_share_544'], r['back_share_truth'])) if fam == 'away' else ''))
out['facing_gate_passes_95'] = out['away/all']['ci95'][0] > 0
out['toward_protected_holds_H1'] = out['forward/all']['ci_h1'][1] < 0
print('\n'.join(lines)); print('facing gate (away rises, 95%% interval above zero): %s | toward protected outcome holds (H1 interval wholly below zero): %s' % (out['facing_gate_passes_95'], out['toward_protected_holds_H1']))
if a.out: json.dump(out, open(a.out, 'w'), indent=1)
