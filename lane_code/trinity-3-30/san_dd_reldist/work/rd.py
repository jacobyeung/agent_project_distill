"""Shared loaders/parsers for lane san_dd_reldist (read-only; caches a compact pickle in /tmp only)."""
import sys, re, os, pickle, collections
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
CACHE = '/tmp/san_dd_reldist_cache_v1.pkl'
STEPS = (('R1', 200), ('R1', 100), ('S1', 544))
SETS = ('dev-S1', 'R0-dev')
KEEPF = ('id', 'set', 'step', 'type', 'question', 'options', 'gt', 'pred', 'score', 'pred_on', 'score_on', 'text',
         'forced_close', 'think_tokens', 'room', 'subtype')

def load():
    if os.path.exists(CACHE):
        return pickle.load(open(CACHE, 'rb'))
    D, C = {}, {}
    for run, step in STEPS:
        for s in SETS:
            D[(step, s)] = {r['id']: {k: r[k] for k in KEEPF} for r in K.direct(run, step, s, types=['object_rel_distance'])}
    for s in SETS:
        C[s] = [{k: r[k] for k in ('id', 'question', 'gt', 'room', 'subtype', 'score', 'pred')} for r in K.direct('R1', 200, s, types=['object_counting'])]
    out = dict(D=D, C=C, SOURCES=sorted(set(K.SOURCES)))
    pickle.dump(out, open(CACHE, 'wb'))
    return out

def sing(w):
    w = w.lower().strip().replace('(s)', '')
    if w in ('mattress', 'thermos', 'glass', 'grass', 'bus', 'canvas', 'glasses', 'blinds', 'pants', 'scissors', 'headphones', 'speakers'):
        return w
    if w.endswith('ies') and len(w) > 4: return w[:-3] + 'y'
    for suf in ('sses', 'xes', 'shes', 'ches'):
        if w.endswith(suf): return w[:-2]
    if w.endswith('s') and not w.endswith('ss') and len(w) > 3: return w[:-1]
    return w

def opts(r):
    return {x[0]: x[3:].strip().lower() for x in r['options']}

def order(text):
    m = re.search(r'order[^\n]*?(?:is|are):\s*([^\n]+)', text or '')
    if not m: return None
    return [re.sub(r'^(?:then |and |the )', '', x.strip().rstrip('.')).strip() for x in m.group(1).lower().split(',')]

def vals544(text):
    m = re.search(r'to each:\s*([^\n]+)', text or '')
    if not m: return None
    out = {}
    for part in m.group(1).rstrip('.').split(';'):
        mm = re.match(r'^\s*(.*?)\s+([0-9]+(?:\.[0-9]+)?)\s*m\s*$', part.strip().rstrip('.'))
        if mm: out[mm.group(1).strip().lower()] = float(mm.group(2))
    return out

def refline(text):
    return (text or '').split('\n')[0]

def cite(text):
    """Classify what the reference line cites: frame<=32 | frame>32 | seconds | question | region | none."""
    l = refline(text).lower()
    m = re.search(r'first seen in (?:the )?frame (\d+)', l)
    if m: return 'frame<=32' if 1 <= int(m.group(1)) <= 32 else 'frame>32'
    if re.search(r'first seen in the [0-9.]+ ?s image', l): return 'seconds'
    if 'first seen in the question' in l: return 'question'
    if 'first seen' in l: return 'region'
    return 'none'

def refname(q):
    m = re.search(r'(?:closest|nearest|farthest|furthest)\s+(?:to|from)\s+(?:the\s+)?([^?]+?)\s*\?', q, re.I)
    return m.group(1).strip().lower() if m else None

def endpoint(r):
    q = r['question'].lower()
    far = (r.get('subtype') == 'farthest') or ('farthest' in q or 'furthest' in q)
    return 'farthest' if far else 'closest'

