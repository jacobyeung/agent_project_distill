import sys, re, collections
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
rows = K.vsti('R1', 200)
bt = collections.defaultdict(list)
for r in rows: bt[r['type']].append(r)
def letter(s):
    m = re.match(r'\s*([A-D])\b', str(s or '')); return m.group(1) if m else None
for t, rs in sorted(bt.items()):
    n = len(rs); wrong = sum(1 for r in rs if not r['score'])
    last = sum(1 for r in rs if letter(r['pred']) == chr(64 + len(r['options'])))
    lastgt = sum(1 for r in rs if letter(r['gt']) == chr(64 + len(r['options'])))
    # polarity word chosen
    pw = collections.Counter(); gw = collections.Counter()
    for r in rs:
        om = {letter(o): o.split('.', 1)[1].strip() for o in r['options']}
        pw[om.get(letter(r['pred']))] += 1; gw[om.get(letter(r['gt']))] += 1
    print(t, 'n', n, 'wrong', wrong, 'last_pred', last, 'last_gt', lastgt, 'nopt', collections.Counter(len(r['options']) for r in rs))
    if len(pw) <= 4: print('   pred words', dict(pw), 'truth words', dict(gw))
# Locate lines cite k?
def kof(q):
    m = re.search(r'frame\s+(\d+)', q); return int(m.group(1)) if m else None
nok = 0; wr = 0
for r in rows:
    if r['score']: continue
    wr += 1
    k = kof(r['question']); th = (r['text'] or '').split('</think>')[0]
    loc = [l for l in th.splitlines() if re.search(r'(?i)locate|first seen|seen in frame', l)]
    cited = set(int(x) for l in loc for x in re.findall(r'frame\s+(\d+)', l))
    if k not in cited: nok += 1
print('wrong', wr, 'wrong with no Locate line citing k', nok)
r = rows[0]; print(r['id'], r['question'][:300]); print(r['text'][:600])
