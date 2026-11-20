K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1; P=/scratch/jjyeung/envs/p1cpu/bin/python; mkdir -p $K/v6b
cat > $K/kit/v6b_jobs.py <<'PYEOF'
"""nvkey3 V6 in the measured boolean form (C1's presence-and-point PROMPT, verbatim from nvkey1 kit/c1_jobs.py), on K1 TRAINING captures at the 32 anchors.
Per capture and per family (Argon high, Astra high) three call kinds, each at most 12 kinds x 32 frames (the size C1 measured):
  A  presence on the named kinds: at most 8 ground-truth classes by sha order (O5) plus check nouns from the frozen list (O6) up to 12 kinds;
  N  naming: up to 25 other distinct objects (singular count-noun name, two aliases, look-alike, one_object / part_of_larger / group; O10), no frames,
     points, sizes or counts;
  I  presence on the inventory: the union of both families' names (chained once every family's N reply is in or has given up), 8 names plus 4 check
     nouns per call.
Labels (downstream): a presence fact enters only where both families agree; points enter only where the raster share is 5% or more (ORCH 0516Z);
inventory kinds carry the tag of LABEL_NOTE['I'] until a mask certifies their size. Counts and first-seen frames are never asked.
usage: v6b_jobs.py build A_QUEUE.jsonl N_QUEUE.jsonl SELECTION      (SELECTION = first30 | rest | file.json of canonicals)
       v6b_jobs.py chain N_OUT.jsonl N_JOB I_QUEUE.jsonl              (N_JOB names K/faults/<N_JOB>.gaveup.jsonl)"""
import json, os, sys, random, hashlib, collections, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import excl, v6_jobs as V
from score_v1 import parse
K = V.K; FR = V.FR; V6 = V.V6; FORM = 'v6-bool-v1'
FAMILIES = [('gcp/google/gemini-4-argon', 'high'), ('openai/openai/gpt-6.2-astra', 'high')]
FAM = {'gemini-4-argon': 'argon', 'gpt-6.2-astra': 'astra'}
PROMPT = ('These are {n} frames sampled in time order from one video of an indoor room. Each image follows its label "Frame k" (k = 1 to {n}).\n'
          'Object kinds: {kinds}.\n'
          'For every frame and every object kind, decide whether at least one object of that kind is visible in that frame, fully or partly '
          '(partly visible or partly occluded objects count; reflections and pictures of objects do not). '
          'If it is visible, give one point on a visible part of it (if several are visible, pick the most visible one) as [x, y] in 0-1000 coordinates '
          'of that frame: x = 0 at the left edge and 1000 at the right edge, y = 0 at the top edge and 1000 at the bottom edge. If it is not visible, give null.\n'
          'Reply with one JSON object and nothing else, with one entry for every frame from 1 to {n} and every object kind: '
          '{{"1": {{"{k0}": [x, y] or null, ...}}, "2": {{...}}, ..., "{n}": {{...}}}}')
NAMING = (V.HEAD + 'Named kinds: {named}.\n'
          'List up to 25 other distinct physical objects visible in these frames (furniture, appliances, fixtures, and objects at least the size of a book) '
          'that are not of the named kinds. An object seen in several frames is one entry; two objects of the same kind are two entries only when a color or '
          'material word tells them apart. For each give "name" (a singular count noun, with a color or material word only when needed to tell two objects '
          'apart), "aliases" (two other names for it), "look_alike" (a kind of object it could be mistaken for), "one_object" (true if it is one physical '
          'object), "part_of_larger" (true if it is part of a larger object) and "group" (true if it is several objects named as one). Do not give frames, '
          'points, sizes or counts.\n'
          'Reply with one JSON object and nothing else: {{"inventory": [{{"name": "...", "aliases": ["...", "..."], "look_alike": "...", "one_object": true, '
          '"part_of_larger": false, "group": false}}, ...]}}')
LABEL_NOTE = {'A': 'named ground-truth classes and frozen check nouns; presence from two families; points are labels only where the raster share is 5% or more',
              'N': 'uncertified namer; candidates only (names feed the I calls)',
              'I': 'open vocabulary; size uncertified; presence from two families; points are not labels'}
MAXK = 12; NINV = 8; NDEC = 4; UNION_CAP = 24
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
def nname(s):
    s = re.sub(r'\s+', ' ', str(s).lower().replace('_', ' ')).strip(); return re.sub(r'^(a|an|the) ', '', s)
