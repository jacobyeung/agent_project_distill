K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1
cat > $K/kit/score_v1.py <<'PYEOF'
"""nvkey2 V1 scoring against K1 raster truth at the 32 anchors (rasters K/k1r; truth summaries K/v1/truth; near-miss truth K/v1/NEARMISS_TRUTH.json).
usage: score_v1.py a OUT.jsonl [...]   (guided names + decoys: presence by band, decoys, points, counts, first frames, kind position, two-family agreement)
       score_v1.py b OUT.jsonl [...]   (blind inventory: recall of ground-truth instances, annotated-vocabulary precision, points, cross-family extras)
       score_v1.py c OUT.jsonl [...]   (judge form: near-miss truth and pilot agreement)
Writes K/scores/V1<form>.json. Intervals: capture-clustered bootstrap (2,000 draws)."""
import json, os, re, sys, random, collections, math
import numpy as np
K = os.environ.get('NVK', '/scratch/jjyeung/orch_n30/nvkey1/work'); VIS = 0.002
SYN = [{'sofa', 'couch', 'loveseat', 'settee'}, {'tv', 'television', 'monitor', 'screen', 'computer monitor', 'display'}, {'refrigerator', 'fridge'},
       {'trash can', 'trash bin', 'garbage can', 'wastebasket', 'bin', 'waste bin', 'trashcan', 'garbage bin', 'recycling bin'},
       {'bookshelf', 'bookcase', 'shelf', 'shelving', 'shelves', 'shelving unit'}, {'nightstand', 'bedside table', 'night table'}, {'cabinet', 'cupboard', 'kitchen cabinet', 'file cabinet'},
       {'lamp', 'floor lamp', 'table lamp', 'desk lamp'}, {'picture', 'painting', 'poster', 'artwork', 'framed picture', 'photo', 'frame'}, {'plant', 'potted plant', 'houseplant'},
       {'pillow', 'cushion', 'throw pillow'}, {'curtain', 'drape', 'drapes', 'curtains'}, {'blinds', 'window blind', 'shade', 'window shade'}, {'counter', 'countertop', 'kitchen counter'},
       {'stool', 'bar stool'}, {'chair', 'armchair', 'office chair', 'dining chair', 'desk chair'}, {'table', 'coffee table', 'dining table', 'side table', 'end table', 'desk'},
       {'toilet', 'wc'}, {'sink', 'basin', 'washbasin'}, {'washer', 'washing machine'}, {'stove', 'oven', 'range', 'cooktop', 'stovetop'}, {'microwave', 'microwave oven'},
       {'door', 'doorway', 'cabinet door'}, {'window'}, {'bed'}, {'bathtub', 'tub', 'bath'}, {'whiteboard', 'white board', 'dry erase board'}, {'radiator', 'heater'},
       {'dresser', 'chest of drawers', 'drawers'}, {'wardrobe', 'closet', 'armoire'}, {'mirror'}, {'printer'}, {'computer tower', 'desktop computer', 'pc tower', 'computer'}, {'backpack', 'bag'}]
STRUCT = {'wall', 'floor', 'ceiling', 'object', 'objects', 'otherfurniture', 'otherprop', 'otherstructure', 'unknown', 'misc', 'structure', 'doorframe', 'beam', 'pipe', 'column'}
def norm(l):
    l = str(l).lower().replace('_', ' ').strip(); return {'tv monitor': 'tv', 'television': 'tv'}.get(l, l)
def head(l):
    h = l.split()[-1] if l.split() else l; return h[:-1] if h.endswith('s') and not h.endswith('ss') else h
def names_match(a, b):
    a, b = norm(a), norm(b)
    if a == b or head(a) == head(b): return True
    return any((a in s or head(a) in s) and (b in s or head(b) in s) for s in SYN)
def parse(t):
    if not t: return None
    t = t.strip(); t = re.sub(r'^```(json)?', '', t).strip(); t = re.sub(r'```$', '', t).strip()
    for cand in (t, t[t.find('{'):t.rfind('}') + 1]):
        for fix in (lambda x: x, lambda x: re.sub(r',\s*([}\]])', r'\1', x)):
            try: return json.loads(fix(cand))
            except Exception: pass
    return None
