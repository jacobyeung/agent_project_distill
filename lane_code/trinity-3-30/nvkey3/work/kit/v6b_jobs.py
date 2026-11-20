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