def lists_for(cn, caps, idx, cv):
    c, pool, labels, big = V.capture_truth(cn, caps, idx)
    named = sorted(pool, key=lambda l: sha(cn + ' ' + l))[:8]
    sib = set().union(*[V.siblings(l) for l in labels]) if labels else set()
    rng = random.Random('check ' + cn); dsv = cv['datasets'].get(cn.split('/')[0], [])
    absent_ann = [x for x in dsv if x not in labels and x not in sib and V.head(x) not in sib]; rng.shuffle(absent_ann)
    omitted = [l for l in big if l not in named and not (V.siblings(l) & set(named))]; rng.shuffle(omitted)
    openv = [x for x in cv['open'] if x not in dsv and x not in sib and V.head(x) not in sib and x not in V.STRUCT]; rng.shuffle(openv)
    check = absent_ann[:5] + omitted[:3]; check += [x for x in openv if x not in check][:15 - len(check)]; rng.shuffle(check)
    ctype = {x: ('absent_annotated' if x in absent_ann[:5] else ('present_omitted' if x in omitted[:3] else 'open')) for x in check}
    dense = c['dense_frames']; slots = [int(s) for s in c['anchor_slots']]; frames = []
    for k, s in enumerate(slots):
        fs = os.path.basename(dense[s]['path']).split('.')[0]; p = '%s/%s/%s.png' % (FR, fs[:2], fs); assert os.path.isfile(p), p
        frames.append({'sha256': fs, 'source_index': int(dense[s]['index'])})
    return named, check, ctype, frames
def content_for(text, frames):
    content = [{'text': text}]
    for k, fr in enumerate(frames): content += [{'text': 'Frame %d' % (k + 1)}, {'image': '%s/%s/%s.png' % (FR, fr['sha256'][:2], fr['sha256']), 'max_side': 640}]
    return content
def pins():
    return {'r3_sha256': sha(open(V6 + '/R3_SIBLINGS.json').read()), 'check_vocab_sha256': sha(open(V6 + '/CHECK_VOCAB.json').read())}
def task(kind, cn, model, effort, text, frames, meta):
    mtag = model.split('/')[-1]; extra = json.loads(os.environ.get('C1_EXTRA', '{}'))
    m = dict({'tag': 'train', 'scenes': [cn], 'form': FORM, 'call': kind, 'family': FAM[mtag], 'canonical': cn, 'frames': frames, 'label_note': LABEL_NOTE[kind[0]]}, **meta)
    return {'id': 'v6b%s_%s_%s' % (kind, sha(cn)[:12], mtag), 'model': model, 'effort': effort, 'max_tokens': 32768, 'extra': extra, 'content': content_for(text, frames), 'meta': m}
def selection(sel, idx):
    c1 = {v['canonical'] for v in json.load(open(K + '/c1/C1_MANIFEST.json')).values()}
    clear = sorted(cn for cn in idx if cn not in c1 and not excl.reasons(cn))
    first = json.load(open(V6 + '/FIRST30.json'))['captures']
    if sel == 'first30': return [cn for cn in first if cn in clear], clear
    if sel == 'rest': return sorted((cn for cn in clear if cn not in set(first)), key=lambda x: sha('v6b ' + x)), clear
    return json.load(open(sel)), clear
def build(qa, qn, sel):
    man = json.load(open(K + '/k1r/geo_k1/stage/K1_MANIFEST.arkit_timing.json')); caps = {c['canonical']: c for c in man['captures']}
    idx = json.load(open(K + '/k1r/k1r_index.json')); cv = json.load(open(V6 + '/CHECK_VOCAB.json')); chosen, clear = selection(sel, idx); P = pins(); na = nn = 0
    excl.assert_train(chosen)
    import c1_jobs; assert c1_jobs.PROMPT == PROMPT, 'PROMPT differs from c1_jobs.PROMPT'
    with open(qa, 'a') as fa, open(qn, 'a') as fn:
        for cn in chosen:
            named, check, ctype, frames = lists_for(cn, caps, idx, cv)
            ca = check[:max(NDEC, MAXK - len(named))]; kinds = named + ca; random.Random('v6b order A ' + cn).shuffle(kinds)
            roles = dict([(k, 'named') for k in named] + [(k, 'check:' + ctype[k]) for k in ca])
            for model, effort in FAMILIES:
                fa.write(json.dumps(task('A', cn, model, effort, PROMPT.format(n=32, kinds=json.dumps(kinds), k0=kinds[0]), frames,
                                         dict(P, kinds=kinds, roles=roles, named=named, check=check, check_type=ctype, check_used=ca, prompt_sha256=sha(PROMPT)))) + '\n'); na += 1
                fn.write(json.dumps(task('N', cn, model, effort, NAMING.format(named=json.dumps(named)), frames,
                                         dict(P, named=named, check=check, check_type=ctype, check_used=ca, prompt_sha256=sha(NAMING)))) + '\n'); nn += 1
    print('v6b build', sel, 'captures', len(chosen), 'A tasks', na, 'N tasks', nn, 'clear pool', len(clear))