def boot(units, f, n=2000):
    caps = sorted(units); rng = random.Random(7); vals = []
    for _ in range(n):
        v = f([u for c in (rng.choice(caps) for _ in caps) for u in units[c]])
        if v is not None: vals.append(v)
    vals.sort(); return [round(vals[int(0.025 * len(vals))], 1), round(vals[int(0.975 * len(vals)) - 1], 1)] if vals else None
def pct(xs):
    xs = [x for x in xs if x is not None]; return round(100.0 * sum(bool(x) for x in xs) / len(xs), 1) if xs else None
def stat(rows, key, cap='alias'):
    by = collections.defaultdict(list)
    for r in rows: by[r[cap]].append(r[key])
    return [pct([r[key] for r in rows]), boot(by, pct), sum(1 for r in rows if r[key] is not None)]
_R = {}
def raster(t):
    if t['alias'] not in _R:
        z = np.load(K + '/k1r/' + t['raster'], allow_pickle=True)
        _R[t['alias']] = dict(inst=z['inst'], ids=[int(x) for x in z['ids']], labels=[norm(x) for x in z['labels']])
    return _R[t['alias']]
def lab2anchor(label, meta):
    try: L = int(label)
    except Exception: return None
    if meta['n'] == 32: return L - 1 if 1 <= L <= 32 else None
    slots = meta['slots']; return slots.index(L - 1) if (L - 1) in slots else None
def lab2anchor_ceil(L, meta):
    if meta['n'] == 32: return L - 1
    for k, s in enumerate(meta['slots']):
        if s >= L - 1: return k
    return 31
def inside(t, R, ids, k, p):
    if not (isinstance(p, (list, tuple)) and len(p) == 2): return None
    try: x, y = float(p[0]), float(p[1])
    except Exception: return None
    W, H = t['W'], t['H']; xi = min(W - 1, max(0, int(x / 1000.0 * W))); yi = min(H - 1, max(0, int(y / 1000.0 * H)))
    return bool(np.isin(R['inst'][k][yi, xi], ids))
