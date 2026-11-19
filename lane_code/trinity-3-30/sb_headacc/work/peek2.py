import sys, json
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
S = K._scorer(); O = S.O
rows, items, _, src = S.load(O.parent / 'out3/A4/ret', O / 'A', 0, 200, 'candidates_argmax')
def short(v, n=1500):
    s = json.dumps(v, default=str)
    return s if len(s) <= n else s[:n] + '...<%d>' % len(s)
n=0
for k in sorted(rows):
    it=items[k]
    if it['question_type']!='object_abs_distance': continue
    o=rows[k]['output']
    if not o['calls']['records']: continue
    print('ITEM', k, short(it, 900))
    print('TEXT', o['text'][:1500])
    for kk in ('calls','entries','scale','perception_memo','frames','decode_budget','scores','timings'):
        print(kk, short(o.get(kk), 5000))
    print('heads keys', {a: (len(b) if hasattr(b,'__len__') else b) for a,b in o['heads'].items()})
    n+=1
    if n>=1: break
