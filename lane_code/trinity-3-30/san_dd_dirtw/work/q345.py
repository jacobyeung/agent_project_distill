"""Q3 (instances), Q4 (object size, name rarity), Q5 (rooms) for toward items; R0-dev and dev-S1.  Writes q345_items.json (small)."""
import sys, json, re, sqlite3, random, collections, csv, statistics as stt
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_dirtw/work'); from tw_lib import *
def norm(n):
    n = n.lower().strip().replace('(s)', '')
    for a, b in (('shelves', 'shelf'), ('ies', 'y'), ('boxes', 'box'), ('glasses', 'glass'), ('dishes', 'dish'), ('brushes', 'brush'), ('benches', 'bench'), ('couches', 'couch')):
        if n.endswith(a): return n[:-len(a)] + b
    if n.endswith('ss'): return n
    return n[:-1] if n.endswith('s') else n
UNIT = {'centimeter': 1, 'centimeters': 1, 'cm': 1, 'meter': 100, 'meters': 100, 'm': 100, 'inch': 2.54, 'inches': 2.54, 'feet': 30.48, 'foot': 30.48, 'millimeter': .1, 'millimeters': .1, 'mm': .1}
CNT = re.compile(r"How many (.+?)(?:\(s\))? (?:do|are|can|is|exist|in |are there)", re.I)
SZ0 = re.compile(r"(?:of|for) the ([a-z0-9][a-z0-9 '\-/]*?)(?=,| in | measured|\?| using|\.| when)", re.I)
class _SZ:
    def search(self, q):
        m = [x for x in SZ0.finditer(q) if not x.group(1).lower().startswith(('longest', 'length', 'largest', 'biggest', 'greatest', 'maximum', 'object', 'item'))]
        return m[-1] if m else None
SZ = _SZ()
def unit_of(q, u):
    m = re.search(r"\b(centimeters?|meters?|inches|inch|feet|foot|millimeters?|cm|mm)\b", q, re.I)
    return UNIT.get(m.group(1).lower(), 1) if m else 1
def room_tables(rows):
    cnt = collections.defaultdict(dict); size = collections.defaultdict(dict)
    for r in rows:
        if r['type'] == 'object_counting' and r.get('subtype') in (None, 'single'):
            m = CNT.search(r['question'])
            if m:
                try: cnt[r['room']][norm(m.group(1))] = float(r['gt'])
                except Exception: pass
        if r['type'] == 'object_size_estimation':
            m = SZ.search(r['question'])
            if m:
                try: size[r['room']][norm(m.group(1))] = float(r['gt']) * unit_of(r['question'], r.get('unit'))
                except Exception: pass
    return cnt, size
# training size medians (3,000 size rows by primary key) and direction-name counts (2,000 direction rows by primary key)
F = json.load(open('/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json'))['families']
con = sqlite3.connect('file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro', uri=True)
def fetch(ids):
    out = []
    for k in range(0, len(ids), 200):
        out += [json.loads(r) for i, r in con.execute('select i,row from rows where i in (%s)' % ','.join(map(str, ids[k:k + 200])))]
    return out
sid = [i for a, b in F['object_size_estimation'] for i in range(a, b + 1)]; print('size rows in store v7:', len(sid)); random.seed(5); S = sorted(random.sample(sid, min(len(sid), 12000)))
med = collections.defaultdict(list)
for j in fetch(S):
    q = j['student_input']['question']; m = SZ.search(q)
    try: v = float(j['answer']) * unit_of(q, None)
    except Exception: continue
    if m: med[norm(m.group(1))].append(v)
MED = {k: stt.median(v) for k, v in med.items()}
did = [i for t in T for a, b in F[t] for i in range(a, b + 1)]; random.seed(7); S2 = sorted(random.sample(did, 2000))
DQ = [j['student_input']['question'].split('\n')[0].lower() for j in fetch(S2)]
_nc = {}
def ncount(n):
    n = n.lower()
    if n not in _nc:
        p = re.compile(r"\bthe " + re.escape(n) + r"(?![a-z])"); _nc[n] = sum(1 for q in DQ if p.search(q))
    return _nc[n]
