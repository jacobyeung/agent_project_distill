"""Independent checks of b12_cntapp rows (does not import gtvis or gen_rows). Usage: check_rows.py ROWS_DIR RASTER_ROOT [...]
1 validator a41ba191 on every row; 2 visibility: every cited frame shows the cited instance (raster share >= 0.002), recomputed
from the npz; 3 answers recomputed (count = instances of the label, all visible; order = GT first-seen order, gaps >= 2, clean
onsets; first-seen = min visible pin); 4 eligibility (scene not dev-S1, bench v2, withheld-80); 5 repeat limits; 6 answer
histograms and no-information constants."""
import sys, os, json, glob, re, hashlib, collections, numpy as np
sys.path.insert(0, '/scratch/jjyeung/orch_n30/rows_rebuild3/work/validator'); import trace_grammar as g
assert hashlib.sha256(open(g.__file__, 'rb').read()).hexdigest().startswith('a41ba191')
FLOOR, EPS = 0.002, 0.0005
D, roots = sys.argv[1], sys.argv[2:]
R = {}
for r in roots:
    for f in sorted(glob.glob(r + '/**/*.npz', recursive=True)): R.setdefault(os.path.basename(f), f)
EL = json.load(open('/scratch/jjyeung/orch_n30/b12_cntapp/work/ELIGIBILITY_SCENES.json'))
cache = {}
def share(name):
    if name not in cache:
        z = np.load(R[name]); inst = z['inst']; n = inst.shape[1] * inst.shape[2]; S = collections.defaultdict(dict)
        for f in range(inst.shape[0]):
            u, c = np.unique(inst[f], return_counts=True)
            for i, cc in zip(u, c):
                if i >= 0: S[int(i)][f + 1] = cc / n
        lab = collections.defaultdict(list)
        for i, l in zip(z['ids'], z['labels']): lab[re.sub(r'\s+', ' ', str(l).strip().lower().replace('_', ' '))].append(int(i))
        if len(cache) > 64: cache.clear()
        cache[name] = (S, lab, [int(x) for x in z['frame_indices']], [bool(v) and bool(m) for v, m in zip(z['valid'], (z['depth'] > 0).any(axis=(1, 2)))])
    return cache[name]
