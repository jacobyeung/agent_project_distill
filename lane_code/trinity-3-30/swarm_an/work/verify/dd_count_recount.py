import sys, re, collections
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
def num(x):
    try: return float(str(x).strip())
    except Exception: return None
for s in ('dev-S1', 'R0-dev'):
    old = K.direct('S1', 544, s, types=['object_counting']); new = K.direct('R1', 200, s, types=['object_counting'])
    print(s, 'step 544 force-closed', sum(bool(r['forced_close']) for r in old), 'of', len(old), '| step 200', sum(bool(r['forced_close']) for r in new), 'of', len(new))
    # truth-3 undercount at step 200, single category, not runaway: number of list entries
    c = collections.Counter(); n3 = 0
    for r in new:
        if r['forced_close'] or (s == 'R0-dev' and r['subtype'] != 'single'): continue
        g, p = num(r['gt']), num(r['pred'])
        if g != 3 or p is None or p >= g: continue
        th = (r['text'] or '').split('</think>')[0]
        m = re.search(r'first appears:(.*?)(?:\n|$)', th)
        if not m: c['no list']; c['nolist'] += 1; continue
        ents = [e for e in m.group(1).strip().rstrip('.').split(';') if e.strip()]
        n3 += 1; c[len(ents)] += 1
    print('  truth 3 undercount with a first-seen list:', n3, 'entries histogram', dict(c))
    if s == 'R0-dev':
        mu = [r for r in new if r['subtype'] == 'multiple']; t2 = [r for r in mu if num(r['gt']) == 2]; nr = [r for r in t2 if not r['forced_close']]
        print('  multiple', len(mu), 'truth 2', len(t2), 'non-runaway', len(nr), 'right', sum(r['score'] >= 1 for r in nr), 'over', sum((num(r['pred']) or 0) > 2 for r in nr))
allr = {r['id']: r for s in ('dev-S1', 'R0-dev') for r in K.direct('R1', 200, s, types=['object_counting'])}
for i in ('vsi590k_051401', '20cf95a49d0dc9160aac5589', '1537072c276dc19107c31895'):
    r = allr[i]; print('---', i, '| gt', r['gt'], 'pred', r['pred'], '|', r['question'][:110]); print('   ', (r['text'] or '')[:330].replace('\n', ' / '))
