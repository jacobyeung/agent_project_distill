"""Session-3 recounts for the third deepening wave (my own definitions, independent of the analysts).
usage: python3 deep3_recount.py [count] [reldist] [size] [dir] [xroom]"""
import sys, re, collections, random, math
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
C = collections.Counter; DD = collections.defaultdict
def num(x):
    try: return float(str(x).strip().split()[0])
    except Exception: return None
def mra(p, g):
    if p is None or g is None or g == 0: return 0.0
    e = abs(p - g) / abs(g); return sum(e <= 1 - t + 1e-9 for t in [0.5 + 0.05 * i for i in range(10)]) / 10.0
def mean(v): return sum(v) / len(v) if v else float('nan')
def med(v):
    v = sorted(v); n = len(v); return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0
which = sys.argv[1:] or ['count', 'reldist', 'size', 'dir', 'xroom']
D = {(s, st): K.direct(s[0], s[1], st) for s in [('R1', 200), ('R1', 100), ('S1', 544)] for st in ['dev-S1', 'R0-dev']}
def byid(s, st): return {r['id']: r for r in D[(s, st)]}
def sing(w):
    w = w.lower().strip(); w = re.sub(r'\(s\)$', '', w)
    for a, b in [('ies', 'y'), ('ves', 'f'), ('ches', 'ch'), ('shes', 'sh'), ('xes', 'x'), ('s', '')]:
        if w.endswith(a) and len(w) > len(a) + 2 and not w.endswith('ss'): return w[:-len(a)] + b
    return w
def kind(r): return r.get('subtype') or r.get('count_kind') or ('single' if r['set'] == 'dev-S1' else None)
def counted(st):  # room -> {class: truth} from single-category counting items
    out = DD(dict)
    for r in D[(('R1', 200), st)]:
        if r['type'] != 'object_counting' or kind(r) != 'single': continue
        m = re.search(r'[Hh]ow many (.+?)(?:\(s\))? (?:do|are|can|exist|is|in|appear|would|could|did)', r['question'])
        if m: out[r['room']][sing(m.group(1))] = num(r['gt'])
        else: out[r['room']]['_unparsed'] = out[r['room']].get('_unparsed', 0) + 1
    return out
def gbin(g): return '5+' if g >= 5 else str(int(g))
if 'count' in which:
    for st in ['R0-dev', 'dev-S1']:
        new = [r for r in D[(('R1', 200), st)] if r['type'] == 'object_counting' and kind(r) == 'single']
        o5, o1 = byid(('S1', 544), st), byid(('R1', 100), st)
        nl = [r for r in new if not r['forced_close']]
        print('COUNT', st, 'single', len(new), 'nonloop', len(nl), 'MRA nonloop 200 %.1f' % (100 * mean([r['score'] for r in nl])), '544 same items %.1f' % (100 * mean([o5[r['id']]['score'] for r in nl])), '100 %.1f' % (100 * mean([o1[r['id']]['score'] for r in nl])))
        conf = C(); over = under = 0.0
        for r in nl:
            g, p = num(r['gt']), num(r['pred'])
            conf[(gbin(g), 'lt' if p is not None and p < g else 'eq' if p == g else 'gt')] += 1
            if p is not None and p > g: over += 1 - r['score']
            elif p is not None and p < g: under += 1 - r['score']
        for gb in ['1', '2', '3', '4', '5+']:
            n = sum(v for (a, b), v in conf.items() if a == gb)
            if n: print('   truth', gb, 'n', n, 'under', conf[(gb, 'lt')], 'right', conf[(gb, 'eq')], 'over', conf[(gb, 'gt')], 'MRA200 %.1f' % (100 * mean([r['score'] for r in nl if gbin(num(r['gt'])) == gb])), 'MRA544 %.1f' % (100 * mean([o5[r['id']]['score'] for r in nl if gbin(num(r['gt'])) == gb])))
        print('   lost points on the single set: overcount %.2f undercount %.2f loops %.2f (of %d items)' % (100 * over / len(new), 100 * under / len(new), 100 * sum(1 - r['score'] for r in new if r['forced_close']) / len(new), len(new)))
        same = C()
        for r in nl:
            if r['score'] < 1: same[(o5[r['id']]['pred'] == r['pred'], o1[r['id']]['pred'] == r['pred'])] += 1
        print('   wrong nonloop: (same as 544, same as 100) ->', dict(same), '| answers 2:', sum(num(r['pred']) == 2 for r in nl), 'of', len(nl), '| always-2 MRA %.1f' % (100 * mean([mra(2.0, num(r['gt'])) for r in nl])))