def fs_of(S, i): v = [f for f, s in S.get(i, {}).items() if s >= FLOOR]; return min(v) if v else None
def mra(p, t): return np.mean([abs(p - t) / t < 1 - th for th in np.arange(0.5, 1.0, 0.05)])
res = {}; bad = collections.defaultdict(list)
for fam in ('count_single', 'count_total', 'appearance', 'first_seen'):
    p = os.path.join(D, fam + '.jsonl')
    if not os.path.exists(p): continue
    rows = [json.loads(l) for l in open(p)]; c = collections.Counter(); hist = collections.Counter(); vrules = collections.Counter()
    qkeys = collections.Counter(); per_scene = collections.Counter(); cat_use = collections.Counter()
    for r in rows:
        alias = r['dataset'] + '/' + r['scene']; pv = r['provenance']; S, lab, fi, valid = share(pv['raster'])
        def fail(why): c['FAIL ' + why] += 1; bad[fam].append((r['qid'], why))
        for e in g.validate_row(r): vrules[e.rule_id] += 1
        if fi != r['student_input']['frame_indices']: fail('pins differ')
        if EL.get(alias, {}).get('excluded') or alias not in EL: fail('scene not eligible')
        if hashlib.sha256(open(R[pv['raster']], 'rb').read()).hexdigest() != pv['raster_sha256']: fail('raster sha')
        q = r['student_input']['question']; qkeys[(alias, q)] += 1; per_scene[alias] += 1; hist[r['answer']] += 1
        if fam == 'count_single' or fam == 'count_total':
            cats = [(x['name'], x['ids'], x['frames']) for x in pv['total_categories']] if fam == 'count_total' else \
                [(re.search(r'(?:How many|Count the) (.+?)\(s\)', q).group(1), [x['id'] for x in pv['instances']], [x['frame'] for x in pv['instances']])]
            tot = 0
            for name, ids, frames in cats:
                if sorted(ids) != sorted(lab.get(name, [])): fail('cited ids != GT instances of label')
                for i, f in zip(ids, frames):
                    if S.get(i, {}).get(f, 0) < FLOOR: fail('cited frame does not show instance')
                    if fs_of(S, i) != f: fail('cited frame is not first-seen')
                    elif not all(valid[:f - 1]): fail('a pin before the cited frame has no raster')
                if f'{name}(s)' not in q: fail('label not in question')
                tline = [l for l in r['target'].split('\n') if f' {name} ' in l or f' {name},' in l]
                if not tline or len(re.findall(r'frame \d+', tline[0])) != len(ids): fail('trace list length != instances')
                tot += len(ids); cat_use[(alias, name)] += 1
            if str(tot) != r['answer']: fail('answer != GT count')
        elif fam == 'appearance':
            cats = list(pv['first_seen']); fsd = {}
            for x in cats:
                ids = lab.get(x, []); f = min([fs_of(S, i) for i in ids if fs_of(S, i)] or [None])
                fsd[x] = f
                if f is None or f != pv['first_seen'][x]: fail('first-seen recompute differs')
                elif any(S.get(i, {}).get(p, 0) >= EPS for i in ids for p in range(1, f)) or not all(valid[:f - 1]): fail('onset not clean')
                cat_use[(alias, x)] += 1
            fr = sorted(fsd.values())
            if None in fr or any(b - a < 2 for a, b in zip(fr, fr[1:])): fail('gap < 2')
            else:
                order = ', '.join(sorted(cats, key=fsd.get)); opt = [o for o in r['student_input']['options'] if o[3:] == order]
                if len(opt) != 1 or opt[0][0] != r['answer']: fail('answer letter != GT order')
                if len({o[3:] for o in r['student_input']['options']}) != 4: fail('options not distinct')
        elif fam == 'first_seen':
            name = re.search(r'(?:does|shows) (?:the|a) (.+?)(?: first appear\?|\?)$', q).group(1); ids = lab.get(name, [])
            f = min([fs_of(S, i) for i in ids if fs_of(S, i)] or [None])
            if f is None or str(f) != r['answer']: fail('first-seen recompute differs')
            elif any(S.get(i, {}).get(p, 0) >= EPS for i in ids for p in range(1, f)): fail('onset not clean')
            cat_use[(alias, name)] += 1
        c['rows'] += 1
    # no-information constants
    if fam.startswith('count'):
        ans = [int(r['answer']) for r in rows]
        best = max(((k, np.mean([mra(k, t) for t in ans])) for k in range(1, 31)), key=lambda x: x[1]) if ans else None
        noinfo = dict(best_constant=best[0], mra=round(float(best[1]), 4), exact=round(hist[str(best[0])] / len(rows), 4)) if ans else None
    else:
        k, v = hist.most_common(1)[0] if hist else (None, 0); noinfo = dict(best_constant=k, exact=round(v / max(1, len(rows)), 4))
    res[fam] = dict(rows=len(rows), checks=dict(c), validator_failures=dict(vrules), duplicate_questions=sum(v - 1 for v in qkeys.values()),
                    max_rows_per_scene=max(per_scene.values() or [0]), max_uses_per_scene_category=max(cat_use.values() or [0]),
                    answer_hist=dict(sorted(hist.items(), key=lambda x: (len(x[0]), x[0]))), no_information=noinfo)
ok = all(not v['validator_failures'] and not any(k.startswith('FAIL') for k in v['checks']) and v['duplicate_questions'] == 0 for v in res.values())
out = dict(verdict='PASS' if ok else 'FAIL', validator_sha256=hashlib.sha256(open(g.__file__, 'rb').read()).hexdigest(), families=res,
           bad_examples={k: v[:20] for k, v in bad.items()},
           files={f: hashlib.sha256(open(os.path.join(D, f + '.jsonl'), 'rb').read()).hexdigest() for f in res})
json.dump(out, open(os.path.join(D, 'CHECK.json'), 'w'), indent=1); print(json.dumps(out, indent=1))
