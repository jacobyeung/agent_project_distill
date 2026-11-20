K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1
cat > $K/kit/score_v6.py <<'PYEOF'
"""nvkey2 V6 form v2 scoring against K1 raster truth at the 32 anchors (consumer spec O3).
usage: score_v6.py PRIMARY_OUT.jsonl SECOND_OUT.jsonl -> K/scores/$V6_TAG.json (default V6_O3); the second file may be a verifier or another primary
Truth state per anchor: L share >= 5%, M 1-5%, S under 1% but nonzero, A zero; frames without depth are skipped.
Reports, per family and by dataset: L-or-M at 1% or more, A at 0 px, points in mask on L and M frames; two-family agreement (kept share, agreed
correct, both-wrong rate, agreed points within 5% of the diagonal, 3% on M frames, in mask); check-noun accuracy by type; blind inventory recall."""
import json, os, sys, re, math, random, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score_v1 import names_match, parse, boot, pct, norm
K = os.environ.get('NVK', '/scratch/jjyeung/orch_n30/nvkey1/work')
STRUCT = {'wall', 'floor', 'ceiling', 'object', 'objects', 'otherfurniture', 'otherprop', 'otherstructure', 'unknown', 'misc', 'structure', 'doorframe', 'beam', 'pipe', 'column'}
idx = json.load(open(K + '/k1r/k1r_index.json')); _R = {}
def raster(cn):
    if cn not in _R:
        z = np.load(K + '/k1r/' + idx[cn]['rel'], allow_pickle=True); inst = z['inst']; n, H, W = inst.shape
        _R[cn] = dict(inst=inst, ids=[int(x) for x in z['ids']], labels=[norm(x) for x in z['labels']], H=H, W=W,
                      valid=[k for k in range(32) if float(z['depth'][k].max()) > 0])
    return _R[cn]
def tstate(s): return 'A' if s == 0 else ('S' if s < 0.01 else ('M' if s < 0.05 else 'L'))
def states(e):
    s = (e or {}).get('states') if isinstance(e, dict) else None
    s = re.sub(r'[^LMSA]', '', str(s).upper()) if s else ''
    return s if len(s) == 32 else None
def pts(e):
    out = {}
    p = (e or {}).get('points') if isinstance(e, dict) else None
    if isinstance(p, dict):
        for L, v in p.items():
            try: k = int(L) - 1
            except Exception: continue
            if 0 <= k < 32 and isinstance(v, (list, tuple)) and len(v) == 2:
                try: out[k] = (float(v[0]), float(v[1]))
                except Exception: pass
    return out
def inmask(R, ids, k, p):
    xi = min(R['W'] - 1, max(0, int(p[0] / 1000.0 * R['W']))); yi = min(R['H'] - 1, max(0, int(p[1] / 1000.0 * R['H']))); return bool(np.isin(R['inst'][k][yi, xi], ids))
