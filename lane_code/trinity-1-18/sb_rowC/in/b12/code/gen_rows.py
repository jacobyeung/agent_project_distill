"""b12_cntapp row generator: counting (single, total), appearance order and first-seen rows from GT instance rasters
at the row's own pins. Usage: gen_rows.py OUT_DIR RASTER_ROOT [RASTER_ROOT ...]
Visibility (gtvis.FLOOR): an instance is visible in pin f when its raster pixel share >= 0.002.
Counting: n >= 2 instances, every instance visible in some pin. Totals: 2-3 such categories (n >= 1, one with n >= 2).
Appearance: 4 categories with clean onsets (no instance share >= ONSET_EPS before the first-seen pin), first-seen pins
pairwise >= 2 apart. First-seen: one category with a clean onset. Category gates: not structural, in the D0/bench vocab
of the dataset, no sibling label sharing its head noun or plural.
Drop rules (DROP_RULES) run after all sampling and balancing and never feed back into them, so a dropped row never
reshuffles another: (a) ARKit capture without an 'ok' pin-alignment entry in either check file, (b) total whose category set
repeats a D0 v5 total, (c) appearance whose category set repeats a D0 v5 appearance row. Sampling inputs stay those of v2:
the scene gate reads ARK_PIN_TS_CHECK.json only and appearance sampling excludes d0_pairs sets only."""
import json, os, sys, glob, hashlib, itertools, collections, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gtvis import FLOOR, DENY, norm, load_raster, ambiguous
import rooms as RM
W = '/scratch/jjyeung/orch_n30/b12_cntapp/work/'
ONSET_EPS = 0.0005
CAP_APP, CAP_TOT, CAP_FS = 40, 8, 6
MAX_SINGLE, MAX_TOTAL = 25, 30
BAN_WORDS = {'frame', 'frames', 'foot', 'feet', 'inch', 'inches', 'yard', 'yards', 'meter', 'meters', 'metre', 'metres', 'square', 'degree',
             'degrees', 'cm', 'mm', 'm', 'ft', 'in', 'km', 'deg'}
FS_FRAME1_SHARE = 0.10
sys.path.insert(0, '/scratch/jjyeung/orch_n30/rows_rebuild3/work/validator'); import trace_grammar as G
assert hashlib.sha256(open(G.__file__, 'rb').read()).hexdigest().startswith('a41ba191')
SING_S = {'canvas', 'atlas', 'lens', 'gas', 'bias', 'news', 'chassis'}
def plural(c):
    w = c.split()[-1]
    return w.endswith('s') and not w.endswith(('ss', 'us', 'is', 'os')) and w not in SING_S
def disjoint(cb):
    ws = [set(c.split()) for c in cb]
    return all(not (a & b) for a, b in itertools.combinations(ws, 2))