if 'reldist' in which:
    for st in ['R0-dev', 'dev-S1']:
        cnt = counted(st); new = [r for r in D[(('R1', 200), st)] if r['type'] == 'object_rel_distance']; o5 = byid(('S1', 544), st); o1 = byid(('R1', 100), st)
        tab = DD(lambda: [0, 0, 0]); unp = 0
        for r in new:
            m = re.search(r'\(([^()]+)\)', r['question'])
            if not m: unp += 1; continue
            cands = [sing(x) for x in m.group(1).split(',')]
            ref = re.search(r'(?:to|from) the ([a-z \-]+?)\?', r['question'].split(')')[-1])
            refc = sing(ref.group(1)) if ref else None
            cc = cnt.get(r['room'], {}); multi = set(k for k, v in cc.items() if v and v >= 2)
            opt = dict((o[0], sing(o[3:])) for o in r['options'])
            keys = ['all', 'room has counting items' if cc else 'room has none', 'ref parsed' if refc else 'ref unparsed']
            if cc:
                keys.append('ref multi' if refc in multi else 'ref not multi')
                keys.append('any cand multi' if any(c in multi for c in cands) else 'no cand multi')
                keys.append('truth cand multi' if opt.get(r['gt']) in multi else 'truth cand not multi')
                keys.append('any of 5 multi' if (refc in multi or any(c in multi for c in cands)) else 'none of 5 multi')
            for k in keys: tab[k][0] += 1; tab[k][1] += r['score'] >= 1; tab[k][2] += o5[r['id']]['score'] >= 1
        print('RELDIST', st, len(new), 'unparsed', unp)
        for k in sorted(tab): v = tab[k]; print('   %-24s n %3d right200 %3d (%.1f) right544 %3d (%.1f)' % (k, v[0], v[1], 100.0 * v[1] / v[0], v[2], 100.0 * v[2] / v[0]))
        w = [r for r in new if r['score'] < 1]
        def vote(r):
            ps = [o5[r['id']]['pred'], o1[r['id']]['pred'], r['pred']]; top = C(ps).most_common(1)[0]
            return float((top[0] if top[1] >= 2 else r['pred']) == r['gt'])
        print('   wrong200', len(w), 'wrong at all three', sum(o5[r['id']]['score'] < 1 and o1[r['id']]['score'] < 1 for r in w), 'same pick at all three', sum(o5[r['id']]['pred'] == r['pred'] == o1[r['id']]['pred'] for r in w), '| majority vote %.1f' % (100 * mean([vote(r) for r in new])), 'any of three right %.1f' % (100 * mean([float(r['score'] >= 1 or o5[r['id']]['score'] >= 1 or o1[r['id']]['score'] >= 1) for r in new])))
