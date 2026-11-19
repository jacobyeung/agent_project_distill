# Q6: room size: step-200 direct traces vs step-544 calls; failure modes by truth band and unit.
import sys; sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_dist/work'); from common import *
from collections import Counter
import numpy as np
d = load()
def rk(v): return np.argsort(np.argsort(v))
for part in ('B', 'A'):
    r2 = {r['id']: r for r in d[(part, 200)] if r['type'] == 'room_size_estimation'}; r5 = {r['id']: r for r in d[(part, 544)] if r['type'] == 'room_size_estimation'}
    ids = sorted(r2); n = len(ids)
    print('==== part', part, 'items', n, 'MRA 200 %.1f 544 %.1f' % (100 * np.mean([r2[i]['score'] for i in ids]), 100 * np.mean([r5[i]['score'] for i in ids])))
    th = lambda i: r2[i]['text'].split('</think>')[0]
    print(' forms 200: Seen: %d, farthest apart %d, "floor area in square" %d, any number+unit in think %d, objects listed mean %.1f' % (
        sum('Seen:' in th(i) for i in ids), sum('farthest apart' in th(i) for i in ids), sum('floor area in square' in th(i) for i in ids),
        sum(bool(re.search(r'\d\s*(?:m\b|m\^?2|square|sq|feet|ft|meters?)', th(i))) for i in ids), np.mean([len(re.findall(r' in frame \d+', th(i))) for i in ids])))
    sqft = [i for i in ids if re.search(r'square (?:feet|foot)|sq\.? ?ft', r2[i]['question'], re.I)]
    for i in sqft:
        a = num(r2[i]['answer']); t = float(r2[i]['gt'])
        print('  sqft %s gt %.1f ans %s score %.1f | ans/10.764=%.1f | think says: %s' % (i[-8:], t, a, r2[i]['score'], (a or 0) / 10.7639, th(i).strip().split('\n')[0][:70]))
    sm = [i for i in ids if i not in sqft]
    a = np.array([num(r2[i]['answer']) for i in sm]); t = np.array([float(r2[i]['gt']) for i in sm]); s = np.array([r2[i]['score'] for i in sm])
    print(' sq m items %d: MRA %.1f; spearman(ans,truth) %.2f pearson %.2f; ans median %.1f IQR %.1f-%.1f; truth median %.1f IQR %.1f-%.1f; over %d under %d' % (
        len(sm), 100 * s.mean(), np.corrcoef(rk(a), rk(t))[0, 1], np.corrcoef(a, t)[0, 1], np.median(a), *np.percentile(a, [25, 75]), np.median(t), *np.percentile(t, [25, 75]), (a > t).sum(), (a < t).sum()))
    bc = max(np.arange(5, 80, 0.5), key=lambda c: np.mean([mra(c, tt) for tt in t])); print('  best constant %.1f m2 MRA %.1f' % (bc, 100 * np.mean([mra(bc, tt) for tt in t])))
    for lo, hi in ((0, 10), (10, 20), (20, 35), (35, 60), (60, 1e9)):
        m = (t >= lo) & (t < hi)
        if m.any(): print('  truth %3d-%-4s n %3d MRA %5.1f  mean ans/truth %.2f  MRA=0: %d' % (lo, str(hi) if hi < 1e8 else 'inf', m.sum(), 100 * s[m].mean(), np.mean(a[m] / t[m]), (s[m] == 0).sum()))
    # 544 behaviour
    fin = Counter(r5[i]['finish'] for i in ids); print(' 544 finish', dict(fin), 'calls', Counter(tuple(c['call'] for c in r5[i]['calls']) for i in ids).most_common(3))
    eos = [i for i in ids if r5[i]['finish'] == 'eos']
    resp = Counter(re.sub(r'\d+(?:\.\d+)?', 'N', (r5[i]['calls'][0].get('response') or ''))[:120] for i in eos)
    print(' 544 eos items', len(eos), 'MRA %.1f' % (100 * np.mean([r5[i]['score'] for i in eos]) if eos else 0), 'responses', resp.most_common(3))
    cap = [i for i in ids if r5[i]['finish'] == 'max_calls']
    print(' 544 capped: first response forms', Counter(re.sub(r'\d+(?:\.\d+)?', 'N', (r5[i]['calls'][0].get('response') or ''))[:100] for i in cap).most_common(2))
    print(' 544 capped: second response forms', Counter(re.sub(r'\d+(?:\.\d+)?', 'N', (r5[i]['calls'][1].get('response') or ''))[:100] for i in cap if len(r5[i]['calls']) > 1).most_common(2))
    if part == 'B':
        for i in eos[:2]: print('  544 eos example', i, 'gt', r5[i]['gt'], 'ans', r5[i]['answer'], 'score', r5[i]['score'], '|', r5[i]['text'][:700].replace('\n', ' | '))
        for i in cap[:1]: print('  544 capped example', i, '|', r5[i]['text'][:900].replace('\n', ' | '))
