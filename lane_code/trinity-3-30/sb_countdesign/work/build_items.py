"""Lane sb_countdesign: the fixed item list of the count pricing kit. All 535 dev counting items (dev-S1 150, R0-dev 385) with the queried
categories, truth, scene, the 32 source frame indices, and the direct answers of step 544 and of R1 step 200 (B2048 arm).
Run: /usr/bin/python3 build_items.py   (writes ../files/COUNT_ITEMS_535.jsonl and ../files/ITEMS93.json)"""
import sys, json, re, collections, hashlib
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_count/work'); import cnt
K = cnt.K
def categories(q):
    out = []
    for c in re.findall(r"((?:[A-Za-z\-']+ ){0,5}[A-Za-z\-']+)\(s\)", q):
        w = c.lower()
        for key in ('how many ', 'count of ', 'number of ', 'quantity of ', 'amount of ', 'among the ', ' and '):
            if key in w: w = w.split(key)[-1]
        ws = w.replace("'", ' ').split()
        while ws and ws[0] in cnt.STOP | {'the', 'total', 'exact', 'precisely', 'specify', 'clarify', 'knowing', 'appreciate'}: ws = ws[1:]
        out.append(' '.join(ws))
    return out
idmap = json.load(open(K.IDMAP))
items = []
for s in ('dev-S1', 'R0-dev'):
    on, b, it = K._files(K.X[('R1', 200)], K.FAM[s])
    raw = {r['id']: r for r in K._jl(on) if r['question_type'] == 'object_counting'}
    per = {}
    for run, step in cnt.CK:
        for r in K.direct(run, step, s, types=['object_counting']): per.setdefault(r['id'], {})['%s_%d' % (run, step)] = r
    for i, d in per.items():
        r = d['R1_200']; w = raw[i]
        if s == 'dev-S1': scene = w['scene']; dataset = w['dataset']; src = dict(native=w.get('native'), source_qid=i)
        else:
            m = idmap[i]; scene = m['room']; dataset = m['dataset']; src = dict(r0_id=m['id'], source_qid=m['source_qid'])
        cats = categories(r['question'])
        items.append(dict(id=i, set=s, dataset=dataset, scene=scene, room=r['room'], question=r['question'], categories=cats, subtype=r['subtype'] or 'single',
                          truth=int(float(r['gt'])), large=float(r['gt']) >= 5, source_frame_indices=w['source_frame_indices'], total_num_frames=w.get('total_num_frames'), fps=w.get('fps'), source=src,
                          direct={k: dict(pred=v['pred'], score=v['score'], forced_close=bool(v['forced_close'])) for k, v in d.items()}))
with open('../files/COUNT_ITEMS_535.jsonl', 'w') as f:
    for x in items: f.write(json.dumps(x, sort_keys=True) + '\n')
big = [x for x in items if x['large']]
json.dump(big, open('../files/ITEMS93.json', 'w'), indent=0, sort_keys=True)
print('items', len(items), collections.Counter(x['set'] for x in items), 'large', len(big), collections.Counter(x['set'] for x in big))
print('ncats', collections.Counter((x['set'], len(x['categories'])) for x in items))
allc = collections.Counter(c for x in items for c in x['categories']); print('distinct categories', len(allc)); print(sorted(allc)[:400])
for s in ('dev-S1', 'R0-dev'):
    L = [x for x in items if x['set'] == s]
    print(s, 'scenes', len(set(x['scene'] for x in L)), 'rooms', len(set(x['room'] for x in L)), 'prompts (scene, category)', len(set((x['scene'], c) for x in L for c in x['categories'])),
          '| large: scenes', len(set(x['scene'] for x in L if x['large'])), 'prompts', len(set((x['scene'], c) for x in L if x['large'] for c in x['categories'])), 'datasets', collections.Counter(x['dataset'] for x in L if x['large']))
    for k in ('S1_544', 'R1_200'):
        print('   bar', k, 'large %.2f' % (100 * sum(x['direct'][k]['score'] for x in L if x['large']) / sum(1 for x in L if x['large'])), 'all %.2f' % (100 * sum(x['direct'][k]['score'] for x in L) / len(L)))
for k in ('S1_544', 'R1_200'): print('pooled bar', k, '%.2f' % (100 * sum(x['direct'][k]['score'] for x in big) / len(big)))
print('sha256', {n: hashlib.sha256(open('../files/' + n, 'rb').read()).hexdigest() for n in ('COUNT_ITEMS_535.jsonl', 'ITEMS93.json')})
