"""Labelling pilot, part 2: score the row audit. Each store-v7 row on the 24 calibration captures is checked against the labeller's answers:
  (a) a cited frame that does not show the object: the trace says the object is seen (or first seen) in frame k, the labeller says it is not visible there;
  (b) a named object the labeller finds in none of the 32 frames (question not answerable from the sampled frames);
  (c) a first-seen citation the labeller places two or more frames earlier or later.
The raster's pixel share at the cited frame (work/pilot_key/audit_raster.json) splits (a) by how much of the frame the object covers.
usage: /usr/bin/python3 score_audit.py TAG   -> prints per-family tables, writes results/ROW_AUDIT_<TAG>.json"""
import sys, json, glob, collections, re
P = '/scratch/jjyeung/orch_n30/swarm_an/work/pilot/'; KD = '/scratch/jjyeung/orch_n30/swarm_an/work/pilot_key/'
tag = sys.argv[1]
key = json.load(open(KD + 'key_audit.json')); rows = json.load(open(KD + 'audit_rows.json')); rast = json.load(open(KD + 'audit_raster.json'))
def num(x):
    m = re.search(r'-?\d+', str(x)); return int(m.group(0)) if m else None
vis = {}; first = {}; clips = 0; sec = 0.0; nans = 0; noans = []
for f in sorted(glob.glob(P + 'results/' + tag + '/*.json')):
    d = json.load(open(f)); ans = d.get('answers')
    if not isinstance(ans, dict) or 'error' in ans: noans.append(d['clip']); continue
    clips += 1; sec += d.get('seconds') or 0
    for kq, k in key.items():
        name, qid = kq.split('/')
        if name != d['clip'] or ans.get(qid) is None: continue
        nans += 1
        if k['kind'] == 'visible': vis[(k['alias'], k['obj'], k['frame'])] = str(ans[qid]).strip().lower().startswith('y')
        else: first[(k['alias'], k['obj'])] = num(ans[qid])
print('== %s: %d dispatches answered (%d without answers: %s), %d labels, %.0f wall seconds = %.0f s and %.1f dispatches per 1,000 labels' % (
    tag, clips, len(noans), ','.join(noans)[:80], nans, sec, 1000.0 * sec / max(1, nans), 1000.0 * clips / max(1, nans)))
def share(alias, o, k):
    x = (rast.get(alias) or {}).get('objs', {}).get(o)
    return None if not x else x['share'][k - 1]
def rfirst(alias, o):
    x = (rast.get(alias) or {}).get('objs', {}).get(o)
    return None if not x else x['first']
fam = collections.defaultdict(lambda: collections.Counter()); out = []; pair_seen = {}
for i, r in rows.items():
    a = r['alias']; f = r['category']; F = fam[f]; F['rows'] += 1
    pv = [(o, k, vis.get((a, o, k))) for o, k in r['pairs']]; pv = [x for x in pv if x[2] is not None]
    ob = [(o, first.get((a, o))) for o in r['objs']]; ob = [x for x in ob if x[1] is not None]
    if not ob and not pv: F['rows without labels'] += 1; continue
    F['rows checked'] += 1
    bad_a = [(o, k) for o, k, v in pv if not v]; bad_b = [o for o, x in ob if x == 0]
    if pv: F['rows citing a frame'] += 1; F['cited pairs'] += len(pv)
    if bad_a: F['a: rows with a cited frame not showing the object'] += 1
    F['a: cited pairs not shown'] += len(bad_a)
    if bad_b: F['b: rows with an object never visible'] += 1
    F['objects'] += len(ob); F['b: objects never visible'] += len(bad_b)
    late = early = 0
    if r['cites_first']:
        mins = {}
        for o, k in r['pairs']: mins[o] = min(k, mins.get(o, 99))
        for o, k in sorted(mins.items()):
            x = first.get((a, o))
            if x is None or x == 0: continue
            F['first-seen citations'] += 1
            if x <= k - 2: early += 1; F['c: labeller sees it 2+ frames earlier'] += 1
            elif x >= k + 2: late += 1; F['c: labeller sees it 2+ frames later'] += 1
            elif x == k: F['c: same frame'] += 1
            else: F['c: within one frame'] += 1
    for o, k, v in pv:
        s = share(a, o, k)
        b = 'no raster label' if s is None else 'raster 0 px' if s == 0 else 'under 0.2%' if s < 0.002 else '0.2-1%' if s < 0.01 else '1-5%' if s < 0.05 else '5%+'
        F['share ' + b] += 1
        if not v: F['share ' + b + ' not shown'] += 1
        pair_seen[(a, o, k)] = (v, s)
    out.append(dict(i=int(i), alias=a, family=f, pool=r['pool'], cited_not_shown=bad_a, never_visible=bad_b, early=early, late=late, q=r['q']))