def band(s): return 'absent' if s == 0 else ('sliver' if s < VIS else ('0.2-1%' if s < 0.01 else ('1-5%' if s < 0.05 else '>=5%')))
def form_a(files):
    facts = []; objs = []; per_call = {}
    for fn in files:
        for l in open(fn):
            r = json.loads(l); m = r['meta']; t = json.load(open(K + '/v1/truth/%s.json' % m['alias'])); R = raster(t); d = parse(r['text'])
            fam = r['model'].split('/')[-1]; key = (fam, m['n']); per_call[(key, m['alias'])] = d is not None
            cls = {c['name']: c for c in t['classes']}
            for pos, kind in enumerate(m['kinds']):
                e = (d or {}).get(kind) if isinstance(d, dict) else None; e = e if isinstance(e, dict) else None
                frames = set()
                if e and isinstance(e.get('frames'), list):
                    for L in e['frames']:
                        k = lab2anchor(L, m)
                        if k is not None: frames.add(k)
                pts = e.get('points') if e and isinstance(e.get('points'), dict) else {}
                apts = {}
                for L, p in pts.items():
                    k = lab2anchor(L, m)
                    if k is not None: apts[k] = p
                c = cls.get(kind); ids = c['ids'] if c else []
                for k in range(32):
                    if t['missing'][k]: continue
                    s = c['share'][k] if c else 0.0; b = band(s) if c else 'decoy'
                    if b == 'sliver': continue
                    said = None if e is None else (k in frames)
                    hit = inside(t, R, ids, k, apts.get(k)) if (said and c and s >= VIS) else None
                    facts.append(dict(key=key, alias=m['alias'], kind=kind, k=k, band=b, truth=(s >= VIS) if c else False, said=said,
                                      ok=None if said is None else (said == ((s >= VIS) if c else False)), hit=hit, pos=pos / max(1, len(m['kinds'])), ds=t['dataset'],
                                      pt=apts.get(k)))
                tc = c['count'] if c else 0; mc = e.get('count') if e else None
                try: mc = int(mc)
                except Exception: mc = None
                mf = []
                if e and isinstance(e.get('instances'), list):
                    for it in e['instances']:
                        try: mf.append(lab2anchor_ceil(int(it.get('first_frame')), m))
                        except Exception: pass
                tf = c['first_frames'] if c else []
                pair = []
                if tf and mf:
                    a, bq = sorted(tf), sorted(mf); used = set()
                    for x in a:
                        j = min((j for j in range(len(bq)) if j not in used), key=lambda j: abs(bq[j] - x), default=None)
                        if j is not None: used.add(j); pair.append(abs(bq[j] - x) <= 1)
                        else: pair.append(False)
                objs.append(dict(key=key, alias=m['alias'], kind=kind, decoy=c is None, tc=tc, mc=mc, exact=None if mc is None else mc == tc,
                                 within1=None if mc is None else abs(mc - tc) <= 1, first_ok=pair, ds=t['dataset']))
    res = collections.OrderedDict()
    for key in sorted(set(f['key'] for f in facts)):
        F = [f for f in facts if f['key'] == key]; O = [o for o in objs if o['key'] == key]; o = collections.OrderedDict(); tag = '%s|f%d' % key
        o['calls_parsed'] = '%d/%d' % (sum(v for (kk, a), v in per_call.items() if kk == key), sum(1 for (kk, a) in per_call if kk == key))
        o['presence_>=1%'] = stat([f for f in F if f['band'] in ('>=5%', '1-5%')], 'ok')
        for b in ('>=5%', '1-5%', '0.2-1%', 'absent', 'decoy'): o['presence_' + b] = stat([f for f in F if f['band'] == b], 'ok')
        o['point_>=1%'] = stat([f for f in F if f['band'] in ('>=5%', '1-5%') and f['said']], 'hit')
        o['point_>=5%'] = stat([f for f in F if f['band'] == '>=5%' and f['said']], 'hit')
        o['point_1-5%'] = stat([f for f in F if f['band'] == '1-5%' and f['said']], 'hit')
        for ds in ('arkitscenes', 'scannet', 'scannetpp'):
            o['presence_>=1%_' + ds] = stat([f for f in F if f['ds'] == ds and f['band'] in ('>=5%', '1-5%')], 'ok')[0]
            o['point_>=1%_' + ds] = stat([f for f in F if f['ds'] == ds and f['band'] in ('>=5%', '1-5%') and f['said']], 'hit')[0]
        for q in range(4): o['presence_kindpos_q%d' % (q + 1)] = pct([f['ok'] for f in F if int(f['pos'] * 4) == q and f['band'] in ('>=5%', '1-5%', 'absent')])
        o['decoy_count0'] = pct([x['mc'] == 0 for x in O if x['decoy'] and x['mc'] is not None])
        T = [x for x in O if not x['decoy'] and 1 <= x['tc'] <= 4]; o['count_exact_truth1-4'] = stat(T, 'exact'); o['count_within1_truth1-4'] = stat(T, 'within1')
        o['count_exact_all'] = stat([x for x in O if not x['decoy']], 'exact')
        fo = [v for x in O if not x['decoy'] for v in x['first_ok']]; o['first_frame_within1'] = [pct(fo), len(fo)]
        res[tag] = o
    fams = sorted(set(f['key'][0] for f in facts))
    for n in sorted(set(f['key'][1] for f in facts)):
        if len(fams) < 2: break
        A = {(f['alias'], f['kind'], f['k']): f for f in facts if f['key'] == (fams[0], n)}; B = {(f['alias'], f['kind'], f['k']): f for f in facts if f['key'] == (fams[1], n)}
        both = [(A[x], B[x]) for x in A if x in B and A[x]['said'] is not None and B[x]['said'] is not None]
        sc = [(a, b) for a, b in both if a['band'] in ('>=5%', '1-5%', 'absent', 'decoy')]
        agree = [(a, b) for a, b in sc if a['said'] == b['said']]
        o = collections.OrderedDict(); o['facts_scored'] = len(sc); o['kept_share'] = round(100.0 * len(agree) / max(1, len(sc)), 1)
        by = collections.defaultdict(list)
        for a, b in agree: by[a['alias']].append(a['ok'])
        o['agreed_presence_correct'] = [pct([a['ok'] for a, b in agree]), boot(by, pct), len(agree)]
        pp = []
        for a, b in agree:
            if a['said'] and a['truth'] and a['band'] in ('>=5%', '1-5%') and isinstance(a['pt'], (list, tuple)) and isinstance(b['pt'], (list, tuple)) and len(a['pt']) == 2 and len(b['pt']) == 2:
                try: dist = math.hypot(float(a['pt'][0]) - float(b['pt'][0]), float(a['pt'][1]) - float(b['pt'][1])) / (1000.0 * math.sqrt(2))
                except Exception: continue
                pp.append((a, dist <= 0.05))
        kept = [a for a, ok in pp if ok]; o['points_agree_within5pct_share'] = pct([ok for a, ok in pp]); o['agreed_points_in_mask'] = [pct([a['hit'] for a in kept]), len(kept)]
        res['agree|%s+%s|f%d' % (fams[0], fams[1], n)] = o
    return res
