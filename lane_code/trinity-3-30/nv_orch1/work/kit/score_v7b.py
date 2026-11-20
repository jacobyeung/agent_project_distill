"""nv_orch1 V7 boolean-form checks (ORCH 0532Z; spec O11 first-100): per (clip, kind) two-family presence agreement (>=80%), point agreement where both
see the kind (within 5% of the frame diagonal; >=75%), decoy acceptance (both families present on any frame; <=10%), parse rates, agreed-fact yield.
usage: score_v7b.py OUTDIR [MAXCLIPS] -> scores/V7B_checks.json (reads OUTDIR/20_v7a.jsonl and 23_v7b.jsonl)"""
import json, sys, os, collections, math
sys.path.insert(0, '/scratch/jjyeung/orch_n30/nv_orch1/work/kit'); import forms_b as F
D = sys.argv[1]; maxc = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 9; diag = math.hypot(1000, 1000)
res = {}
for part, fn in (('a', '20_v7a.jsonl'), ('b', '23_v7b.jsonl')):
    p = os.path.join(D, fn)
    if not os.path.exists(p): continue
    lab = collections.defaultdict(dict); st = collections.Counter(); calls = collections.defaultdict(set)
    for l in open(p):
        r = json.loads(l); m = r['meta']; fam = F.fam(r['model']); d = F.parse(r['text']); st['calls_' + fam] += 1; st['parsed_' + fam] += isinstance(d, dict)
        st['finish_%s_%s' % (fam, r['finish'])] += 1; calls[m['clip']].add(fam)
        if not isinstance(d, dict): continue
        for kd in m['kinds']:
            pres = []; pts = []
            for k in range(32):
                v = (d.get(str(k + 1)) or {}).get(kd) if isinstance(d.get(str(k + 1)), dict) else None
                ok = isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v)
                pres.append(ok); pts.append(v if ok else None)
            lab[(m['clip'], kd)][fam] = (pres, pts, kd in (m.get('decoys') or []))
    clips = sorted(set(c for c, _ in lab))[:maxc]; cs = set(clips)
    fr = collections.Counter(); pa = collections.Counter(); dec = collections.Counter(); y = collections.Counter()
    for (c, kd), v in lab.items():
        if c not in cs or 'argon' not in v or 'other' not in v: continue
        (pa_, pta, isd), (ps_, pts, _) = v['argon'], v['other']
        anyboth = False
        for k in range(32):
            fr['frames'] += 1; fr['agree'] += pa_[k] == ps_[k]
            if pa_[k] or ps_[k]: fr['either'] += 1
            if pa_[k] and ps_[k]:
                fr['both'] += 1; anyboth = True
                if not isd:
                    y['agreed_presence_facts'] += 1
                    pa['pairs'] += 1; ok = math.hypot(pta[k][0] - pts[k][0], pta[k][1] - pts[k][1]) <= 0.05 * diag; pa['agree'] += ok; y['agreed_point_pairs_raw'] += ok
        if isd: dec['decoys'] += 1; dec['accepted_both'] += anyboth; dec['accepted_argon'] += any(pa_); dec['accepted_astra'] += any(ps_)
    res[part] = {'calls': dict(st), 'clips_scored': len(clips), 'clips_with_both_families': sum(1 for c in clips if calls[c] >= {'argon', 'other'}),
                 'presence_agreement_all_frames': round(fr['agree'] / max(1, fr['frames']), 3), 'presence_agreement_where_either': round(fr['both'] / max(1, fr['either']), 3),
                 'point_agreement_where_both': round(pa['agree'] / max(1, pa['pairs']), 3), 'point_pairs': pa['pairs'],
                 'decoy_acceptance_both': round(dec['accepted_both'] / max(1, dec['decoys']), 3), 'decoys': dict(dec), 'yield': dict(y)}
json.dump(res, open('/scratch/jjyeung/orch_n30/nv_orch1/work/scores/V7B_checks.json', 'w'), indent=1); print(json.dumps(res, indent=0))