DSN = {'d1': 'scannet', 'd2': 'scannetpp', 'd3': 'arkitscenes'}
LIC = {'d1': ['ScanNet Terms of Use'], 'd2': ['ScanNet++ Terms of Use'], 'd3': ['ARKitScenes CC BY-NC-SA 4.0']}
GEN_SHA = hashlib.sha256(open(os.path.abspath(__file__), 'rb').read()).hexdigest()
GTVIS_SHA = hashlib.sha256(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gtvis.py'), 'rb').read()).hexdigest()

def h(s): return int(hashlib.sha256(s.encode()).hexdigest(), 16)
def sha_file(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def region(c): return 'left' if c < 1 / 3 else 'right' if c > 2 / 3 else 'middle'

def vocab():
    dv = json.load(open(W + 'd0_vocab.json')); bv = json.load(open(W + 'bench_vocab.json')); out = {}
    for ds, bn in DSN.items():
        v = set()
        for k, c in dv.items():
            if k.endswith('|' + ds): v |= {norm(x) for x in c}
        for k, c in bv.items():
            if k.endswith('|' + bn): v |= {norm(x) for x in c}
        out[ds] = v - DENY
    return out

def raster_index(roots):
    R = {}
    for r in roots:
        for f in sorted(glob.glob(r + '/**/*.npz', recursive=True)): R.setdefault(os.path.basename(f)[:-4], f)
    return R

def raster_key(c):
    ds, i = c.split('/', 1)
    return i if ds == 'arkitscenes' else c.replace('scannetpp/', 'scannetppv2/').replace('/', '__')

# ---- question and trace templates (deterministic choice by qid hash) ----
Q_SINGLE = ['How many {c}(s) do we have in this room?', 'How many {c}(s) are there in this room?',
            'Count the {c}(s) in this room. How many are there?']
Q_TOTAL = ['Count the {j} in this room together. How many are there in total?', 'What is the total number of {j} in this room?',
           'How many objects are there altogether among the {j} in this room?']
L_LIST = ['list each distinct {c} once, by the frame where it first appears: {l}.', 'locate each distinct {c} at its first appearance: {l}.',
          'find each distinct {c}, using its first-seen frame: {l}.', 'list the distinct {c} instances by first appearance: {l}.']
S_SINGLE = ['So the count is {n}.', 'So the count equals {n}.', 'So there are {n} in all.']
Q_APP = 'What will be the first-time appearance order of the following categories in the video: {l}?'
Q_FS = ['In which frame does {a} {c} first appear?', 'Which frame is the first one that shows {a} {c}?']
L_FS = ['Step 1: {a} {c} is first seen in frame {f} ({r}).', 'Step 1: {a} {c} first appears in frame {f} ({r}).']

def inst_list(insts):
    return '; '.join(f'frame {f} ({r})' for f, r in insts)

def scene_facts(rs, ds, V):
    """per category: instances (id, first-seen pin, region), onset pin and clean-onset flag"""
    by = collections.defaultdict(list)
    for i, l in rs['labels'].items(): by[l].append(i)
    labels = set(by); cats = {}; why = collections.Counter()
    valid = rs.get('valid') or [True] * rs['shape'][0]
    for cat, ids in by.items():
        if cat in DENY: why['structural'] += 1; continue
        if cat not in V[ds]: why['not in vocab'] += 1; continue
        if ambiguous(cat, labels): why['sibling label'] += 1; continue
        if set(cat.split()) & BAN_WORDS or 'frame' in cat or any(ch.isdigit() for ch in cat): why['frame/unit/digit word in label'] += 1; continue
        insts = []
        for i in sorted(ids):
            vis = sorted(f for f, s in rs['share'].get(i, {}).items() if s >= FLOOR)
            insts.append((i, vis[0] if vis else None, region(rs['cent'][i][vis[0]]) if vis else None,
                          round(rs['share'][i][vis[0]], 5) if vis else None))
        seen = [x[1] for x in insts if x[1] is not None]
        onset = min(seen) if seen else None
        clean = onset is not None and all(valid[p - 1] for p in range(1, onset)) and \
            all(rs['share'].get(i, {}).get(p, 0) < ONSET_EPS for i in ids for p in range(1, onset))
        cats[cat] = dict(plural=plural(cat), n=len(ids), insts=insts, allvis=all(x[1] is not None and all(valid[p - 1] for p in range(1, x[1])) for x in insts), onset=onset, clean=clean)
    return cats, why

def base_row(alias, si, qt, qid, q, opts, ans, target, prov):
    ds, sc = alias.split('/', 1)
    stu = dict(question=q, options=opts, fps=si['fps'], timestamps=si.get('timestamps'), total_num_frames=si.get('total_num_frames'),
               frame_indices=si['frame_indices'], frames=si['frames'])
    return dict(answer=str(ans), benchmark_improvement_claim=False, benchmark_trained_diagnostic=True, category=qt, dataset=ds,
                generation_commit='', infrastructure_only=False, license=LIC[ds], pool='b12_cntapp_gt_v1',
                provenance=dict(prov, view_labels='frame_numbers', frame_map_sha256=si.get('frame_map_sha256'), frame_store=si.get('frame_store'),
                                generator_sha256=GEN_SHA, gtvis_sha256=GTVIS_SHA, visibility_floor=FLOOR, onset_eps=ONSET_EPS),
                provisional_diagnostic='ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW', qid=qid, question_type=qt,
                result_status='diagnostic, provisional', scene=sc, score_nomination_allowed=False, validation_commit='',
                student_input=stu, target=target)

def total_trace(qid, parts):
    lines, ns = [], []
    for k, (c, insts) in enumerate(parts):
        lines.append(f'Step {k + 1}: ' + L_LIST[h(qid + c) % 4].format(c=c, l=inst_list(insts))); ns.append(len(insts))
    acc, sums = ns[0], []
    for n in ns[1:]: sums.append(f'{acc} + {n} = {acc + n}'); acc += n
    lines.append(f'Step {len(parts) + 1}: add them: ' + '; '.join(sums) + '.')
    lines.append(f'So there are {acc} in total.')
    return '\n'.join(lines), acc

def gen_scene(alias, canonical, rpath, si, V, d0c, d0a):
    rs = load_raster(rpath)
    if rs['fi'] != list(si['frame_indices']): return None, {'raster pins differ': 1}
    ds = alias[:2]; cats, why = scene_facts(rs, ds, V); rows = collections.defaultdict(list)
    rprov = dict(source='b12_cntapp gt raster', canonical=canonical, raster=os.path.basename(rpath), raster_sha256=sha_file(rpath))
    rnd = random.Random(h(alias))
    cnt = {c: v for c, v in cats.items() if v['allvis'] and not v['plural']}
    why['count: plural label skipped'] += sum(1 for v in cats.values() if v['allvis'] and v['plural'])
    # single counting: new pairs only (D0 counting pairs are rows_a2's retrace)
    for c, v in sorted(cnt.items()):
        if v['n'] < 2: continue
        if c in d0c: why['single: D0 pair'] += 1; continue
        if v['n'] > MAX_SINGLE: why['single: n above cap'] += 1; continue
        qid = 'b12cs_' + hashlib.sha256(f'{alias}|{c}'.encode()).hexdigest()[:24]
        insts = sorted((x[1], x[2]) for x in v['insts'])
        body = 'Step 1: ' + L_LIST[h(qid + 'a') % 4].format(c=c, l=inst_list(insts)) + '\n' + S_SINGLE[h(qid + 'b') % 3].format(n=len(insts))
        rows['count_single'].append(base_row(alias, si, 'object_counting', qid, Q_SINGLE[h(qid) % 3].format(c=c), [], len(insts),
                                             f'<think>\n{body}\n</think>\n\n{len(insts)}',
                                             dict(rprov, count_kind='single', instances=[dict(id=x[0], frame=x[1], region=x[2], share=x[3]) for x in v['insts']])))
    # totals: 2-3 categories, at least one with n >= 2
    tc = sorted(cnt); combos = [cb for k in (2, 3) for cb in itertools.combinations(tc, k)
                                if max(cnt[x]['n'] for x in cb) >= 2 and disjoint(cb) and sum(cnt[x]['n'] for x in cb) <= MAX_TOTAL]
    rnd.shuffle(combos); use = collections.Counter()
    for cb in combos:
        if len(rows['count_total']) >= CAP_TOT: break
        if any(use[x] >= 3 for x in cb): continue
        for x in cb: use[x] += 1
        qid = 'b12ct_' + hashlib.sha256(f'{alias}|{"|".join(cb)}'.encode()).hexdigest()[:24]
        parts = [(x, sorted((i[1], i[2]) for i in cnt[x]['insts'])) for x in cb]
        body, tot = total_trace(qid, parts)
        j = ' and '.join(f'{x}(s)' for x in cb)
        r = base_row(alias, si, 'object_counting', qid, Q_TOTAL[h(qid) % 3].format(j=j), [], tot, f'<think>\n{body}\n</think>\n\n{tot}',
                     dict(rprov, count_kind='total', total_categories=[dict(name=x, ids=[i[0] for i in cnt[x]['insts']], frames=[i[1] for i in cnt[x]['insts']]) for x in cb]))
        r['count_kind'] = 'total'; r['count_arity'] = len(cb); rows['count_total'].append(r)
    # appearance order
    app = {c: v['onset'] for c, v in cats.items() if v['clean']}
    why['appearance: clean-onset categories'] += len(app)
    ac = sorted(app); sets = []
    if len(ac) >= 4:
        allc = list(itertools.combinations(ac, 4))
        if len(allc) > 200000: allc = rnd.sample(allc, 200000)
        sets = [cb for cb in allc if all(b - a >= 2 for a, b in zip(sorted(app[x] for x in cb), sorted(app[x] for x in cb)[1:]))
                and tuple(cb) not in d0a and disjoint(cb)]
    rnd.shuffle(sets); use = collections.Counter(); chosen = []
    for rnds in range(4):  # greedy: spread categories, each used at most 2*(round+1) times
        for cb in sets:
            if len(chosen) >= CAP_APP: break
            if cb in chosen or any(use[x] >= 2 * (rnds + 1) for x in cb): continue
            chosen.append(cb); use.update(cb)
    for cb in chosen:
        qid = 'b12ao_' + hashlib.sha256(f'{alias}|{"|".join(cb)}'.encode()).hexdigest()[:24]
        order = sorted(cb, key=app.get); perms = [list(p) for p in itertools.permutations(cb) if list(p) != order]
        rr = random.Random(h(qid)); dis = rr.sample(perms, 3); pos = h(qid + 'pos') % 4
        opts = dis[:pos] + [order] + dis[pos:]; L = 'ABCD'
        body = ('Step 1: find the first frame showing each object: ' + '; '.join(f'{x} frame {app[x]}' for x in cb) + '.\n'
                'Step 2: order them by first appearance: ' + ', '.join(order) + '.')
        rows['appearance'].append(base_row(alias, si, 'obj_appearance_order', qid, Q_APP.format(l=', '.join(cb)),
                                           [f'{L[k]}. ' + ', '.join(o) for k, o in enumerate(opts)], L[pos], f'<think>\n{body}\n</think>\n\n{L[pos]}',
                                           dict(rprov, first_seen={x: app[x] for x in cb}, gap_min=min(b - a for a, b in zip(sorted(app[x] for x in cb), sorted(app[x] for x in cb)[1:])))))
    # first-seen auxiliary
    fsc = sorted(c for c in app if not cats[c]['plural']); rnd.shuffle(fsc)
    for c in fsc[:CAP_FS]:
        v = cats[c]; f = v['onset']; reg = [x[2] for x in v['insts'] if x[1] == f][0]
        qid = 'b12fs_' + hashlib.sha256(f'{alias}|{c}'.encode()).hexdigest()[:24]
        a = 'the' if v['n'] == 1 else 'a'
        q = Q_FS[h(qid) % 2].format(a=a, c=c); body = L_FS[h(qid + 'l') % 2].format(a=a, c=c, f=f, r=reg)
        r = base_row(alias, si, 'first_seen_frame', qid, q, [], f, f'<think>\n{body}\n</think>\n\n{f}',
                     dict(rprov, first_seen=f, n_instances=v['n'], onset_instance=[x[0] for x in v['insts'] if x[1] == f][0]))
        rows['first_seen'].append(r)
    return rows, why

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; out, roots = args[0], args[1:]
    os.makedirs(out, exist_ok=True)
    am = json.load(open('/scratch/jjyeung/orch_n30/rows_a2/work/alias_map.json')); am.update(json.load(open(W + 'd3_token_map.json')))
    SI = json.load(open(W + 'si_by_alias.json')); EL = json.load(open(W + 'ELIGIBILITY_SCENES.json'))
    if '--ext' in sys.argv:
        ext = json.load(open(W + 'si_ext_by_alias.json')); SI.update({a: v for a, v in ext.items() if a not in SI})
        for j in json.load(open(W + 'streams_ark_jobs.json')): am.setdefault(j['alias'], 'arkitscenes/' + j['id'])
        for j in json.load(open(W + 'streams_scn_jobs.json')): am.setdefault(j['alias'], 'scannet/' + j['id'])
    d0 = json.load(open(W + 'd0_pairs.json')); V = vocab(); R = raster_index(roots)
    D0S = json.load(open(W + 'd0_sets.json'))
    GATE = json.load(open(W + 'ARK_PIN_TS_CHECK.json')); ARKTS = {}
    for f in ('ARK_PIN_TS_CHECK.json', 'ARK_PIN_TS_CHECK_K1.json'):
        for a, v in json.load(open(W + f)).items(): ARKTS[a] = v if ARKTS.get(a, 'ok') == 'ok' else ARKTS[a]
    def drop_rule(r):
        a = r['dataset'] + '/' + r['scene']
        if r['dataset'] == 'd3' and ARKTS.get(a, 'no check') != 'ok': return 'ARKit pin alignment not ok (%s)' % ARKTS.get(a, 'no check')[:40]
        if r.get('count_kind') == 'total' and tuple(sorted(x['name'] for x in r['provenance']['total_categories'])) in {tuple(x) for x in D0S['total'].get(a, [])}:
            return 'total: D0 v5 category set'
        if r['question_type'] == 'obj_appearance_order' and tuple(sorted(r['provenance']['first_seen'])) in {tuple(x) for x in D0S['app'].get(a, [])}:
            return 'appearance: D0 v5 category set'
    st = collections.Counter(); fams = collections.defaultdict(list); per_scene = {}; held = collections.defaultdict(list)
    for alias in sorted(SI):
        c = am.get(alias)
        if not c: st['scene: no canonical'] += 1; continue
        if EL.get(alias, {}).get('excluded'): st['scene: excluded'] += 1; continue
        k = raster_key(c)
        if k not in R: st['scene: no raster'] += 1; continue
        if alias.startswith('d3/') and GATE.get(alias, 'ok') != 'ok': st['scene: ARKit pin timestamps differ from RGB'] += 1; continue
        rows, why = gen_scene(alias, c, R[k], SI[alias], V, set(d0['count'].get(alias, [])), {tuple(x) for x in d0['app'].get(alias, [])})
        for w, n in why.items(): st[w] += n
        if rows is None: st['scene: raster pins differ'] += 1; continue
        rs_ = RM.status(c)
        if rs_ == 'r0': st['scene: R0 reserve room (rows dropped)'] += 1; continue
        if rs_ == 'k1_heldout':
            st['scene: K1 held-out room (rows filtered)'] += 1
            for f, v in rows.items(): held[f].extend(v)
            continue
        st['scene: used'] += 1; per_scene[alias] = {f: len(v) for f, v in rows.items()}
        for f, v in rows.items():
            for r in v:
                e = G.validate_row(r)
                if e: st[f'{f}: dropped by validator {e[0].rule_id}'] += 1
                else: fams[f].append(r)
    # first-seen answer balance: frame-1 rows at most FS_FRAME1_SHARE of the family (deterministic by qid hash)
    one = sorted((r for r in fams['first_seen'] if r['answer'] == '1'), key=lambda r: h(r['qid'] + 'bal'))
    rest = [r for r in fams['first_seen'] if r['answer'] != '1']; keep1 = int(FS_FRAME1_SHARE * len(rest) / (1 - FS_FRAME1_SHARE))
    st['first_seen: frame-1 rows dropped for balance'] = max(0, len(one) - keep1)
    keep = {r['qid'] for r in one[:keep1]}
    fams['first_seen'] = [r for r in fams['first_seen'] if r['answer'] != '1' or r['qid'] in keep]
    dropped = []
    for pool in (fams, held):
        for f in list(pool):
            kept = []
            for r in pool[f]:
                w = drop_rule(r)
                if w: dropped.append(dict(qid=r['qid'], family=f, rule=w, heldout=pool is held)); st[f'drop rule: {f}: {w}'] += 1
                else: kept.append(r)
            pool[f] = kept
    with open(os.path.join(out, 'DROPPED.jsonl'), 'w') as fh:
        for d in dropped: fh.write(json.dumps(d, sort_keys=True) + '\n')
    man = dict(generator_sha256=GEN_SHA, gtvis_sha256=GTVIS_SHA, validator_sha256=hashlib.sha256(open(G.__file__, 'rb').read()).hexdigest(), raster_roots=roots, n_rasters_indexed=len(R), stats=dict(st), families={})
    for f, v in sorted(fams.items()):
        p = os.path.join(out, f + '.jsonl')
        with open(p, 'w') as fh:
            for r in v: fh.write(json.dumps(r, sort_keys=True) + '\n')
        man['families'][f] = dict(path=p, rows=len(v), sha256=sha_file(p), scenes=len({r['dataset'] + '/' + r['scene'] for r in v}),
                                  by_dataset=dict(collections.Counter(r['dataset'] for r in v)))
    os.makedirs(os.path.join(out, 'filtered_k1_heldout'), exist_ok=True); man['filtered_k1_heldout'] = {}
    for f, v in sorted(held.items()):
        p = os.path.join(out, 'filtered_k1_heldout', f + '.jsonl')
        with open(p, 'w') as fh:
            for r in v: fh.write(json.dumps(r, sort_keys=True) + '\n')
        man['filtered_k1_heldout'][f] = dict(path=p, rows=len(v), sha256=sha_file(p), scenes=sorted({r['dataset'] + '/' + r['scene'] for r in v}))
    man['room_authorities'] = RM.AUTH
    k1n = lambda c: c.replace('scannetppv2/', 'scannetpp/')
    man['k1_captures_used'] = sorted({k1n(r['provenance']['canonical']) for v in fams.values() for r in v if k1n(r['provenance']['canonical']) in RM.K1_CAPTURES})
    man['k1_captures_used_split'] = dict(collections.Counter(RM.K1_CAPTURES[c] for c in man['k1_captures_used']))
    json.dump(per_scene, open(os.path.join(out, 'PER_SCENE.json'), 'w'))
    json.dump(man, open(os.path.join(out, 'GEN_MANIFEST.json'), 'w'), indent=1)
    print(json.dumps(man, indent=1))

if __name__ == '__main__':
    main()
