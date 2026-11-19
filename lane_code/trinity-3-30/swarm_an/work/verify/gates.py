"""Step-N gates of lane swarm_an (STATUS.md, "Gates to read first"; their step-200 values are in that list).
usage: /usr/bin/python3 gates.py NEWSTEP            direct, facing and VSTI gates at steps 544, 200 and NEWSTEP
Scores and answers come from the scored arm (B2048); trace text from the full generation (ON16k).
A read that is not wired for NEWSTEP (kit/roots.json) is skipped and named. NEWSTEP 200 prints the 544 and 200 columns only."""
import sys, re, collections
sys.dont_write_bytecode = True
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
C = collections.Counter; DD = collections.defaultdict
NEW = int(sys.argv[1]) if len(sys.argv) > 1 else 200
STEPS = [('S1', 544), ('R1', 200)] + ([('R1', NEW)] if NEW != 200 else [])
LAB = ['%d' % s[1] for s in STEPS]
def num(x):
    try: return float(str(x).strip().split()[0])
    except Exception: return None
def mra(p, g):
    if p is None or g is None or g == 0: return 0.0
    e = abs(p - g) / abs(g); return sum(e <= 1 - t + 1e-9 for t in [0.5 + 0.05 * i for i in range(10)]) / 10.0
def mean(v): return sum(v) / float(len(v)) if v else float('nan')
def med(v):
    v = sorted(v); n = len(v)
    return float('nan') if not n else (v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0)
def think(r): return (r['text'] or '').split('</think>')[0].replace('<think>', '').strip()
def pct(rs): return '%.1f' % (100 * mean([r['score'] or 0.0 for r in rs])) if rs else '-'
def line(name, vals): print('  %-58s %s' % (name, ' | '.join('%s: %s' % (l, v) for l, v in zip(LAB, vals))))
def load(fn, *a):
    out = []
    for s in STEPS:
        try: out.append(fn(s[0], s[1], *a))
        except Exception as e: out.append(None); print('  [not loaded: %s %s %s: %s]' % (fn.__name__, s, a, str(e)[:80]))
    return out
def typ(rows, t, sub=None): return [r for r in rows if r['type'] == t and (sub is None or r.get('subtype') == sub)]
def each(sets, f): return [f(x) if x is not None else 'n/a' for x in sets]

S1 = load(K.direct, 'dev-S1'); R0 = load(K.direct, 'R0-dev')
R100 = {r['id']: r for st in ('dev-S1', 'R0-dev') for r in K.direct('R1', 100, st)}
ID = [dict((r['id'], r) for r in (a or []) + (b or [])) for a, b in zip(S1, R0)]

print('== G0 scores by type (B2048), steps', LAB)
for name, sets in (('dev-S1', S1), ('R0-dev', R0)):
    keys = sorted(set((r['type'], r.get('subtype')) for r in sets[1]))
    for k in keys:
        line('%s %s%s (%d)' % (name, k[0], '/' + k[1] if k[1] and k[1] not in ('first_seen', 'longest_dimension') and name == 'R0-dev' else '', len(typ(sets[1], k[0], k[1] if name == 'R0-dev' else None))),
             each(sets, lambda x: pct(typ(x, k[0], k[1] if name == 'R0-dev' else None))))

print('== G1 force-closed (runaway) items')
fc = lambda rs: '%d of %d' % (sum(bool(r['forced_close']) for r in rs), len(rs))
line('dev-S1 counting', each(S1, lambda x: fc(typ(x, 'object_counting'))))
line('R0-dev counting, all', each(R0, lambda x: fc(typ(x, 'object_counting'))))
line('R0-dev counting, single', each(R0, lambda x: fc(typ(x, 'object_counting', 'single'))))
line('R0-dev counting, multiple', each(R0, lambda x: fc(typ(x, 'object_counting', 'multiple'))))
line('dev-S1 relative count', each(S1, lambda x: fc(typ(x, 'relative_count'))))
line('every other type, both sets', each([(a or []) + (b or []) if a is not None and b is not None else None for a, b in zip(S1, R0)],
     lambda x: fc([r for r in x if r['type'] not in ('object_counting', 'relative_count')])))

LIST = re.compile(r'(first appearance|first-seen frame|first appears)[^:\n]*:|first seen in frame', re.I)
def form(r):
    t = think(r)
    if re.search(r'Step 2: match', t): return 'match-544'
    if LIST.search(t): return 'list'
    if re.search(r'count (it|each) once', t) and 'frame ' not in t.replace('across the frames', ''): return 'procedure'
    return 'other'