if 'size' in which:
    for st in ['R0-dev', 'dev-S1']:
        new = [r for r in D[(('R1', 200), st)] if r['type'] == 'object_size_estimation']; o5, o1 = byid(('S1', 544), st), byid(('R1', 100), st)
        rows = []
        for r in new:
            m = re.search(r'of the (.+?),? (?:measured|in )', r['question']) or re.search(r"the ([a-z \-]+?)'s", r['question']) or re.search(r'of the ([a-z \-]+?)\?', r['question'])
            g, p = num(r['gt']), num(r['pred'])
            if g is None or p is None or p <= 0: continue
            rows.append((sing(m.group(1)) if m else '?', g, p, r))
        cls = DD(list)
        for c, g, p, r in rows: cls[c].append((g, p, r))
        big = dict((c, v) for c, v in cls.items() if len(v) >= 3 and c != '?')
        n = sum(len(v) for v in big.values())
        a = mean([mra(p, g) for v in big.values() for g, p, r in v]); b = c_ = d_ = 0.0
        for cname, v in big.items():
            b += max(sum(mra(p * f, g) for g, p, r in v) for f in [0.4 + 0.02 * i for i in range(131)])
            for i, (g, p, r) in enumerate(v):
                c_ += mra(med([x[0] for j, x in enumerate(v) if j != i]), g); d_ += mra(med([x[1] for x in v]), g)
        print('SIZE', st, 'items', len(new), 'parsed', len(rows), 'class unparsed', len(cls.get('?', [])), '| classes>=3:', len(big), 'items', n, '| (a) model %.1f (b) oracle class factor %.1f (c) dev-truth class median LOO %.1f (d) model class median %.1f | all items model %.1f' % (100 * a, 100 * b / n, 100 * c_ / n, 100 * d_ / n, 100 * mean([mra(p, g) for c, g, p, r in rows])))
        sg = C(); le = []
        for c, g, p, r in rows:
            p5, p1 = num(o5[r['id']]['pred']), num(o1[r['id']]['pred'])
            if not p5 or not p1 or p5 <= 0 or p1 <= 0: continue
            s = [math.log(x / g) for x in (p5, p1, p)]; le.append(s)
            sg['same sign x3' if (min(s) > 0 or max(s) < 0) else 'zero or mixed'] += 1
        print('   sign of log error across 544/100/200:', dict(sg), '| geo-mean of three MRA %.1f vs 200 alone %.1f, 544 alone %.1f (n %d)' % (100 * mean([mra(math.exp(mean(s)), 1.0) for s in le]), 100 * mean([mra(math.exp(s[2]), 1.0) for s in le]), 100 * mean([mra(math.exp(s[0]), 1.0) for s in le]), len(le)))
        small = [(g, p, r) for c, g, p, r in rows if g < 30]
        if small: print('   truth<30 in the asked unit: n', len(small), 'MRA %.1f' % (100 * mean([r['score'] for g, p, r in small])), 'pred>=30:', sum(p >= 30 for g, p, r in small), 'median abs err %.1f' % med([abs(p - g) for g, p, r in small]))
if 'dir' in which:
    T = ['object_rel_direction_easy', 'object_rel_direction_medium', 'object_rel_direction_hard']
    def lab(r, letter): return next((o[3:].strip().lower() for o in r['options'] if o.startswith(str(letter) + '.')), str(letter))
    for st in ['R0-dev', 'dev-S1']:
        for lvl in T:
            new = [r for r in D[(('R1', 200), st)] if r['type'] == lvl and r.get('subtype') in (None, 'toward')]
            w = [r for r in new if r['score'] < 1]
            if lvl.endswith('hard'):
                bits = C()
                for r in w:
                    gl, pl = lab(r, r['gt']).split('-'), lab(r, r['pred']).split('-')
                    if len(gl) == 2 and len(pl) == 2: bits[('FB wrong' if gl[0] != pl[0] else 'FB ok') + ', ' + ('LR wrong' if gl[1] != pl[1] else 'LR ok')] += 1
                    else: bits['unparsed'] += 1
                print('DIR', st, 'hard toward', len(new), 'wrong', len(w), dict(bits), '| truth back', sum(lab(r, r['gt']).startswith('back') for r in new), 'answers back', sum(lab(r, r['pred']).startswith('back') for r in new))
            else:
                print('DIR', st, lvl[-6:], 'toward', len(new), 'wrong', len(w), 'truth x answer', sorted(C((lab(r, r['gt']), lab(r, r['pred'])) for r in new).items()))
