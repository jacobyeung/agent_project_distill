K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1; P=/scratch/jjyeung/envs/p1cpu/bin/python
cat > $K/kit/v2_handover.py <<'PYEOF'
"""nvkey3: hand-over file for the phrase-kit lane from job 56_v2o4 (Argon and Astra naming the 146 O4 crops; ORCH ANSWER 0518Z).
Writes K/v2/O4_ALIAS_CANDIDATES.jsonl: one line per O4 instance keyed by (canonical, ground-truth instance id), each family's five phrases,
question-writer noun and two flags, the union of phrases, and the tag. usage: v2_handover.py"""
import json, os, sys, hashlib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score_v1 import parse
K = os.environ.get('NVK', '/scratch/jjyeung/orch_n30/nvkey1/work')
TAG = 'uncertified namer; candidates only'
CONTROL = {'job': '55_v2cal', 'controls': 175, 'argon_top3': [81.1, [75.1, 86.8]], 'argon_top5': 87.4, 'opus_top3': [71.4, [64.6, 78.0]],
           'one_object_true': {'argon': 92.0, 'opus': 89.7}, 'bar': 'top 3 at 90% and one_object at 95%; kill line: control hit under 85%',
           'verdict': 'V2 failed its control bar (RESULT/QUESTION 0517Z); ORCH ANSWER 0518Z: send the 146 O4 crops as candidates only, two families'}
inst = {x['id']: x for x in json.load(open(K + '/v2/O4_INSTANCES.json'))}
out = collections.OrderedDict((i, dict(id=i, canonical=x['canonical'], dataset=x['dataset'], gt_instance=x['inst'], gt_label=x['label'], operand=x['operand'],
                                       never_proposed=x['never_proposed'], category=x['category'], fold=x['fold'], crop_frame=x['frame'], crop_share=x['share'],
                                       families={}, tag=TAG)) for i, x in inst.items())
bad = collections.Counter()
for l in open(K + '/out/56_v2o4.jsonl'):
    r = json.loads(l); fam = 'argon' if 'argon' in r['model'] else ('astra' if 'astra' in r['model'] else r['model'])
    d = parse(r['text']); items = r['meta']['items']
    if not isinstance(d, dict): bad[fam] += 1; continue
    for j, it in enumerate(items, 1):
        iid = it['id'] if isinstance(it, dict) else it; e = d.get(str(j))
        if iid not in out: bad['unknown_item'] += 1; continue
        if not isinstance(e, dict): bad[fam + '_missing'] += 1; continue
        out[iid]['families'][fam] = dict(phrases=[str(p) for p in (e.get('phrases') or [])][:5], question_noun=e.get('question_noun'),
                                         part_of_larger=e.get('part_of_larger'), one_object=e.get('one_object'), served=r.get('served'), reply_id=r['id'])
for v in out.values():
    seen = []
    for fam in sorted(v['families']):
        for p in v['families'][fam]['phrases']:
            if p.lower() not in [s.lower() for s in seen]: seen.append(p)
    v['phrase_union'] = seen
p = K + '/v2/O4_ALIAS_CANDIDATES.jsonl'
with open(p, 'w') as f:
    f.write(json.dumps({'header': True, 'tag': TAG, 'source_job': '56_v2o4', 'instances_file': 'v2/O4_INSTANCES.json',
                        'instances_sha256': hashlib.sha256(open(K + '/v2/O4_INSTANCES.json', 'rb').read()).hexdigest(), 'control': CONTROL,
                        'binding_rule': 'a phrase binds only after SAM 3 at the served setting finds the instance on K1-train anchors and the fold rule picks it in 4 of 5 folds (consumer spec PHRASE), and only after PHRASE_KIT part 2'}) + '\n')
    for v in out.values(): f.write(json.dumps(v) + '\n')
fams = collections.Counter(len(v['families']) for v in out.values())
print('handover', p, 'instances', len(out), 'families per instance', dict(fams), 'bad', dict(bad), 'sha256', hashlib.sha256(open(p, 'rb').read()).hexdigest(), 'bytes', os.path.getsize(p))
print('sample', json.dumps(list(out.values())[0])[:600])
PYEOF
date -u +%T; wc -l out/60_v6bA_first30.jsonl out/61_v6bN_first30.jsonl queue/62_v6bI_first30.jsonl 2>&1 | head -5; tail -4 runner.log; tail -2 v6b/chain.log; cat meter/METER.json; echo
$P -B kit/v2_handover.py