def count_map(C):
    """(set, room, singular class) -> list of single-class counts; and multi-class sums."""
    single, multi = collections.defaultdict(list), collections.defaultdict(list)
    for s, rows in C.items():
        for r in rows:
            q = r['question']
            m = re.search(r'among the (.+?) in this room', q, re.I)
            if m:
                cls = [sing(x) for x in re.split(r'\s*,\s*|\s+and\s+', m.group(1)) if x.strip()]
                for c in cls: multi[(s, r['room'], c)].append((int(float(r['gt'])), tuple(cls)))
                continue
            m = re.search(r'how many (.+?)\(s\)', q, re.I)
            if m: single[(s, r['room'], sing(m.group(1)))].append(int(float(r['gt'])))
    return single, multi

def ref_of(r200):
    """Reference name: the step-200 trace's Step-1 object when it occurs in the question, else a question regex."""
    m = re.search(r'find the (.+?)(?:,| \(|\s+first)', refline(r200['text']).lower())
    q = r200['question'].lower()
    if m and m.group(1).strip() in q: return m.group(1).strip()
    q2 = re.sub(r'\([^)]*\)', '', q)
    for mm in re.finditer(r"(?:\bto|\bnearest|\bclosest|\bfrom) the ([a-z][\w \-']*?)(?=\s*(?:[,.?;]|\bbased\b|\bfrom\b|\busing\b|\bmeasured\b|\bwhen\b|$))", q2):
        x = mm.group(1).strip()
        if re.match(r'(closest|nearest) (point|instance)|shortest', x): continue
        return x
    return None

def ratio(a, b):
    a, b = max(a, 0.01), max(b, 0.01)
    return max(a, b) / min(a, b)

def table(X=None):
    X = X or load(); D = X['D']; single, multi = count_map(X['C'])
    T = []
    for s in SETS:
        for i, r in D[(200, s)].items():
            r1, r5 = D[(100, s)][i], D[(544, s)][i]
            o = opts(r); ep = endpoint(r); E = 3 if ep == 'farthest' else 0
            t = dict(id=i, set=s, ep=ep, room=r['room'], q=r['question'], opts=o, gt=r['gt'], truth=o[r['gt']])
            t['ref'] = ref_of(r)
            for st, rr in ((200, r), (100, r1), (544, r5)):
                t['pick%d' % st] = o.get(rr['pred']); t['s%d' % st] = rr['score']; t['cite%d' % st] = cite(rr['text'])
                t['text%d' % st] = rr['text']
            for st, rr in ((200, r), (100, r1)):
                od = order(rr['text']); t['ord%d' % st] = od
                t['rk%d' % st] = od.index(t['truth']) if od and t['truth'] in od else None
            v = vals544(r5['text']); t['v544'] = v
            od5 = sorted(v, key=lambda k: v[k]) if v and set(v) == set(o.values()) else None
            t['ord544'] = od5; t['rk544'] = od5.index(t['truth']) if od5 else None
            for st in (200, 100, 544):
                t['d%d' % st] = abs(t['rk%d' % st] - E) if t['rk%d' % st] is not None else None
            # step-544 margin at the asked endpoint (its own numbers): ratio between endpoint value and the next one
            if od5:
                e1, e2 = (od5[0], od5[1]) if E == 0 else (od5[3], od5[2])
                t['m544'] = ratio(v[e1], v[e2]); t['m544_abs'] = abs(v[e1] - v[e2])
                t['tp544'] = ratio(v[t['truth']], v[t['pick200']]) if t['pick200'] != t['truth'] else None
            else:
                t['m544'] = t['m544_abs'] = t['tp544'] = None
            # multiplicity from the same room's counting items
            def cnt(name):
                if not name: return None
                k = (s, r['room'], sing(name))
                if k in single: return max(single[k])
                return None
            def wcnt(name):
                if not name: return None
                k = (s, r['room'], sing(name))
                return multi.get(k)
            t['cnt'] = {n: cnt(n) for n in list(o.values()) + [t['ref']]}
            t['wcnt'] = {n: wcnt(n) for n in list(o.values()) + [t['ref']] if wcnt(n)}
            t['multi_ref'] = (t['cnt'].get(t['ref']) or 0) >= 2
            t['multi_truth'] = (t['cnt'].get(t['truth']) or 0) >= 2
            t['multi_pick'] = (t['cnt'].get(t['pick200']) or 0) >= 2
            t['multi_any'] = any((c or 0) >= 2 for c in t['cnt'].values())
            names = list(o.values()) + [t['ref'] or '']
            t['overlap'] = sorted({(a, b) for a in names for b in names if a and b and a != b and re.search(r'\b%s\b' % re.escape(a), b)})
            t['plural'] = sorted({n for n in names if n and sing(n) != n})
            T.append(t)
    return T

