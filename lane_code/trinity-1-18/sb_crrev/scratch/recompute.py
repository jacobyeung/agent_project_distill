"""Independent recomputation of call rate, capped rate, score and room MRA splits.

Imports nothing from sb_callrate or the package scorer. Score = journal scores.answer,
forced to 0 on finish=max_calls (the package rule); an independent MRA from the
answer text cross-checks it.
"""
import glob, json, random, re
from collections import defaultdict
import numpy as np

IN = '/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/'
READS = {'A4': IN + 'A4/ret/metadata/reads/0', 'B5': IN + 'B5/ret/metadata/reads/0',
         'b1r0': IN + 'bases/b1/work/ret/metadata/reads/0', 'b1r1': IN + 'bases/b1/work/ret/metadata/reads/1',
         'b2r0': IN + 'bases/b2/work/ret/metadata/reads/0'}
CAPS = {'max_calls', 'max_new_tokens', 'length'}


def journal(name):
    rows = {}
    for p in sorted(glob.glob(READS[name] + '/metadata/journals/*/*/items.jsonl')):
        for line in open(p):
            r = json.loads(line)
            assert r['id'] not in rows
            rows[r['id']] = r
    return rows


def tag(call):
    m = re.match(r'<(\w+)', call or '')
    args = dict((k, v.strip('"')) for k, v in re.findall(r'(\w+)=("[^"]*"|[^\s>/]+)', call or ''))
    return (m[1] if m else None), args


def is_call(rec, kind):
    name, args = tag(rec.get('call'))
    if kind == 'object_abs_distance':
        return name == 'gap' or (name == 'ground' and args.get('mode') != 'room')
    if kind == 'room_size_estimation':
        return (name == 'ground' and args.get('mode') == 'room') or rec.get('family') == 'room'
    raise KeyError(kind)


def score(o):
    return 0.0 if o.get('finish') == 'max_calls' else float(o['scores']['answer'])


def mra(pred, gt):
    rel = abs(pred - gt) / abs(gt)
    return float(np.mean([rel < 1 - t for t in np.arange(0.5, 0.96, 0.05)]))


def answer(o):
    if o.get('finish') == 'max_calls':
        return None
    t = o.get('text', '')
    tags = re.findall(r'<answer>\s*(.*?)\s*</answer>', t, re.S)
    s = tags[-1] if tags else (t.rsplit('</think>', 1)[1].split('<|', 1)[0].strip() if '</think>' in t else '')
    m = re.match(r'\s*([+-]?\d+(?:\.\d*)?)', s)
    return float(m[1]) if m else None


def boot(pairs):
    g = defaultdict(list)
    for room, v in pairs:
        g[room].append(v)
    groups = [(sum(g[k]), len(g[k])) for k in sorted(g)]
    rng = random.Random(17)
    s = []
    for _ in range(10000):
        d = rng.choices(groups, k=len(groups))
        s.append(sum(a for a, _ in d) / sum(n for _, n in d))
    tot = sum(a for a, _ in groups) / sum(n for _, n in groups)
    return round(tot, 6), [round(x, 6) for x in np.quantile(s, [.025, .975])]


def metrics(rows, ids, kind):
    sel = [rows[k] for k in ids]
    n = len(sel)
    calls = sum(any(is_call(r, kind) for r in x['output']['calls'].get('records', [])) for x in sel)
    anyrec = sum(bool(x['output']['calls'].get('records')) for x in sel)
    capped = sum(x['output'].get('finish') in CAPS for x in sel)
    sc = [score(x['output']) for x in sel]
    return dict(n=n, call=calls, call_rate=round(calls / n, 6), any_record=anyrec, capped=capped,
                capped_rate=round(capped / n, 6), score=round(float(np.mean(sc)), 6))


def paired(ra, rb, ids, items):
    return boot([(items[k]['room_key'], 100 * (score(ra[k]['output']) - score(rb[k]['output']))) for k in ids])


if __name__ == '__main__':
    A4, B5, b1r0, b1r1, b2r0 = (journal(k) for k in ('A4', 'B5', 'b1r0', 'b1r1', 'b2r0'))
    dev = {i['id']: i for i in json.load(open(IN + 'A4/src/items/devs1_routed.json'))['items']}
    rm = json.load(open(IN + 'B4/src/items/room134.json'))
    room = {i['id']: i for i in rm['items']}
    sets = rm['sets']
    print('room134 sets:', {k: len(v) for k, v in sets.items()})
    D = sorted(k for k, i in dev.items() if i['question_type'] == 'object_abs_distance')
    R36 = sorted(k for k, i in dev.items() if i['question_type'] == 'room_size_estimation')
    R134 = sorted(room)
    print('room36 subset of room134:', set(R36) <= set(R134), '| room36 in dev-S1:', len(set(R36) & set(sets['dev-S1'])))
    for k in R36:
        for f in ('question', 'ground_truth', 'room_key'):
            assert dev[k].get(f) == room[k].get(f), (k, f)
    out = {}
    out['distance A4 s200'] = metrics(A4, D, 'object_abs_distance')
    out['distance b1r1 s544'] = metrics(b1r1, D, 'object_abs_distance')
    out['distance delta A4-b1r1'] = paired(A4, b1r1, D, dev)
    out['room36 A4 s200'] = metrics(A4, R36, 'room_size_estimation')
    out['room36 b2r0 s544'] = metrics(b2r0, R36, 'room_size_estimation')
    out['room36 b1r0 s544'] = metrics(b1r0, R36, 'room_size_estimation')
    out['room36 delta A4-b2r0'] = paired(A4, b2r0, R36, dev)
    out['room36 delta A4-b1r0'] = paired(A4, b1r0, R36, dev)
    out['room134 B5 s200'] = metrics(B5, R134, 'room_size_estimation')
    out['room134 b2r0 s544'] = metrics(b2r0, R134, 'room_size_estimation')
    for pop, ids in [('all', R134), ('dev-S1', sorted(sets['dev-S1'])), ('R0-dev', sorted(sets['R0-dev']))]:
        out['MRA ' + pop] = dict(n=len(ids), A_B5=round(100 * np.mean([score(B5[k]['output']) for k in ids]), 2),
                                 B_b2r0=round(100 * np.mean([score(b2r0[k]['output']) for k in ids]), 2),
                                 delta=paired(B5, b2r0, ids, room))
    out['dev-S1 MRA from A4 rooms'] = round(100 * np.mean([score(A4[k]['output']) for k in R36]), 2)
    for k, v in out.items():
        print(k, json.dumps(v))
    # Cross-check scores.answer against an independent MRA of the parsed final answer.
    for name, rows, ids, items in [('A4 dist', A4, D, dev), ('b1r1 dist', b1r1, D, dev), ('B5 room', B5, R134, room), ('b2r0 room', b2r0, R134, room)]:
        agree = bad = 0
        for k in ids:
            o = rows[k]['output']
            p = answer(o)
            mine = 0.0 if p is None else mra(p, float(items[k]['ground_truth']))
            if abs(mine - score(o)) < 1e-9:
                agree += 1
            else:
                bad += 1
        print('MRA cross-check', name, 'agree', agree, 'differ', bad)