print('size rows sampled 3000 -> classes', len(MED), '; direction questions', len(DQ))
cnt_rooms = {}
def table(setname):
    allr = K.direct('R1', 200, setname); cnt, size = room_tables(allr); cnt_rooms[setname] = cnt
    t544 = {r['id']: r for r in K.direct('S1', 544, setname, types=T)}
    out = []
    for r in allr:
        if r['type'] not in T: continue
        if setname == 'R0-dev' and re.search(r"opposite direction|away from|my back to", r['question'].split('\n')[0], re.I): continue
        if setname == 'R0-dev' and r['subtype'] != 'toward': continue
        o = names3(r['question'])
        if None in o: continue
        cs = [cnt[r['room']].get(norm(n)) for n in o]
        sz = [size[r['room']].get(norm(n)) for n in o]; szs = ['room' if s is not None else ('train' if MED.get(norm(n)) else None) for s, n in zip(sz, o)]
        sz = [s if s is not None else (MED.get(norm(n)) or MED.get(norm(n).split(' ')[-1])) for s, n in zip(sz, o)]
        out.append(dict(id=r['id'], lv=LV[r['type']], room=r['room'], objs=o, s200=r['score'], s544=(t544.get(r['id']) or {}).get('score'),
                        counts=cs, sizes=sz, size_src=szs, ncnt=[ncount(n) for n in o]))
    return out
res = {}
for st in ('R0-dev', 'dev-S1'):
    X = table(st); res[st] = X
    print('==', st, 'toward items', len(X))
    # Q3 instances
    def has2(x): return any(c is not None and c >= 2 for c in x['counts'])
    def known(x): return sum(c is not None for c in x['counts'])
    for nm, f in (('any named class counted >=2', has2),):
        for lab, sel in (('wrong@200', lambda x: x['s200'] == 0), ('right@200', lambda x: x['s200'] == 1)):
            Y = [x for x in X if sel(x)]
            print('  Q3 %s: %s %d of %d (items with >=1 counted name: %d)' % (lab, nm, sum(f(x) for x in Y), len(Y), sum(known(x) > 0 for x in Y)))
    rolec = collections.Counter()
    for x in X:
        for k, c in zip('OFT', x['counts']):
            if c is not None and c >= 2: rolec[(k, x['s200'])] += 1
    print('  Q3 role of the >=2 class (role, score200):', sorted(rolec.items()))
    # Q4 bands
    def band_size(x):
        s = [v for v in x['sizes'] if v is not None]
        if len(s) < 3: return 'unknown'
        m = min(s); return '<30cm' if m < 30 else ('30-100cm' if m <= 100 else '>100cm')
    def band_name(x):
        m = min(x['ncnt']); return '0' if m == 0 else ('1-9' if m < 10 else '>=10')
    for nm, f in (('smallest object size', band_size), ('rarest name count in 2,000 rows', band_name)):
        b = collections.defaultdict(lambda: [0, 0, 0])
        for x in X:
            k = f(x); b[k][0] += 1; b[k][1] += x['s200'] or 0; b[k][2] += x['s544'] or 0
        print('  Q4 %s: %s' % (nm, {k: '%d items, %.0f%% @200, %.0f%% @544' % (v[0], 100 * v[1] / v[0], 100 * v[2] / v[0]) for k, v in sorted(b.items())}))
    print('  size source of the three objects:', collections.Counter(s for x in X for s in x['size_src']), 'with a size (incl. head-noun median):', sum(v is not None for x in X for v in x['sizes']))
    cr = collections.Counter(); 
    for x in X: cr[(sum(c is not None for c in x['counts']))] += 1
    print('  counted names per item:', sorted(cr.items()), '; rooms with counting items:', len(cnt_rooms[st]), 'classes counted:', sum(len(v) for v in cnt_rooms[st].values()))
json.dump(res, open('q345_items.json', 'w'))
