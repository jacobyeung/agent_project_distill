"""nv_orch1 V7 first-100 checks (spec O11): two-family presence agreement (>=80%), point agreement (>=75%), absent-noun acceptance (<=10%),
plus parse/finish rates and the agreed-label yield under RULING 0516Z (presence at L or M from both families; points only where both say L, within 5% of
the diagonal). usage: score_v7.py PRIMARY_OUT.jsonl VERIFIER_OUT.jsonl -> scores/V7_checks.json"""
import json, sys, collections, math
sys.path.insert(0, '/scratch/jjyeung/orch_n30/nv_orch1/work/kit'); import forms_v2 as F
P = {json.loads(l)['id'][:-2]: json.loads(l) for l in open(sys.argv[1])}; V = {json.loads(l)['id'][:-2]: json.loads(l) for l in open(sys.argv[2])}
st = collections.Counter(); fr = collections.Counter(); pa = collections.Counter(); chk = collections.Counter(); yield_ = collections.Counter(); diag = math.hypot(1000, 1000)
def states(x):
    s = (x or {}).get('states') if isinstance(x, dict) else None
    return s if isinstance(s, str) and len(s) == 32 else None
for k, p in P.items():
    st['primary'] += 1; dp = F.parse(p['text']); st['primary_parsed'] += dp is not None; st['finish_' + str(p['finish'])] += 1
    v = V.get(k)
    if not v: st['no_verifier'] += 1; continue
    dv = F.parse(v['text']); st['verifier_parsed'] += dv is not None
    if not (isinstance(dp, dict) and isinstance(dv, dict)): continue
    inv = collections.defaultdict(list)
    for x in dp.get('inventory') or []:
        if isinstance(x, dict) and x.get('name'): inv[F.norm(x['name'])].append(x)
    vk = {F.norm(n): x for n, x in (dv.get('kinds') or {}).items()} if isinstance(dv.get('kinds'), dict) else {}
    rej = {F.norm(x) for x in (dv.get('rejects') or []) if isinstance(x, str)}
    for name, xs in inv.items():
        st['kinds'] += 1; st['kinds_rejected'] += name in rej
        sp = [states(x) for x in xs if states(x)]; sv = states(vk.get(name))
        if not sp or not sv: st['kinds_no_states'] += 1; continue
        merged = ''.join(max((s[i] for s in sp), key='ASML'.index) for i in range(32))  # most visible instance per frame
        for i in range(32):
            a, b = merged[i] in 'LM', sv[i] in 'LM'
            fr['frames'] += 1; fr['agree'] += a == b
            if a or b: fr['either'] += 1; fr['both'] += a and b
            if a and b: yield_['presence_facts'] += 1
            if merged[i] == 'L' and sv[i] == 'L':
                pp = [x.get('points', {}).get(str(i + 1)) for x in xs if isinstance(x.get('points'), dict)]; pp = [q for q in pp if isinstance(q, list) and len(q) == 2]
                qv = (vk.get(name) or {}).get('points', {}); qv = qv.get(str(i + 1)) if isinstance(qv, dict) else None
                if pp and isinstance(qv, list) and len(qv) == 2:
                    pa['pairs'] += 1; d = min(math.hypot(q[0] - qv[0], q[1] - qv[1]) for q in pp)
                    if d <= 0.05 * diag: pa['agree'] += 1; yield_['point_facts'] += 1
    for name, typ in (p['meta'].get('check_type') or {}).items():
        a = states((dp.get('check') or {}).get(name)); b = states((dv.get('check') or {}).get(name))
        chk['nouns'] += 1
        if a and b:
            chk['scored'] += 1; chk['accepted_both'] += any(a[i] in 'LM' and b[i] in 'LM' for i in range(32)); chk['accepted_primary'] += any(c in 'LM' for c in a)
res = {'calls': dict(st), 'presence_agreement_all_frames': round(fr['agree'] / max(1, fr['frames']), 3), 'presence_agreement_where_either_present': round(fr['both'] / max(1, fr['either']), 3),
       'point_agreement_L_both': round(pa['agree'] / max(1, pa['pairs']), 3), 'point_pairs': pa['pairs'],
       'absent_noun_acceptance_both': round(chk['accepted_both'] / max(1, chk['scored']), 3), 'absent_noun_acceptance_primary': round(chk['accepted_primary'] / max(1, chk['scored']), 3), 'check': dict(chk),
       'yield': dict(yield_), 'bars': {'presence': '>=0.80', 'point': '>=0.75', 'absent_noun': '<=0.10', 'by_eye': '>=0.90 (separate)'}}
json.dump(res, open('/scratch/jjyeung/orch_n30/nv_orch1/work/scores/V7_checks.json', 'w'), indent=1); print(json.dumps(res, indent=0))