def form_b(files):
    res = collections.OrderedDict(); recs = collections.defaultdict(list); inv = {}
    for fn in files:
        for l in open(fn):
            r = json.loads(l); m = r['meta']; t = json.load(open(K + '/v1/truth/%s.json' % m['alias'])); R = raster(t); d = parse(r['text'])
            fam = r['model'].split('/')[-1]; key = (fam, m['n']); items = (d or {}).get('instances') if isinstance(d, dict) else None
            items = [x for x in (items or []) if isinstance(x, dict)]
            area = float(t['H'] * t['W']); gts = []
            for i, lab in zip(R['ids'], R['labels']):
                sh = [float((R['inst'][k] == i).sum()) / area if not t['missing'][k] else 0.0 for k in range(32)]
                if max(sh) >= 0.01 and lab not in STRUCT: gts.append(dict(id=i, label=lab, share=sh))
            vocab = set(R['labels']); found_named = {g['id']: False for g in gts}; found_loc = dict(found_named); prec = []; ptok = []; extras = []
            for it in items:
                nm = [str(it.get('name', ''))] + [str(a) for a in (it.get('aliases') or [])][:2]
                pts = it.get('points') if isinstance(it.get('points'), dict) else {}
                hits = collections.Counter(); npts = 0
                for L, p in pts.items():
                    k = lab2anchor(L, m)
                    if k is None or t['missing'][k] or not (isinstance(p, (list, tuple)) and len(p) == 2): continue
                    try: xi = min(t['W'] - 1, max(0, int(float(p[0]) / 1000.0 * t['W']))); yi = min(t['H'] - 1, max(0, int(float(p[1]) / 1000.0 * t['H'])))
                    except Exception: continue
                    npts += 1; v = int(R['inst'][k][yi, xi])
                    if v in R['ids']: hits[v] += 1
                lab_of = dict(zip(R['ids'], R['labels']))
                named = any(names_match(a, lab) for a in nm for lab in vocab)
                for g in gts:
                    if hits.get(g['id']):
                        found_loc[g['id']] = True
                        if any(names_match(a, g['label']) for a in nm): found_named[g['id']] = True
                if named:
                    ok = any(hits.get(i) and any(names_match(a, lab_of[i]) for a in nm) for i in hits)
                    prec.append(ok)
                    best = max(hits, key=hits.get) if hits else None
                    if best is not None and any(names_match(a, lab_of[best]) for a in nm): ptok.append(hits[best] / max(1, npts))
                else: extras.append(dict(name=nm[0], pts={lab2anchor(L, m): p for L, p in pts.items() if lab2anchor(L, m) is not None}))
            inv[(key, m['alias'])] = extras
            recs[key].append(dict(alias=m['alias'], ds=t['dataset'], parsed=d is not None, n_items=len(items), n_gt=len(gts), named=list(found_named.values()),
                                  loc=list(found_loc.values()), prec=prec, ptok=ptok, n_extra=len(extras)))
    for key, rows in sorted(recs.items()):
        o = collections.OrderedDict(); u = {r['alias']: [r] for r in rows}
        def agg(rs, f):
            xs = [x for r in rs for x in r[f]]; return round(100.0 * sum(xs) / len(xs), 1) if xs else None
        o['calls_parsed'] = '%d/%d' % (sum(r['parsed'] for r in rows), len(rows)); o['items_per_call'] = round(sum(r['n_items'] for r in rows) / len(rows), 1)
        o['recall_named_>=1%'] = [agg(rows, 'named'), boot(u, lambda rs: agg(rs, 'named')), sum(len(r['named']) for r in rows)]
        o['recall_located_>=1%'] = [agg(rows, 'loc'), boot(u, lambda rs: agg(rs, 'loc'))]
        o['precision_annotated_vocab'] = [agg(rows, 'prec'), boot(u, lambda rs: agg(rs, 'prec')), sum(len(r['prec']) for r in rows)]
        o['points_on_matched_instance'] = round(100.0 * sum(x for r in rows for x in r['ptok']) / max(1, sum(len(r['ptok']) for r in rows)), 1)
        o['extras_per_call'] = round(sum(r['n_extra'] for r in rows) / len(rows), 1)
        for ds in ('arkitscenes', 'scannet', 'scannetpp'):
            S = [r for r in rows if r['ds'] == ds]; o['recall_named_' + ds] = agg(S, 'named'); o['precision_' + ds] = agg(S, 'prec')
        res['%s|f%d' % key] = o
    fams = sorted(set(k[0] for k in recs))
    if len(fams) >= 2:
        for n in sorted(set(k[1] for k in recs)):
            agreed = tot = 0; ark_out = ark_tot = 0
            for (key, alias), ex in inv.items():
                if key != (fams[0], n): continue
                other = inv.get(((fams[1], n), alias), [])
                for e in ex:
                    tot += 1
                    ok = any(names_match(e['name'], o2['name']) and any(k in o2['pts'] and isinstance(p, (list, tuple)) and isinstance(o2['pts'][k], (list, tuple)) and len(p) == 2 and len(o2['pts'][k]) == 2 and
                             math.hypot(float(p[0]) - float(o2['pts'][k][0]), float(p[1]) - float(o2['pts'][k][1])) / (1000.0 * math.sqrt(2)) <= 0.05 for k, p in e['pts'].items()) for o2 in other)
                    agreed += ok
            res['extras_cross_family_agreed|%s+%s|f%d' % (fams[0], fams[1], n)] = [round(100.0 * agreed / max(1, tot), 1), tot]
    return res