def main():
    P = {json.loads(l)['meta']['canonical']: json.loads(l) for l in open(sys.argv[1])}
    V = {json.loads(l)['meta']['canonical']: json.loads(l) for l in open(sys.argv[2])} if len(sys.argv) > 2 and os.path.exists(sys.argv[2]) else {}
    facts = []; checks = []; inv = []; parsed = collections.Counter()
    for cn, r in P.items():
        R = raster(cn); m = r['meta']; dp = parse(r['text']); v = V.get(cn); dv = parse(v['text']) if v else None
        parsed['primary_ok' if isinstance(dp, dict) else 'primary_bad'] += 1
        if v: parsed['verifier_ok' if isinstance(dv, dict) else 'verifier_bad'] += 1
        area = float(R['H'] * R['W']); ds = cn.split('/')[0]
        def share(label_ids, k): return float(np.isin(R['inst'][k], label_ids).sum()) / area
        for kind in m['named']:
            ids = [i for i, l in zip(R['ids'], R['labels']) if l == kind]
            ep = ((dp or {}).get('named') or {}).get(kind) if isinstance(dp, dict) else None
            ev = ((dv or {}).get('kinds') or (dv or {}).get('named') or {}).get(kind) if isinstance(dv, dict) else None
            sp, sv, pp, pv = states(ep), states(ev), pts(ep), pts(ev)
            for k in R['valid']:
                s = share(ids, k)
                facts.append(dict(cn=cn, ds=ds, kind=kind, k=k, t=tstate(s), p=sp[k] if sp else None, v=sv[k] if sv else None,
                                  pp=pp.get(k), pv=pv.get(k), hp=inmask(R, ids, k, pp[k]) if k in pp else None, hv=inmask(R, ids, k, pv[k]) if k in pv else None,
                                  hm=inmask(R, ids, k, ((pp[k][0] + pv[k][0]) / 2, (pp[k][1] + pv[k][1]) / 2)) if (k in pp and k in pv) else None))
        for kind in m['check']:
            ty = m['check_type'][kind]; ids = [i for i, l in zip(R['ids'], R['labels']) if l == kind]
            sp = states(((dp or {}).get('check') or {}).get(kind)) if isinstance(dp, dict) else None
            sv = states(((dv or {}).get('check') or {}).get(kind)) if isinstance(dv, dict) else None
            for k in R['valid']:
                s = share(ids, k) if ids else 0.0
                checks.append(dict(cn=cn, ds=ds, kind=kind, ty=ty, k=k, t=tstate(s), p=sp[k] if sp else None, v=sv[k] if sv else None))
        items = [x for x in ((dp or {}).get('inventory') or []) if isinstance(x, dict)] if isinstance(dp, dict) else []
        named = set(m['named'])
        for i, lab in zip(R['ids'], R['labels']):
            if lab in STRUCT or lab in named: continue
            sh = {k: float((R['inst'][k] == i).sum()) / area for k in R['valid']}
            if max(sh.values() or [0]) < 0.01: continue
            loc = nm = False
            for it in items:
                ip = pts(it); hit = any(R['inst'][k][min(R['H'] - 1, max(0, int(p[1] / 1000.0 * R['H']))), min(R['W'] - 1, max(0, int(p[0] / 1000.0 * R['W'])))] == i for k, p in ip.items() if k in sh)
                if hit:
                    loc = True
                    if any(names_match(a, lab) for a in [str(it.get('name', ''))] + [str(x) for x in (it.get('aliases') or [])][:2]): nm = True
            inv.append(dict(cn=cn, ds=ds, label=lab, named=nm, loc=loc))
    res = collections.OrderedDict(); res['parsed'] = dict(parsed); res['captures'] = len(P); res['verifier_captures'] = len(V)
    LM = ('L', 'M')
    def fam(F, key, tag):
        o = collections.OrderedDict(); u = lambda S, f: {c: [f(x) for x in S if x['cn'] == c] for c in set(x['cn'] for x in S)}
        S1 = [x for x in F if x['t'] in LM and x[key] is not None]; S0 = [x for x in F if x['t'] == 'A' and x[key] is not None]
        o['LM_at_1pct'] = [pct([x[key] in LM for x in S1]), boot(u(S1, lambda x: x[key] in LM), pct), len(S1)]
        o['A_at_0px'] = [pct([x[key] == 'A' for x in S0]), boot(u(S0, lambda x: x[key] == 'A'), pct), len(S0)]
        o['L_given_L'] = pct([x[key] == 'L' for x in F if x['t'] == 'L' and x[key] is not None]); o['M_given_M'] = pct([x[key] == 'M' for x in F if x['t'] == 'M' and x[key] is not None])
        o['S_truth_said_LM'] = pct([x[key] in LM for x in F if x['t'] == 'S' and x[key] is not None])
        hk = 'hp' if key == 'p' else 'hv'
        for b in LM: o['point_in_mask_truth_' + b] = [pct([x[hk] for x in F if x['t'] == b and x[key] in LM and x[hk] is not None]), sum(1 for x in F if x['t'] == b and x[key] in LM and x[hk] is not None)]
        for dsn in ('arkitscenes', 'scannet', 'scannetpp'):
            G = [x for x in F if x['ds'] == dsn]
            o['LM_at_1pct_' + dsn] = pct([x[key] in LM for x in G if x['t'] in LM and x[key] is not None]); o['A_at_0px_' + dsn] = pct([x[key] == 'A' for x in G if x['t'] == 'A' and x[key] is not None])
            o['point_LM_' + dsn] = pct([x[hk] for x in G if x['t'] in LM and x[key] in LM and x[hk] is not None])
        res[tag] = o
    fam(facts, 'p', 'primary_named'); fam(facts, 'v', 'verifier_named')
    B = [x for x in facts if x['p'] is not None and x['v'] is not None]
    co = lambda s: 'LM' if s in LM else s
    agree = [x for x in B if co(x['p']) == co(x['v'])]
    o = collections.OrderedDict(); o['facts_both'] = len(B); o['kept_share'] = pct([co(x['p']) == co(x['v']) for x in B])
    o['agreed_LM_at_1pct'] = pct([co(x['p']) == 'LM' for x in agree if x['t'] in LM]); o['agreed_A_at_0px'] = pct([x['p'] == 'A' for x in agree if x['t'] == 'A'])
    o['both_wrong_at_1pct'] = pct([x['p'] not in LM and x['v'] not in LM for x in B if x['t'] in LM]); o['both_wrong_at_0px'] = pct([x['p'] in LM and x['v'] in LM for x in B if x['t'] == 'A'])
    ap = []
    for x in B:
        if x['p'] in LM and x['v'] in LM and x['pp'] and x['pv'] and x['t'] in LM:
            d = math.hypot(x['pp'][0] - x['pv'][0], x['pp'][1] - x['pv'][1]) / (1000.0 * math.sqrt(2)); tol = 0.03 if (x['p'] == 'M' or x['v'] == 'M') else 0.05
            ap.append((x, d <= tol))
    kept = [x for x, ok in ap if ok]; o['points_agree_share'] = pct([ok for x, ok in ap])
    o['agreed_points_in_mask'] = [pct([x['hm'] for x in kept]), boot({c: [x['hm'] for x in kept if x['cn'] == c] for c in set(x['cn'] for x in kept)}, pct), len(kept)]
    for b in LM: o['agreed_points_in_mask_truth_' + b] = [pct([x['hm'] for x in kept if x['t'] == b]), sum(1 for x in kept if x['t'] == b)]
    for dsn in ('arkitscenes', 'scannet', 'scannetpp'):
        o['agreed_points_in_mask_' + dsn] = [pct([x['hm'] for x in kept if x['ds'] == dsn]), sum(1 for x in kept if x['ds'] == dsn)]
        o['agreed_points_in_mask_M_' + dsn] = [pct([x['hm'] for x in kept if x['ds'] == dsn and x['t'] == 'M']), sum(1 for x in kept if x['ds'] == dsn and x['t'] == 'M')]
    res['two_family_named'] = o
    oc = collections.OrderedDict()
    for ty in ('absent_annotated', 'present_omitted', 'open'):
        C = [x for x in checks if x['ty'] == ty]
        if ty == 'absent_annotated':
            oc[ty] = dict(primary_A=pct([x['p'] == 'A' for x in C if x['p']]), verifier_A=pct([x['v'] == 'A' for x in C if x['v']]),
                          clip_all_A_primary=pct([all(x['p'] == 'A' for x in C if x['cn'] == c and x['kind'] == kd and x['p']) for c, kd in set((x['cn'], x['kind']) for x in C)]),
                          both_wrong=pct([x['p'] in LM and x['v'] in LM for x in C if x['p'] and x['v']]), facts=len(C))
        elif ty == 'present_omitted':
            oc[ty] = dict(primary_LM_at_1pct=pct([x['p'] in LM for x in C if x['t'] in LM and x['p']]), verifier_LM_at_1pct=pct([x['v'] in LM for x in C if x['t'] in LM and x['v']]),
                          primary_A_at_0=pct([x['p'] == 'A' for x in C if x['t'] == 'A' and x['p']]), facts=len(C))
        else:
            oc[ty] = dict(agree=pct([co(x['p']) == co(x['v']) for x in C if x['p'] and x['v']]), primary_any_LM=pct([any(x['p'] in LM for x in C if x['cn'] == c and x['kind'] == kd and x['p']) for c, kd in set((x['cn'], x['kind']) for x in C)]), facts=len(C))
    res['check_nouns'] = oc
    oi = collections.OrderedDict(); oi['gt_instances'] = len(inv); oi['recall_named'] = [pct([x['named'] for x in inv]), boot({c: [x['named'] for x in inv if x['cn'] == c] for c in set(x['cn'] for x in inv)}, pct)]
    oi['recall_located'] = pct([x['loc'] for x in inv])
    for dsn in ('arkitscenes', 'scannet', 'scannetpp'): oi['recall_named_' + dsn] = pct([x['named'] for x in inv if x['ds'] == dsn])
    res['blind_inventory'] = oi
    a = res['primary_named']['LM_at_1pct'][0]; b = res['primary_named']['A_at_0px'][0]; c = res['two_family_named']['agreed_points_in_mask'][0]
    res['O3_gate'] = dict(LM_at_1pct_95=a, A_at_0px_97=b, agreed_points_90=c, passes=bool(a and b and c and a >= 95 and b >= 97 and c >= 90))
    print(json.dumps(res, indent=0)); json.dump(res, open(K + '/scores/%s.json' % os.environ.get('V6_TAG', 'V6_O3'), 'w'), indent=1)
if __name__ == '__main__': main()
PYEOF
P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%T; cat meter/METER.json; wc -l out/4*.jsonl out/55_v2cal.jsonl; tail -2 runner.log
timeout 300 $P -B kit/score_v2.py out/55_v2cal.jsonl > scores/V2cal.txt 2>&1; echo v2 rc $?; tr -d '\n' < scores/V2cal.txt | cut -c1-2500; echo
$P -B kit/ledger.py nvkey2 '{"50_v1a32": "V1 form (a) calibration: guided names plus 3 decoys, frames, points, instances and counts, 32 anchors, 22 K1 training captures vs raster truth (tag calibration)", "51_v1a64": "V1 form (a) at 64 frames (stopped at 34 of 44 under O10)", "52_v1b32": "V1 form (b) calibration: blind inventory, 32 anchors, 22 K1 training captures vs raster truth", "53_v1c_pilot": "V1 form (c) judge with ring plus 256-px crop on the 1,208 dev-S1 pilot pointing rows (analysis only)", "54_v1c_nearmiss": "V1 form (c) judge on 300 raster near-miss claims from 22 K1 training captures (calibration for V4 flags)"}'