print('== G2 single-category counting outside the loops (each step on its own non-looping items)')
for name, sets, sub in (('dev-S1', S1, None), ('R0-dev', R0, 'single')):
    def nl(x): return [r for r in typ(x, 'object_counting', sub) if not r['forced_close']]
    line(name + ' items, non-looping', each(sets, lambda x: '%d, %d' % (len(typ(x, 'object_counting', sub)), len(nl(x)))))
    line(name + ' MRA all items', each(sets, lambda x: pct(typ(x, 'object_counting', sub))))
    line(name + ' MRA non-looping against a constant 2', each(sets, lambda x: '%s against %.1f' % (pct(nl(x)), 100 * mean([mra(2.0, num(r['gt'])) for r in nl(x)]))))
    line(name + ' non-looping answers equal to 2', each(sets, lambda x: '%d of %d' % (sum(num(r['pred']) == 2 for r in nl(x)), len(nl(x)))))
    line(name + ' trace form, non-looping', each(sets, lambda x: ', '.join('%s %d' % kv for kv in sorted(C(form(r) for r in nl(x)).items()))))
    line(name + ' procedure-only traces: n, MRA', each(sets, lambda x: '%d, %s' % (len([r for r in nl(x) if form(r) == 'procedure']), pct([r for r in nl(x) if form(r) == 'procedure']))))
    line(name + ' truth 2: right of non-looping', each(sets, lambda x: '%d of %d' % (sum(num(r['pred']) == 2 for r in nl(x) if num(r['gt']) == 2), sum(num(r['gt']) == 2 for r in nl(x)))))
    line(name + ' truth 3: undercounts of non-looping', each(sets, lambda x: '%d of %d' % (sum((num(r['pred']) or 0) < 3 for r in nl(x) if num(r['gt']) == 3), sum(num(r['gt']) == 3 for r in nl(x)))))
    line(name + ' truth 5 or more: MRA all items (n)', each(sets, lambda x: '%s (%d)' % (pct([r for r in typ(x, 'object_counting', sub) if num(r['gt']) >= 5]), sum(num(r['gt']) >= 5 for r in typ(x, 'object_counting', sub)))))
    if len(STEPS) == 3 and sets[2] is not None:
        both = [r for r in nl(sets[2]) if not ID[1][r['id']]['forced_close']]
        print('  %-58s %s: %s | %s: %s (n %d)' % (name + ' fixed items, non-looping at 200 and at ' + LAB[2], LAB[1], pct([ID[1][r['id']] for r in both]), LAB[2], pct(both), len(both)))
        was = [r for r in typ(sets[2], 'object_counting', sub) if ID[1][r['id']]['forced_close']]
        print('  %-58s n %d | at %s still looping %d | MRA 544 %s, 200 %s, %s %s' % (name + ' items that looped at 200', len(was), LAB[2], sum(bool(r['forced_close']) for r in was),
              pct([ID[0][r['id']] for r in was if r['id'] in ID[0]]), pct([ID[1][r['id']] for r in was]), LAB[2], pct(was)))

print('== G3 R0-dev multiple-category counting at a truth of 2')
def g3(x):
    t2 = [r for r in typ(x, 'object_counting', 'multiple') if num(r['gt']) == 2]; nr = [r for r in t2 if not r['forced_close']]
    return 'truth 2: %d, non-looping %d, right %d, over %d' % (len(t2), len(nr), sum(r['score'] >= 1 for r in nr), sum((num(r['pred']) or 0) > 2 for r in nr))
line('R0-dev multiple', each(R0, g3))

def noturn(r):
    t = think(r); return t.startswith('Step 1') and not re.search(r'half turn|flip forward', t)
def away(x): return [r for r in x if r['type'].startswith('object_rel_direction') and r.get('subtype') == 'away']
def tow(x): return [r for r in x if r['type'].startswith('object_rel_direction') and r.get('subtype') == 'toward']
print('== G4 R0-dev away direction (202 items)')
line('opening "Step 1: find"', each(R0, lambda x: '%d of %d' % (sum(think(r).startswith('Step 1: find') for r in away(x)), len(away(x)))))
line('opening "Seen:"', each(R0, lambda x: '%d' % sum(think(r).startswith('Seen:') for r in away(x))))
line('half turn omitted (wrong among them)', each(R0, lambda x: '%d (%d)' % (sum(noturn(r) for r in away(x)), sum(noturn(r) and r['score'] < 1 for r in away(x)))))
for lv in ('easy', 'medium', 'hard'):
    line('away %s right' % lv, each(R0, lambda x: '%d of %d' % (sum(r['score'] >= 1 for r in away(x) if r['type'].endswith(lv)), sum(r['type'].endswith(lv) for r in away(x)))))
