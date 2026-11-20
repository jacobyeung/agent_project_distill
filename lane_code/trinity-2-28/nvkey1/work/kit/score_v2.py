"""nvkey2 V2 alias-table calibration: for each numbered crop of a K1 training GT instance, is the GT class or a synonym from the frozen SYN list
(score_v1.py, sha256 de175d44) among the top-3 phrases; does the one_object flag agree with the raster (one GT instance = one object); parse rate.
usage: score_v2.py OUT.jsonl [INSTANCES.json] -> K/scores/V2cal.json"""
import json, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score_v1 import names_match, parse, pct, boot, SYN, norm
K = os.environ.get('NVK', '/scratch/jjyeung/orch_n30/nvkey1/work')
inst = {x['id']: x for x in json.load(open(sys.argv[2] if len(sys.argv) > 2 else K + '/v2/INSTANCES.json'))}
synw = set(w for s in SYN for w in s)
rows = []; calls = collections.Counter()
for l in open(sys.argv[1]):
    r = json.loads(l); d = parse(r['text']); fam = r['model'].split('/')[-1]; calls[(fam, d is not None)] += 1
    for q, iid in enumerate(r['meta']['items']):
        x = inst[iid]; e = (d or {}).get(str(q + 1)) if isinstance(d, dict) else None
        ph = [str(p) for p in (e.get('phrases') or [])] if isinstance(e, dict) else []
        qn = str(e.get('question_noun', '')) if isinstance(e, dict) else ''
        rows.append(dict(fam=fam, cn=x['canonical'], label=x['label'], ds=x['dataset'], parsed=isinstance(e, dict) and len(ph) >= 3,
                         top3=any(names_match(p, x['label']) for p in ph[:3]) if ph else None, top5=any(names_match(p, x['label']) for p in ph[:5]) if ph else None,
                         qn=names_match(qn, x['label']) if qn else None, one=(e.get('one_object') is True) if isinstance(e, dict) else None,
                         part=(e.get('part_of_larger') is True) if isinstance(e, dict) else None, ctrl=x['label'] in synw or x['label'].split()[-1] in synw))
res = collections.OrderedDict(); res['calls'] = {'%s parsed=%s' % k: v for k, v in calls.items()}
for fam in sorted(set(r['fam'] for r in rows)):
    R = [r for r in rows if r['fam'] == fam]; C = [r for r in R if r['ctrl']]; o = collections.OrderedDict()
    u = lambda S, k: {c: [r[k] for r in S if r['cn'] == c] for c in set(r['cn'] for r in S)}
    o['items'] = len(R); o['parse_fail'] = pct([not r['parsed'] for r in R])
    o['control_items'] = len(C); o['control_top3'] = [pct([r['top3'] for r in C]), boot(u(C, 'top3'), pct)]; o['control_top5'] = pct([r['top5'] for r in C])
    o['all_top3'] = [pct([r['top3'] for r in R]), boot(u(R, 'top3'), pct)]; o['question_noun_match_all'] = pct([r['qn'] for r in R]); o['question_noun_match_control'] = pct([r['qn'] for r in C])
    o['one_object_true'] = pct([r['one'] for r in R]); o['part_of_larger_true'] = pct([r['part'] for r in R])
    for ds in ('arkitscenes', 'scannet', 'scannetpp'): o['all_top3_' + ds] = pct([r['top3'] for r in R if r['ds'] == ds])
    res[fam] = o
print(json.dumps(res, indent=0)); json.dump(res, open(K + '/scores/V2cal.json', 'w'), indent=1)