def form_c(files):
    nm = {r['id']: r for r in json.load(open(K + '/v1/NEARMISS_TRUTH.json'))} if os.path.exists(K + '/v1/NEARMISS_TRUTH.json') else {}
    V = collections.defaultdict(dict); kinds = {}
    for fn in files:
        for l in open(fn):
            r = json.loads(l); d = parse(r['text']) or {}; fam = r['model'].split('/')[-1]; m = r['meta']
            for rid in m['rows']:
                v = d.get(rid) if isinstance(d, dict) else None
                if isinstance(v, dict): v = v.get('verdict')
                V[(fam, m['set'])][rid] = str(v).strip().lower() if v is not None else None
    res = collections.OrderedDict()
    def doubt(v, kind):
        if v is None or v == 'unsure': return None
        return v in ('off', 'wrong_name', 'absent') if kind == 'point' else v == 'visible'
    for (fam, st), vs in sorted(V.items()):
        if st != 'nearmiss': continue
        rows = [dict(alias=nm[i]['canonical'], wrong=nm[i]['type'] in ('off', 'wrong_name', 'false_absent'), type=nm[i]['type'], flag=doubt(v, nm[i]['kind']), v=v) for i, v in vs.items() if i in nm]
        o = collections.OrderedDict(); o['rows'] = len(rows); o['unsure_or_missing'] = sum(1 for r in rows if r['flag'] is None)
        F = [r for r in rows if r['flag']]; o['flag_precision'] = [pct([r['wrong'] for r in F]), len(F)]
        o['recall_of_wrong'] = pct([bool(r['flag']) for r in rows if r['wrong']]); o['false_flag_on_true'] = pct([bool(r['flag']) for r in rows if not r['wrong']])
        for ty in ('true_point', 'off', 'wrong_name', 'true_absent', 'false_absent'): o['flag_rate_' + ty] = pct([bool(r['flag']) for r in rows if r['type'] == ty])
        res['nearmiss|' + fam] = o
    fams = sorted(f for f, st in V if st == 'nearmiss')
    for i in range(len(fams)):
        for j in range(i + 1, len(fams)):
            a, b = V[(fams[i], 'nearmiss')], V[(fams[j], 'nearmiss')]
            rows = [dict(wrong=nm[x]['type'] in ('off', 'wrong_name', 'false_absent'), fa=doubt(a.get(x), nm[x]['kind']), fb=doubt(b.get(x), nm[x]['kind'])) for x in nm]
            F = [r for r in rows if r['fa'] and r['fb']]
            res['nearmiss_both|%s+%s' % (fams[i], fams[j])] = dict(removals=len(F), precision=pct([r['wrong'] for r in F]), recall_of_wrong=pct([bool(r['fa'] and r['fb']) for r in rows if r['wrong']]),
                                                                  false_removal_of_true=pct([bool(r['fa'] and r['fb']) for r in rows if not r['wrong']]))
    pf = sorted(f for f, st in V if st == 'pilot')
    if len(pf) >= 2:
        meta = json.load(open(K + '/c2_rows_meta.json')); a, b = V[(pf[0], 'pilot')], V[(pf[1], 'pilot')]
        kind = lambda rid: 'absent' if meta[rid[1:]]['kind'] == 'gt_absent' else 'point'
        ids = [x for x in a if x in b]; da = [doubt(a[x], kind(x)) for x in ids]; db = [doubt(b[x], kind(x)) for x in ids]
        res['pilot'] = dict(rows=len(ids), doubted=[pct(da), pct(db)], both=pct([x and y for x, y in zip(da, db) if x is not None and y is not None]),
                            agreement=pct([x == y for x, y in zip(da, db) if x is not None and y is not None]), unsure=[sum(x is None for x in da), sum(x is None for x in db)])
        th = K + '/c2/REMOVAL_CANDIDATES.jsonl'
        if os.path.exists(th):
            cand = {'r%d' % json.loads(l)['store_index'] for l in open(th)}
            res['pilot']['c2_candidates_still_doubted_by_both'] = pct([doubt(a.get(x), kind(x)) and doubt(b.get(x), kind(x)) for x in cand if x in a and x in b])
    return res
if __name__ == '__main__':
    form = sys.argv[1]; files = sys.argv[2:]
    res = {'a': form_a, 'b': form_b, 'c': form_c}[form](files)
    print(json.dumps(res, indent=0)); os.makedirs(K + '/scores', exist_ok=True); json.dump(res, open(K + '/scores/V1%s.json' % form, 'w'), indent=1)
PYEOF
P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%T; wc -l out/4*.jsonl out/5*.jsonl analysis_only/out/5*.jsonl 2>/dev/null | tail -9; tail -1 v6/chain.log; ls faults
timeout 300 $P -B kit/score_v1.py b out/52_v1b32.jsonl > scores/V1b.txt 2>&1; echo b rc $?; tr -d '\n' < scores/V1b.txt | cut -c1-1800; echo
timeout 300 $P -B kit/score_v1.py c out/54_v1c_nearmiss.jsonl analysis_only/out/53_v1c_pilot.jsonl > scores/V1c.txt 2>&1; echo c rc $?; tr -d '\n' < scores/V1c.txt | cut -c1-3000; echo