if len(STEPS) == 3 and R0[2] is not None:
    lost = [r for r in away(R0[2]) if noturn(r) and not noturn(ID[1][r['id']])]; got = [r for r in away(R0[2]) if not noturn(r) and noturn(ID[1][r['id']])]
    print('  turn lost since 200: %d (right now %d, right at 200 %d) | turn regained: %d (right now %d, right at 200 %d)' % (len(lost), sum(r['score'] >= 1 for r in lost),
          sum(ID[1][r['id']]['score'] >= 1 for r in lost), len(got), sum(r['score'] >= 1 for r in got), sum(ID[1][r['id']]['score'] >= 1 for r in got)))

print('== G5 R0-dev toward direction (376 items)')
line('wrong', each(R0, lambda x: '%d of %d' % (sum(r['score'] < 1 for r in tow(x)), len(tow(x)))))
for lv in ('easy', 'medium', 'hard'):
    line('toward %s wrong' % lv, each(R0, lambda x: '%d of %d' % (sum(r['score'] < 1 for r in tow(x) if r['type'].endswith(lv)), sum(r['type'].endswith(lv) for r in tow(x)))))
aw3 = [r for r in tow(R0[1]) if r['score'] < 1 and ID[0][r['id']]['score'] < 1 and R100[r['id']]['score'] < 1]
print('  wrong at 544, 100 and 200: %d; same option at 544 and 200: %d' % (len(aw3), sum(ID[0][r['id']]['pred'] == r['pred'] for r in aw3)))
if len(STEPS) == 3 and R0[2] is not None:
    print('  of those %d at %s: still wrong %d, same option as at 200 %d, now right %d' % (len(aw3), LAB[2], sum(ID[2][r['id']]['score'] < 1 for r in aw3),
          sum(ID[2][r['id']]['pred'] == r['pred'] for r in aw3), sum(ID[2][r['id']]['score'] >= 1 for r in aw3)))
line('dev-S1 direction (450) wrong', each(S1, lambda x: '%d' % sum(r['score'] < 1 for r in x if r['type'].startswith('object_rel_direction'))))

FR = re.compile(r'frames? (\d+(?:\.\d+)?)')
def gt32(rs):
    n = 0
    for r in rs:
        v = [float(a) for a in FR.findall(think(r))]
        n += bool(v) and max(v) > 32
    return '%d of %d' % (n, len(rs))
print('== G6 traces that cite a frame above 32')
line('R0-dev appearance order', each(R0, lambda x: gt32(typ(x, 'obj_appearance_order'))))
line('R0-dev counting', each(R0, lambda x: gt32(typ(x, 'object_counting'))))
line('R0-dev direction', each(R0, lambda x: gt32([r for r in x if r['type'].startswith('object_rel_direction')])))
line('R0-dev relative distance', each(R0, lambda x: gt32(typ(x, 'object_rel_distance'))))

def app(rs):
    def frames(r):
        m = re.search(r'Step 1:[^\n]*?:(.*)', think(r))
        if not m: return None
        out = {}
        for part in m.group(1).split(';'):
            mm = re.match(r'\s*(.+?)\s+frame\s+([\d.]+)', part.strip().rstrip('.'))
            if mm: out[mm.group(1).strip().lower()] = float(mm.group(2))
        return out
    def lcp(a, b):
        n = 0
        for x, y in zip(a, b):
            if x != y: break
            n += 1
        return n
    agree = right = n = 0.0; first = C()
    for r in rs:
        oo = dict((o[0], [x.strip().lower() for x in o.split('.', 1)[1].split(',')]) for o in r['options']); truth = oo[str(r['gt']).strip()[0]]
        f = frames(r)
        if not f or set(f) != set(truth): continue
        n += 1; order = sorted(f, key=lambda x: f[x])
        best = max(lcp(order, o) for o in oo.values()); cands = [k for k, o in oo.items() if lcp(order, o) == best]
        if len(cands) > 1:
            def pa(o): return sum(order.index(o[i]) < order.index(o[j]) for i in range(4) for j in range(i + 1, 4))
            m = max(pa(oo[k]) for k in cands); cands = [k for k in cands if pa(oo[k]) == m]
        pl = str(r['pred']).strip()[:1]
        if pl in cands: agree += 1.0 / len(cands)
        if str(r['gt']).strip()[0] in cands: right += 1.0 / len(cands)
        first[(r['score'] >= 1, f[truth[0]] <= 2)] += 1
    return 'parsed %d of %d; decoder equals the answer %.0f, the truth %.0f; truly-first cited at frame 1 or 2: wrong %d of %d, right %d of %d' % (
        n, len(rs), agree, right, first[(False, True)], first[(False, True)] + first[(False, False)], first[(True, True)], first[(True, True)] + first[(True, False)])
print('== G7 appearance order: the answer against the stated first-seen frames (step 544 states no such list in this form)')
for l, x in zip(LAB, R0):
    if x is not None: print('  %s: %s' % (l, app(typ(x, 'obj_appearance_order'))))

