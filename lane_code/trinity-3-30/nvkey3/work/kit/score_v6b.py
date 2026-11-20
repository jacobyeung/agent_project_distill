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
    oi = collections.OrderedDict(); gt = []; gtl = []; prec = collections.Counter(); kinds_agreed = collections.defaultdict(set)
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
            gt.append(dict(cn=cn, ds=cn.split('/')[0], label=lab, iid=i, located=bool(kn), named=nm, **{'single_' + f: bool(single.get((f, i))) for f in fams}))
        for lab in sorted(set(x['label'] for x in gt if x['cn'] == cn)):
            G = [x for x in gt if x['cn'] == cn and x['label'] == lab]
            gtl.append(dict(cn=cn, ds=cn.split('/')[0], label=lab, located=any(x['located'] for x in G), named=any(x['named'] for x in G)))
    oi['gt_instances_1pct'] = len(gt); oi['recall_located_agreed'] = [pct([x['located'] for x in gt]), boot(u(gt, lambda x: x['located']), pct)]
    oi['recall_named_agreed'] = [pct([x['named'] for x in gt]), boot(u(gt, lambda x: x['named']), pct)]
    for f in fams: oi['recall_located_' + f] = pct([x['single_' + f] for x in gt])
    oi['recall_named_agreed_by_ds'] = by_ds(gt, lambda S: pct([x['named'] for x in S]))
    oi['gt_labels_1pct'] = len(gtl); oi['label_recall_named_agreed'] = [pct([x['named'] for x in gtl]), boot(u(gtl, lambda x: x['named']), pct)]
    oi['label_recall_located_agreed'] = pct([x['located'] for x in gtl]); oi['label_recall_named_agreed_by_ds'] = by_ds(gtl, lambda S: pct([x['named'] for x in S]))
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