def union(cn, named, replies):
    """replies: {family: parsed N reply or None}. Returns the inventory kinds (at most UNION_CAP) with who named them and their fields."""
    sib = set().union(*[V.siblings(l) for l in named]) if named else set(); per = collections.OrderedDict(); info = {}
    for fam, d in replies.items():
        items = [x for x in ((d or {}).get('inventory') or []) if isinstance(x, dict) and x.get('name')] if isinstance(d, dict) else []
        names = []
        for it in items:
            nm = nname(it['name'])
            if not nm or it.get('part_of_larger') is True or it.get('group') is True: continue
            if nm in V.STRUCT or V.head(nm) in V.STRUCT or nm in sib or V.head(nm) in sib or nm in named: continue
            if nm not in names: names.append(nm)
            e = info.setdefault(nm, {'named_by': [], 'aliases': {}, 'look_alike': {}, 'one_object': {}})
            if fam not in e['named_by']: e['named_by'].append(fam)
            e['aliases'][fam] = [str(a) for a in (it.get('aliases') or [])][:2]; e['look_alike'][fam] = str(it.get('look_alike') or ''); e['one_object'][fam] = it.get('one_object')
        per[fam] = names
    both = [n for n in info if len(info[n]['named_by']) == len(replies) > 1]
    out = [n for n in sorted(both, key=lambda n: min(per[f].index(n) for f in per))]
    lists = [l for l in per.values()]; i = 0
    while len(out) < UNION_CAP and any(i < len(l) for l in lists):
        for l in lists:
            if i < len(l) and l[i] not in out and len(out) < UNION_CAP: out.append(l[i])
        i += 1
    return out, {n: info[n] for n in out}