order = ['obj_appearance_order', 'object_counting', 'object_rel_distance', 'object_size_estimation', 'object_rel_direction_easy', 'object_rel_direction_medium', 'object_rel_direction_hard', 'route_planning']
def pc(a, b): return '%5.1f%% (%d/%d)' % (100.0 * a / b, a, b) if b else '      -'
print('\n(a) trace cites a frame that does not show the object, per ROW and per cited PAIR')
for f in order:
    F = fam[f]; print('  %-28s rows %4d | citing %4d | rows flagged %s | pairs flagged %s' % (f, F['rows checked'], F['rows citing a frame'],
        pc(F['a: rows with a cited frame not showing the object'], F['rows citing a frame']), pc(F['a: cited pairs not shown'], F['cited pairs'])))
print('\n(b) question names an object the labeller finds in no frame, per ROW and per OBJECT')
for f in order:
    F = fam[f]; print('  %-28s rows %4d | rows flagged %s | objects flagged %s' % (f, F['rows checked'], pc(F['b: rows with an object never visible'], F['rows checked']), pc(F['b: objects never visible'], F['objects'])))
print('\n(c) first-seen citations against the labeller\'s first-seen frame')
for f in order:
    F = fam[f]; n = F['first-seen citations']
    if n: print('  %-28s citations %4d | same %s | within one %s | labeller 2+ earlier %s | 2+ later %s' % (f, n, pc(F['c: same frame'], n), pc(F['c: within one frame'], n),
        pc(F['c: labeller sees it 2+ frames earlier'], n), pc(F['c: labeller sees it 2+ frames later'], n)))
print('\nDistinct cited (capture, object, frame) pairs by raster pixel share at the cited frame: not shown / all')
T = collections.Counter(); N = collections.Counter()
for (a, o, k), (v, s) in pair_seen.items():
    b = 'no raster label' if s is None else 'raster 0 px' if s == 0 else 'under 0.2%' if s < 0.002 else '0.2-1%' if s < 0.01 else '1-5%' if s < 0.05 else '5%+'
    T[b] += 1; N[b] += (not v)
for b in ['raster 0 px', 'under 0.2%', '0.2-1%', '1-5%', '5%+', 'no raster label']: print('  %-16s %s' % (b, pc(N[b], T[b])))
print('  %-16s %s' % ('all', pc(sum(N.values()), sum(T.values()))))
ob = collections.Counter(); 
for (a, o), x in first.items():
    rf = rfirst(a, o); ob['objects asked'] += 1
    if x == 0: ob['labeller: never visible'] += 1; ob['  of those, raster has the label and a visible frame' if rf else '  of those, raster has no label or no visible frame'] += 1
print('\nDistinct (capture, object):', dict(ob))
json.dump(dict(tag=tag, families=dict((f, dict(v)) for f, v in fam.items()), rows=out, pairs=[dict(alias=a, obj=o, frame=k, shown=v, share=s) for (a, o, k), (v, s) in pair_seen.items()],
               first=[dict(alias=a, obj=o, labeller=x, raster=rfirst(a, o)) for (a, o), x in first.items()]), open(P + 'results/ROW_AUDIT_%s.json' % tag, 'w'), indent=0)