if 'xroom' in which:
    random.seed(0)
    for st in ['R0-dev', 'dev-S1']:
        for step in [('R1', 200), ('S1', 544)]:
            rs = D[(step, st)]; tm = DD(list)
            for r in rs: tm[r['type']].append(r['score'])
            mu = dict((t, mean(v)) for t, v in tm.items()); sd = dict((t, (mean([(x - mu[t]) ** 2 for x in v]) ** 0.5 or 1.0)) for t, v in tm.items())
            z = [((r['score'] - mu[r['type']]) / sd[r['type']], r['room'], r['type']) for r in rs]
            def stat(zz):
                per = DD(list)
                for v, room, t in zz: per[room].append(v)
                ms = [mean(v) * (len(v) ** 0.5) for v in per.values() if len(v) >= 5]
                return mean([m * m for m in ms]), len(ms)
            obs, nr = stat(z); sh = []; byt = DD(list)
            for i, (v, room, t) in enumerate(z): byt[t].append(i)
            for _ in range(300):
                zz = list(z)
                for t, idx in byt.items():
                    vals = [z[i][0] for i in idx]; random.shuffle(vals)
                    for i, v in zip(idx, vals): zz[i] = (v, z[i][1], t)
                sh.append(stat(zz)[0])
            print('XROOM', st, step, 'rooms with >=5 items', nr, '| mean squared standardised room effect: observed %.2f, shuffled mean %.2f, shuffled max %.2f, p %.3f' % (obs, mean(sh), max(sh), mean([float(s >= obs) for s in sh])))
            if step == ('R1', 200):
                per = DD(list)
                for r in rs: per[r['room']].append(1 - r['score'])
                tot = sum(sum(v) for v in per.values()); acc = 0; k = 0
                for v in sorted(per.values(), key=lambda v: -sum(v)):
                    acc += sum(v); k += 1
                    if acc >= tot / 2: break
                srt2 = sorted(per.values(), key=lambda v: -mean(v)); fifth = srt2[:max(1, len(srt2) // 5)]
                print('      rooms', len(per), '| rooms holding half the lost points', k, '| worst fifth by mean loss:', len(fifth), 'rooms, %d items, %.1f%% of lost points, %.1f%% of items' % (sum(len(v) for v in fifth), 100 * sum(sum(v) for v in fifth) / tot, 100.0 * sum(len(v) for v in fifth) / len(rs)))
if 'stable' in which:
    for st in ['R0-dev', 'dev-S1']:
        o5, o1 = byid(('S1', 544), st), byid(('R1', 100), st); bt = DD(list)
        for r in D[(('R1', 200), st)]: bt[r['type'] + ('/' + r['subtype'] if r.get('subtype') in ('toward', 'away', 'single', 'multiple', 'closest', 'farthest') else '')].append(r)
        for t in sorted(bt):
            rs = [r for r in bt[t] if r['id'] in o5 and r['id'] in o1]; w = [r for r in rs if r['score'] < 1]
            w3 = [r for r in w if o5[r['id']]['score'] < 1 and o1[r['id']]['score'] < 1]
            same = sum(o5[r['id']]['pred'] == r['pred'] == o1[r['id']]['pred'] for r in w3)
            best = mean([max(r['score'], o5[r['id']]['score'], o1[r['id']]['score']) for r in rs]); med3 = mean([med([r['score'], o5[r['id']]['score'], o1[r['id']]['score']]) for r in rs])
            print('STABLE %-7s %-36s n %3d | score 544 %.1f, 100 %.1f, 200 %.1f | wrong at 200: %3d, wrong at all three: %3d (%.0f%%), same answer at all three: %3d | per-item median of three %.1f, best of three %.1f' % (st, t[:36], len(rs), 100 * mean([o5[r['id']]['score'] for r in rs]), 100 * mean([o1[r['id']]['score'] for r in rs]), 100 * mean([r['score'] for r in rs]), len(w), len(w3), 100.0 * len(w3) / max(1, len(w)), same, 100 * med3, 100 * best))