def short_cite(text):
    l = refline(text)
    m = re.search(r'first seen (.*?)(?:\)|\.$|,| and each|$)', l)
    return (m.group(1) if m else l)[:40]

def show(t, k=0):
    E = 3 if t['ep'] == 'farthest' else 0
    v = t['v544'] or {}
    vs = '; '.join('%s %.2f' % (n, v[n]) for n in (t['ord544'] or []))
    fl = []
    c = {n: x for n, x in t['cnt'].items() if x}
    if c: fl.append('cnt%s' % c)
    if t['plural']: fl.append('pl%s' % t['plural'])
    if t['overlap']: fl.append('ov%s' % t['overlap'])
    tp = ('%.2f' % t['tp544']) if t['tp544'] else '-'
    print('#%d %s %s %s | ref=%s [200:%s | 544:%s] | T=%s | P200/100/544=%s/%s/%s | d=%s/%s/%s | tp544=%s m544=%.2f %s' % (
        k, t['id'][:14], t['set'][:2], t['ep'][:3], t['ref'], short_cite(t['text200']), short_cite(t['text544']), t['truth'],
        t['pick200'], t['pick100'], t['pick544'], t['d200'], t['d100'], t['d544'], tp, t['m544'] or 0, ' '.join(fl)))
    print('   200: %s || 100: %s || 544: %s' % (', '.join(t['ord200']), ', '.join(t['ord100']), vs))

LABEL_E = {  # read by hand: wording defect touching the reference or the truth (REPORT Q7)
    'ba14ba2ac2a20cfb282711e3': 'reference "adapter" is contained in the truth "power adapter"; step 544 gives power adapter 0.00 m',
    'fc7bcd5a41ea580a57516a22': 'truth "toilet flush button" is a part of the reference "toilet"',
    '5f8c9f829534c0f4a3b3727f': 'reference is the generic class "structure"',
    '927caec4a53e4ce8b3c76fa1': 'reference is the generic class "structure"',
}

def flags(t):
    f = {}
    f['near25'] = (t['tp544'] is not None and t['tp544'] <= 1.25) or (t['tp544'] is None and False)
    f['near33'] = (t['tp544'] is not None and t['tp544'] <= 4 / 3.)
    f['adj_all'] = all(t['d%d' % s] is not None and t['d%d' % s] <= 1 for s in (200, 100, 544))
    f['gross_all'] = all(t['d%d' % s] is not None and t['d%d' % s] >= 2 for s in (200, 100, 544))
    f['unstable'] = len({t['pick200'], t['pick100'], t['pick544']}) > 1
    f['b_mech'] = t['multi_truth'] or t['multi_ref'] or (t['truth'] in t['plural']) or (t['ref'] in t['plural'])
    f['b_any'] = t['multi_any'] or bool(t['plural'])
    f['e'] = t['id'] in LABEL_E
    return f

def primary(t):
    f = flags(t)
    if f['e']: return 'e'
    if f['near25'] or f['adj_all']: return 'a'
    if f['gross_all']: return 'c'
    if f['b_mech']: return 'b'
    if f['unstable']: return 'd'
    return 'other'

def price(items, T, s, ep=None):
    """type points, benchmark points (VSI: /8; ReVSI: leaf points x 1/2 / 7)."""
    N = sum(1 for t in T if t['set'] == s and (ep is None or t['ep'] == ep))
    loss = sum(1 - t['s200'] for t in items)
    tp = 100.0 * loss / N
    if s == 'dev-S1': return tp, tp / 8
    return tp, tp * 0.5 / 7