def chain(nout, njob, iq):
    """Appends I tasks to I_QUEUE for every capture whose N replies are in from every family (a family that gave up counts as an empty list);
    captures handled are listed in I_QUEUE.done (one canonical per line), including those whose union is empty."""
    dfile = iq + '.done'; done = set(open(dfile).read().split()) if os.path.exists(dfile) else set()
    res = collections.defaultdict(dict); metas = {}
    if os.path.exists(nout):
        for l in open(nout):
            r = json.loads(l); m = r['meta']; res[m['canonical']][m['family']] = parse(r['text']); metas[m['canonical']] = m
    gf = os.path.join(K, 'faults', njob + '.gaveup.jsonl')
    if os.path.exists(gf):
        for l in open(gf):
            parts = json.loads(l)['id'].split('_'); fam = FAM.get(parts[-1])
            for cn, d in list(res.items()):
                if sha(cn)[:12] == parts[1] and fam: d.setdefault(fam, None)
    old = open(iq).read() if os.path.exists(iq) else ''; tmp = os.path.join(os.path.dirname(iq), '.' + os.path.basename(iq) + '.tmp'); n = 0; new_done = []
    with open(tmp, 'w') as f:
        f.write(old)
        for cn, reps in sorted(res.items()):
            if cn in done or len(reps) < len(FAMILIES): continue
            m = metas[cn]; inv, info = union(cn, m['named'], reps); new_done.append(cn)
            dec = [x for x in m['check'] if x not in m['check_used'] and x not in inv] + [x for x in m['check_used'] if x not in inv]
            for j in range(0, len(inv), NINV):
                part = inv[j:j + NINV]; ds = [dec[(j // NINV * NDEC + q) % len(dec)] for q in range(min(NDEC, len(dec)))] if dec else []
                ds = list(dict.fromkeys(ds)); kinds = part + [x for x in ds if x not in part]; random.Random('v6b order I%d %s' % (j // NINV, cn)).shuffle(kinds)
                roles = dict([(k, 'inventory') for k in part] + [(k, 'check:' + m['check_type'][k]) for k in ds])
                for model, effort in FAMILIES:
                    meta = {k: m[k] for k in ('named', 'check', 'check_type', 'r3_sha256', 'check_vocab_sha256')}
                    meta.update(kinds=kinds, roles=roles, inventory={k: info[k] for k in part}, union_size=len(inv), n_replies={fm: (d is not None) for fm, d in reps.items()}, prompt_sha256=sha(PROMPT))
                    f.write(json.dumps(task('I%d' % (j // NINV), cn, model, effort, PROMPT.format(n=32, kinds=json.dumps(kinds), k0=kinds[0]), m['frames'], meta)) + '\n'); n += 1
    if n: os.replace(tmp, iq)
    if new_done: open(dfile, 'a').write(''.join(c + '\n' for c in new_done))
    return n
if __name__ == '__main__':
    a = sys.argv[1]
    if a == 'build': build(sys.argv[2], sys.argv[3], sys.argv[4])
    elif a == 'chain': print('chained', chain(sys.argv[2], sys.argv[3], sys.argv[4]))
PYEOF
cat > $K/kit/score_v6b.py <<'PYEOF'
"""nvkey3 scoring of V6 in the boolean form (v6b_jobs.py) against K1 raster truth at the 32 anchors.
usage: score_v6b.py A_OUT.jsonl I_OUT.jsonl [N_OUT.jsonl] -> K/scores/$V6B_TAG.json (default V6B_first30)
Truth per (kind, anchor): share of the frame covered by ground-truth instances of that label; presence is scored at 1% or more and at 0 px
(0-1% is kept and flagged, never a negative); frames without depth are skipped. Points: inside the label mask, by band (5% or more, 1-5%).
Two families: agreement on presence, agreed facts' accuracy, both-wrong rates, agreed points (within 5% of the diagonal) at their midpoint.
Check nouns by type (absent_annotated: ground truth shows the annotated class absent; present_omitted; open). Inventory (I calls): ground-truth
instances at 1% or more outside the named list, located when an agreed point pair's midpoint falls on the instance, named when the kind or an alias
matches its label; agreed inventory facts by where their midpoint falls (matching instance, other instance, unannotated pixels)."""
import json, os, sys, math, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score_v1 import names_match, parse, boot, pct, norm
K = os.environ.get('NVK', '/scratch/jjyeung/orch_n30/nvkey1/work')
STRUCT = {'wall', 'floor', 'ceiling', 'object', 'objects', 'otherfurniture', 'otherprop', 'otherstructure', 'unknown', 'misc', 'structure', 'doorframe', 'beam', 'pipe', 'column'}
ARKIT17 = {'cabinet', 'refrigerator', 'shelf', 'stove', 'bed', 'sink', 'washer', 'toilet', 'bathtub', 'oven', 'dishwasher', 'fireplace', 'stool', 'chair', 'table', 'tv', 'sofa'}
idx = json.load(open(K + '/k1r/k1r_index.json')); _R = {}
def raster(cn):
    if cn not in _R:
        z = np.load(K + '/k1r/' + idx[cn]['rel'], allow_pickle=True); inst = z['inst']; n, H, W = inst.shape
        _R[cn] = dict(inst=inst, ids=[int(x) for x in z['ids']], labels=[norm(x) for x in z['labels']], H=H, W=W,
                      valid=[k for k in range(32) if float(z['depth'][k].max()) > 0])
    return _R[cn]
def nk(s): return ' '.join(str(s).lower().replace('_', ' ').split())
def table(d, kinds):
    """Reply -> {kind: {k: point | True | False}} for anchors k = 0..31 (missing entries are absent from the dict)."""
    out = {x: {} for x in kinds}; key = {nk(x): x for x in kinds}
    if not isinstance(d, dict): return None
    def val(v):
        if v is None or v is False: return False
        if isinstance(v, (list, tuple)) and len(v) == 2:
            try: return (float(v[0]), float(v[1]))
            except Exception: return True
        if isinstance(v, dict) and 'x' in v and 'y' in v:
            try: return (float(v['x']), float(v['y']))
            except Exception: return True
        return True if v is True else None
    fk = [x for x in d if str(x).strip().isdigit()]
    if fk:
        for f in fk:
            k = int(str(f).strip()) - 1; row = d[f]
            if not (0 <= k < 32 and isinstance(row, dict)): continue
            for kn, v in row.items():
                x = key.get(nk(kn)); w = val(v)
                if x is not None and w is not None: out[x][k] = w
    else:
        for kn, row in d.items():
            x = key.get(nk(kn))
            if x is None: continue
            items = row.items() if isinstance(row, dict) else (enumerate(row, 1) if isinstance(row, list) else [])
            for f, v in items:
                try: k = int(f) - 1
                except Exception: continue
                w = val(v)
                if 0 <= k < 32 and w is not None: out[x][k] = w
    return out
def px(R, p): return min(R['W'] - 1, max(0, int(p[0] / 1000.0 * R['W']))), min(R['H'] - 1, max(0, int(p[1] / 1000.0 * R['H'])))
def inmask(R, ids, k, p):
    x, y = px(R, p); return bool(np.isin(R['inst'][k][y, x], ids))
def dist(a, b): return math.hypot(a[0] - b[0], a[1] - b[1]) / (1000.0 * math.sqrt(2))
def load(fn):
    out = []
    if fn and os.path.exists(fn):
        for l in open(fn):
            try: out.append(json.loads(l))
            except Exception: pass
    return out
def main():
    A, I = load(sys.argv[1]), load(sys.argv[2]); N = load(sys.argv[3]) if len(sys.argv) > 3 else []
    res = collections.OrderedDict(); st = collections.Counter()
    for r in A + I + N:
        c = r['meta']['call'][0]; f = r['meta']['family']; d = parse(r['text'])
        st['%s_%s_replies' % (c, f)] += 1; st['%s_%s_parsed' % (c, f)] += isinstance(d, dict); st['%s_%s_length' % (c, f)] += r.get('finish') == 'length'
    res['calls'] = dict(st); res['captures_A'] = len(set(r['meta']['canonical'] for r in A)); res['captures_I'] = len(set(r['meta']['canonical'] for r in I))
    facts = []; inv_facts = []; tabs = collections.defaultdict(dict)
    for r in A + I:
        m = r['meta']; cn = m['canonical']; T = table(parse(r['text']), m['kinds'])
        tabs[(cn, m['call'])][m['family']] = (T, m)
    for (cn, call), fams in tabs.items():
        R = raster(cn); area = float(R['H'] * R['W']); ds = cn.split('/')[0]; m = list(fams.values())[0][1]
        for kind in m['kinds']:
            role = m['roles'][kind]
            if role == 'inventory':
                for k in R['valid']:
                    v = {f: (T[kind].get(k) if T is not None else None) for f, (T, _) in fams.items()}
                    inv_facts.append(dict(cn=cn, ds=ds, call=call, kind=kind, k=k, v=v, info=m['inventory'].get(kind, {})))
                continue
            ids = [i for i, l in zip(R['ids'], R['labels']) if l == kind]
            for k in R['valid']:
                s = float(np.isin(R['inst'][k], ids).sum()) / area if ids else 0.0
                v = {f: (T[kind].get(k) if T is not None else None) for f, (T, _) in fams.items()}
                hit = {f: (inmask(R, ids, k, p) if isinstance(p, tuple) and ids else None) for f, p in v.items()}
                facts.append(dict(cn=cn, ds=ds, call=call, kind=kind, role=role, k=k, s=s, v=v, hit=hit, ids=ids))
    fams = sorted(set(f for x in facts for f in x['v']))
    said = lambda w: None if w is None else (w is not False)
    def by_ds(F, f):
        return {d: f([x for x in F if x['ds'] == d]) for d in ('arkitscenes', 'scannet', 'scannetpp')}
    def u(F, g): return {c: [g(x) for x in F if x['cn'] == c] for c in set(x['cn'] for x in F)}
    NM = [x for x in facts if x['role'] == 'named']
    for f in fams:
        o = collections.OrderedDict(); P1 = [x for x in NM if x['s'] >= 0.01 and said(x['v'].get(f)) is not None]; P0 = [x for x in NM if x['s'] == 0 and said(x['v'].get(f)) is not None]
        g1 = lambda x: said(x['v'][f]); g0 = lambda x: not said(x['v'][f])
        o['present_at_1pct'] = [pct([g1(x) for x in P1]), boot(u(P1, g1), pct), len(P1)]; o['absent_at_0px'] = [pct([g0(x) for x in P0]), boot(u(P0, g0), pct), len(P0)]
        o['present_at_1pct_by_ds'] = by_ds(P1, lambda S: pct([g1(x) for x in S])); o['absent_at_0px_by_ds'] = by_ds(P0, lambda S: pct([g0(x) for x in S]))
        o['present_at_0.2-1pct'] = pct([said(x['v'][f]) for x in NM if 0.002 <= x['s'] < 0.01 and said(x['v'].get(f)) is not None])
        for lo, hi, b in ((0.05, 2, '5pct_plus'), (0.01, 0.05, '1-5pct')):
            S = [x for x in NM if lo <= x['s'] < hi and x['hit'].get(f) is not None]
            o['point_in_mask_' + b] = [pct([x['hit'][f] for x in S]), len(S)]; o['point_in_mask_%s_by_ds' % b] = by_ds(S, lambda Q: pct([x['hit'][f] for x in Q]))
        res['named_' + f] = o
    B = [x for x in NM if len(fams) == 2 and all(said(x['v'].get(f)) is not None for f in fams)]
    o = collections.OrderedDict(); ag = lambda x: said(x['v'][fams[0]]) == said(x['v'][fams[1]])
    o['facts_both'] = len(B); o['kept_share'] = [pct([ag(x) for x in B]), boot(u(B, ag), pct)]
    Ag = [x for x in B if ag(x)]
    a1 = [x for x in Ag if x['s'] >= 0.01]; a0 = [x for x in Ag if x['s'] == 0]
    o['agreed_present_at_1pct'] = [pct([said(x['v'][fams[0]]) for x in a1]), boot(u(a1, lambda x: said(x['v'][fams[0]])), pct), len(a1)]
    o['agreed_present_at_1pct_by_ds'] = by_ds(a1, lambda S: pct([said(x['v'][fams[0]]) for x in S]))
    sp = [x for x in a1 if x['ds'] in ('scannet', 'scannetpp')]; o['agreed_present_at_1pct_scannet_pp'] = [pct([said(x['v'][fams[0]]) for x in sp]), boot(u(sp, lambda x: said(x['v'][fams[0]])), pct), len(sp)]
    o['agreed_absent_at_0px'] = [pct([not said(x['v'][fams[0]]) for x in a0]), len(a0)]
    o['agreed_correct_at_1pct_or_0px'] = pct([said(x['v'][fams[0]]) == (x['s'] >= 0.01) for x in Ag if x['s'] >= 0.01 or x['s'] == 0])
    o['both_wrong_at_1pct'] = pct([not said(x['v'][fams[0]]) and not said(x['v'][fams[1]]) for x in B if x['s'] >= 0.01])
    o['both_wrong_at_0px'] = pct([said(x['v'][fams[0]]) and said(x['v'][fams[1]]) for x in B if x['s'] == 0])
    pairs = [x for x in Ag if isinstance(x['v'][fams[0]], tuple) and isinstance(x['v'][fams[1]], tuple) and x['s'] > 0]
    for x in pairs:
        x['close'] = dist(x['v'][fams[0]], x['v'][fams[1]]) <= 0.05
        mid = ((x['v'][fams[0]][0] + x['v'][fams[1]][0]) / 2, (x['v'][fams[0]][1] + x['v'][fams[1]][1]) / 2); x['hm'] = inmask(raster(x['cn']), x['ids'], x['k'], mid)
    for lo, hi, b in ((0.05, 2, '5pct_plus'), (0.01, 0.05, '1-5pct')):
        S = [x for x in pairs if lo <= x['s'] < hi]; Sc = [x for x in S if x['close']]
        o['points_close_share_' + b] = pct([x['close'] for x in S])
        o['agreed_points_in_mask_' + b] = [pct([x['hm'] for x in Sc]), boot(u(Sc, lambda x: x['hm']), pct), len(Sc)]
        o['agreed_points_in_mask_%s_by_ds' % b] = by_ds(Sc, lambda Q: [pct([x['hm'] for x in Q]), len(Q)])
    res['two_family_named'] = o
    oc = collections.OrderedDict()
    for ty in ('absent_annotated', 'present_omitted', 'open'):
        C = [x for x in facts if x['role'] == 'check:' + ty]; e = collections.OrderedDict(); e['facts'] = len(C)
        for f in fams:
            if ty == 'absent_annotated': e[f + '_rejected_per_frame'] = pct([not said(x['v'][f]) for x in C if said(x['v'].get(f)) is not None])
            elif ty == 'present_omitted': e[f + '_present_at_1pct'] = pct([said(x['v'][f]) for x in C if x['s'] >= 0.01 and said(x['v'].get(f)) is not None])
            e[f + '_clip_accepts'] = pct([any(said(x['v'].get(f)) for x in C if (x['cn'], x['call'], x['kind']) == key) for key in set((x['cn'], x['call'], x['kind']) for x in C)])
        if len(fams) == 2:
            e['both_accept_same_frame_clip'] = pct([any(said(x['v'].get(fams[0])) and said(x['v'].get(fams[1])) for x in C if (x['cn'], x['call'], x['kind']) == key) for key in set((x['cn'], x['call'], x['kind']) for x in C)])
            e['both_wrong_per_frame'] = pct([bool(said(x['v'][fams[0]]) and said(x['v'][fams[1]])) for x in C if x['s'] == 0 and all(said(x['v'].get(f)) is not None for f in fams)])
        oc[ty] = e
    res['check_nouns'] = oc
    oi = collections.OrderedDict(); gt = []; prec = collections.Counter(); kinds_agreed = collections.defaultdict(set)
    named_by_cap = {}
    for (cn, call), fm in tabs.items(): named_by_cap[cn] = set(list(fm.values())[0][1]['named'])
    for x in inv_facts:
        if len(fams) == 2 and all(isinstance(x['v'].get(f), tuple) for f in fams) and dist(x['v'][fams[0]], x['v'][fams[1]]) <= 0.05:
            R = raster(x['cn']); mid = ((x['v'][fams[0]][0] + x['v'][fams[1]][0]) / 2, (x['v'][fams[0]][1] + x['v'][fams[1]][1]) / 2); xx, yy = px(R, mid)
            iid = int(R['inst'][x['k']][yy, xx]); lab = dict(zip(R['ids'], R['labels'])).get(iid)
            names = [x['kind']] + [a for al in (x['info'].get('aliases') or {}).values() for a in al]
            where = 'unannotated' if (lab is None or lab in STRUCT) else ('match' if any(names_match(n, lab) for n in names) else 'other_instance')
            x['mid'] = (x['k'], iid, where); prec[where] += 1; kinds_agreed[x['cn']].add(x['kind'])
    caps = sorted(set(x['cn'] for x in inv_facts))
    for cn in caps:
        R = raster(cn); area = float(R['H'] * R['W']); F = [x for x in inv_facts if x['cn'] == cn]
        hits = collections.defaultdict(set)
        for x in F:
            if 'mid' in x: hits[x['mid'][1]].add(x['kind'])
        single = collections.defaultdict(set)
        for x in F:
            for f in fams:
                p = x['v'].get(f)
                if isinstance(p, tuple): xx, yy = px(R, p); single[(f, int(R['inst'][x['k']][yy, xx]))].add(x['kind'])
        for i, lab in zip(R['ids'], R['labels']):
            if lab in STRUCT or lab in named_by_cap.get(cn, set()): continue
            if max([float((R['inst'][k] == i).sum()) / area for k in R['valid']] or [0]) < 0.01: continue
            kn = hits.get(i, set()); info = {x['kind']: x['info'] for x in F}
            nm = any(names_match(n, lab) for kd in kn for n in [kd] + [a for al in (info.get(kd, {}).get('aliases') or {}).values() for a in al])
            gt.append(dict(cn=cn, ds=cn.split('/')[0], label=lab, located=bool(kn), named=nm, **{'single_' + f: bool(single.get((f, i))) for f in fams}))
    oi['gt_instances_1pct'] = len(gt); oi['recall_located_agreed'] = [pct([x['located'] for x in gt]), boot(u(gt, lambda x: x['located']), pct)]
    oi['recall_named_agreed'] = [pct([x['named'] for x in gt]), boot(u(gt, lambda x: x['named']), pct)]
    for f in fams: oi['recall_located_' + f] = pct([x['single_' + f] for x in gt])
    oi['recall_named_agreed_by_ds'] = by_ds(gt, lambda S: pct([x['named'] for x in S]))
    tot = sum(prec.values()); oi['agreed_facts'] = tot; oi['agreed_fact_midpoint'] = {k: round(100.0 * v / tot, 1) for k, v in prec.items()} if tot else {}
    ak = [(cn, kd) for cn, s in kinds_agreed.items() for kd in s]; oi['agreed_kinds'] = len(ak)
    vocab = {cn: set(raster(cn)['labels']) for cn in caps}
    oi['agreed_kinds_outside_capture_gt_vocab'] = pct([not any(names_match(kd, l) for l in vocab[cn]) for cn, kd in ak])
    oi['agreed_kinds_outside_arkit17'] = pct([not any(names_match(kd, l) for l in ARKIT17) for cn, kd in ak])
    us = [m['union_size'] for (cn, call), fm in tabs.items() for (T, m) in fm.values() if call.startswith('I')]; oi['union_size_mean'] = round(sum(us) / len(us), 1) if us else None
    res['inventory'] = oi
    t = res['two_family_named']; a = t['agreed_present_at_1pct_scannet_pp'][0]; b = t['agreed_points_in_mask_5pct_plus'][0]; c = t['kept_share'][0]
    rj = [oc['absent_annotated'].get(f + '_rejected_per_frame') for f in fams]
    ln = sum(v for k, v in st.items() if k.endswith('_length')); nr = sum(v for k, v in st.items() if k.endswith('_replies'))
    res['bars'] = dict(agreed_presence_1pct_scannet_pp_95=a, agreed_points_5pct_90=b, absent_rejected_90=rj, kept_80=c, max_tokens_share_5=round(100.0 * ln / nr, 1) if nr else None,
                       passes=bool(a and b and c and a >= 95 and b >= 90 and c >= 80 and all(x is not None and x >= 90 for x in rj) and nr and 100.0 * ln / nr <= 5))
    print(json.dumps(res, indent=0)); json.dump(res, open(K + '/scores/%s.json' % os.environ.get('V6B_TAG', 'V6B_first30'), 'w'), indent=1)
if __name__ == '__main__': main()
PYEOF
cat > $K/kit/test_v6b.py <<'PYEOF'
"""nvkey3 dry test of v6b_jobs.py and score_v6b.py with an oracle labeller built from the rasters (writes only under K/v6b/test; sends nothing)."""
import json, os, sys, collections, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import v6b_jobs as J, score_v6b as S
from score_v1 import names_match
K = J.K; T = K + '/v6b/test'; os.makedirs(T, exist_ok=True)
for fn in os.listdir(T): os.replace(os.path.join(T, fn), os.path.join(T, '.old_' + fn))
qa, qn, qi = T + '/A.jsonl', T + '/N.jsonl', T + '/I.jsonl'
J.build(qa, qn, 'first30')
def oracle(t):
    m = t['meta']; R = S.raster(m['canonical']); area = float(R['H'] * R['W']); out = {}
    for k in range(32): out[str(k + 1)] = {}
    for kind in m['kinds']:
        role = m['roles'][kind]
        ids = [i for i, l in zip(R['ids'], R['labels']) if (names_match(kind, l) if role == 'inventory' else l == kind)]
        for k in range(32):
            mk = np.isin(R['inst'][k], ids) if ids else None
            if mk is not None and mk.sum() / area >= 0.002:
                ys, xs = np.nonzero(mk); j = len(ys) // 2; out[str(k + 1)][kind] = [int(1000 * (xs[j] + 0.5) / R['W']), int(1000 * (ys[j] + 0.5) / R['H'])]
            else: out[str(k + 1)][kind] = None
    return json.dumps(out)
def oracle_n(t):
    m = t['meta']; R = S.raster(m['canonical']); area = float(R['H'] * R['W']); inv = []
    for i, l in zip(R['ids'], R['labels']):
        if l in S.STRUCT or l in m['named'] or any(x['name'] == l for x in inv): continue
        if max([float((R['inst'][k] == i).sum()) / area for k in R['valid']] or [0]) >= 0.01: inv.append({'name': l, 'aliases': [l + ' unit', 'thing'], 'look_alike': 'box', 'one_object': True, 'part_of_larger': False, 'group': False})
    inv.append({'name': 'unicorn statue', 'aliases': ['statue', 'figure'], 'look_alike': 'lamp', 'one_object': True, 'part_of_larger': False, 'group': False})
    return json.dumps({'inventory': inv[:25]})
def fake(qf, of, f):
    with open(of, 'w') as o:
        for l in open(qf):
            t = json.loads(l); o.write(json.dumps({'id': t['id'], 'model': t['model'], 'meta': t['meta'], 'text': f(t), 'finish': 'stop'}) + '\n')
fake(qa, T + '/A.out.jsonl', oracle); fake(qn, T + '/N.out.jsonl', oracle_n)
print('chain', J.chain(T + '/N.out.jsonl', 'no_such_job', qi), 'again', J.chain(T + '/N.out.jsonl', 'no_such_job', qi))
fake(qi, T + '/I.out.jsonl', oracle)
A = [json.loads(l) for l in open(qa)]; N = [json.loads(l) for l in open(qn)]; I = [json.loads(l) for l in open(qi)]
print('tasks A', len(A), 'N', len(N), 'I', len(I), 'I per capture', collections.Counter(collections.Counter(t['meta']['canonical'] for t in I).values()))
print('kinds per A', collections.Counter(len(t['meta']['kinds']) for t in A), 'per I', collections.Counter(len(t['meta']['kinds']) for t in I))
print('images per task', collections.Counter(sum(1 for c in t['content'] if 'image' in c) for t in A + N + I))
print('A text:', A[0]['content'][0]['text'][:700].replace('\n', ' | '))
print('N text:', N[0]['content'][0]['text'][:900].replace('\n', ' | '))
print('I meta sample:', json.dumps({k: I[0]['meta'][k] for k in ('kinds', 'roles', 'union_size', 'n_replies', 'label_note')})[:700])
print('ids unique', len(set(t['id'] for t in A + N + I)) == len(A + N + I), 'tags', collections.Counter(t['meta']['tag'] for t in A + N + I))
PYEOF
sha256sum kit/v6b_jobs.py kit/score_v6b.py kit/test_v6b.py kit/score_v1.py | cut -c1-16,65-
timeout 900 $P -B kit/test_v6b.py 2>&1 | tail -20
V6B_TAG=V6B_oracle_test timeout 600 $P -B kit/score_v6b.py v6b/test/A.out.jsonl v6b/test/I.out.jsonl v6b/test/N.out.jsonl > v6b/test/score.txt 2>&1; echo "score rc $?"; tail -5 v6b/test/score.txt
$P -B -c "
import json; d=json.load(open('scores/V6B_oracle_test.json'))
print('calls', d['calls'])
for k in ('named_argon','two_family_named','check_nouns','inventory','bars'): print(k, json.dumps(d.get(k))[:900])"
$P -B - <<'PY'
import json, sys, collections, statistics as st
sys.path.insert(0, 'kit'); import score_v1 as N
for fn in ('out/45_v6p30.jsonl', 'out/48_v6p30astra.jsonl'):
    for l in open(fn):
        r = json.loads(l)
        if N.parse(r['text']) is None:
            t = N._JS.sub(N._jscall, (r['text'] or '').strip()); t = t[t.find('{'):]
            try: json.loads(t)
            except Exception as e: print('POST-JS FAIL', fn, r['id'][:22], len(t), str(e)[:70], repr(t[max(0, e.pos - 90):e.pos + 40]))
lat = collections.defaultdict(list)
for l in open('meter/CALLS.jsonl'):
    r = json.loads(l)
    if r.get('status') == 200 and r.get('secs'): lat[(r['job'], r['model'].split('/')[-1])].append(r['secs'])
for k, v in sorted(lat.items()):
    if k[0][:2] in ('30', '50', '52', '45', '46', '47', '48', '55', '56'): print('secs', k, 'n', len(v), 'median', round(st.median(v)), 'p90', round(sorted(v)[max(0, int(0.9 * len(v)) - 1)]), 'max', round(max(v)))
PY
cat meter/METER.json; echo; tail -2 runner.log; df -h /scratch | tail -1