print('== G8 object size')
DS = {'d1': 'ScanNet', 'd2': 'ScanNet++', 'd3': 'ARKitScenes'}
for k in ('d1', 'd2', 'd3'):
    line('dev-S1 %s (%d)' % (DS[k], sum(str(r['room']).startswith(k + '/') for r in typ(S1[1], 'object_size_estimation'))),
         each(S1, lambda x: pct([r for r in typ(x, 'object_size_estimation') if str(r['room']).startswith(k + '/')])))
def ratio(x, lo, hi):
    v = [num(r['pred']) / num(r['gt']) for r in typ(x, 'object_size_estimation') if num(r['pred']) and num(r['gt']) and lo <= num(r['gt']) < hi]
    rs = [r for r in typ(x, 'object_size_estimation') if num(r['gt']) and lo <= num(r['gt']) < hi]
    return 'median %.2f, MRA %s (n %d)' % (med(v), pct(rs), len(rs))
for lo, hi, nm in ((0, 30, 'under 30'), (30, 60, '30 to 60'), (60, 120, '60 to 120'), (120, 250, '120 to 250'), (250, 1e9, '250 or more')):
    line('R0-dev answer over truth, truth %s cm' % nm, each(R0, lambda x: ratio(x, lo, hi)))

print('== G9 relative distance by the margin of step 544 between its two endpoint candidates (both sets, 429 items)')
try:
    sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_reldist/work'); import rd
    T = rd.table()
    for nm, f in (('margin under 1.25', lambda t: t['m544'] is not None and t['m544'] < 1.25), ('margin 1.25 to 2', lambda t: t['m544'] is not None and 1.25 <= t['m544'] < 2.0),
                  ('margin 2 or more', lambda t: t['m544'] is not None and t['m544'] >= 2.0), ('no margin parsed', lambda t: t['m544'] is None)):
        ids = [t['id'] for t in T if f(t)]
        line('%s (%d)' % (nm, len(ids)), ['%d right' % sum(d[i]['score'] >= 1 for i in ids if i in d) for d in ID])
except Exception as e:
    print('  [margin table not available: %s]' % str(e)[:120])
line('R0-dev closest right', each(R0, lambda x: '%d of %d' % (sum(r['score'] >= 1 for r in typ(x, 'object_rel_distance', 'closest')), len(typ(x, 'object_rel_distance', 'closest')))))
line('R0-dev farthest right', each(R0, lambda x: '%d of %d' % (sum(r['score'] >= 1 for r in typ(x, 'object_rel_distance', 'farthest')), len(typ(x, 'object_rel_distance', 'farthest')))))

print('== G10 facing twins')
for tw in ('away', 'forward'):
    F = load(K.facing, tw)
    for lv in ('easy', 'medium', 'hard'):
        line('%s twins %s right' % (tw, lv), each(F, lambda x: '%d of %d' % (sum(r['score'] >= 1 for r in x if r['type'].endswith(lv)), sum(r['type'].endswith(lv) for r in x))))
    if tw == 'away':
        line('away twins: half turn omitted (wrong among them)', each(F, lambda x: '%d (%d)' % (sum(noturn(r) for r in x), sum(noturn(r) and r['score'] < 1 for r in x))))
        line('away twins: "back" answers on hard', each(F, lambda x: '%d of %d' % (sum('back' in str(dict((o[0], o) for o in r['options']).get(str(r['pred']).strip()[:1], '')).lower() for r in x if r['type'].endswith('hard')), sum(r['type'].endswith('hard') for r in x))))
        line('away twins citing a frame above 32', each(F, gt32))

print('== G11 VSTI relative dev set')
V = load(K.vsti)
for t in sorted(set(r['type'] for r in V[1])):
    line('%s (150)' % t, each(V, lambda x: pct(typ(x, t))))
line('VSTI traces citing a frame above 32', each(V, gt32))
def lastopt(x, t):
    rs = typ(x, t); return '%d chosen, %d true' % (sum(str(r['pred']).strip()[:1] == r['options'][-1][0] for r in rs), sum(str(r['gt']).strip()[:1] == r['options'][-1][0] for r in rs))
for t in ('camera_obj_rel_dist_v1', 'camera_obj_rel_dist_v2', 'camera_obj_rel_dist_v3'):
    line('%s last option' % t, each(V, lambda x: lastopt(x, t)))
def klocate(x):
    cam = [r for r in x if r['type'].startswith('camera')]; n = 0
    for r in cam:
        m = re.search(r'frame (\d+) of 32', r['question'])
        n += bool(m) and bool(re.search(r'in view in frame %s\b|out of view in frame %s\b' % (m.group(1), m.group(1)), think(r)))
    return '%d of %d' % (n, len(cam))
line('camera items with an in-view or out-of-view line at k', each(V, klocate))
print('sources read:', len(K.SOURCES))
