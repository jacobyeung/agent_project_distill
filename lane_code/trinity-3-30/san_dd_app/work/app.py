"""Parse R0-dev obj_appearance_order traces (read in place through san_kit). Lane san_dd_app."""
import re, sys
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
T = ['obj_appearance_order']
S1 = re.compile(r'Step 1:[^:]*:\s*(.*?)\s*(?:\n|$)')
S2 = re.compile(r'Step 2:[^:]*:\s*(.*?)\s*(?:\n|</think>|$)')
def norm(s): return re.sub(r'\s+', ' ', s.strip().strip('.').strip().lower())
def qobjs(q):
    m = re.search(r':\s*(.*?)\?\s*$', q.strip()); return [norm(x) for x in m.group(1).split(',')] if m else None
def opts(options):
    out = {}
    for o in options:
        m = re.match(r'\s*([A-Z])\.\s*(.*)$', o); out[m.group(1)] = [norm(x) for x in m.group(2).split(',')]
    return out
def think(t):
    return t.split('</think>')[0] if t and '</think>' in t else (t or '')
def frames(t):
    m = S1.search(think(t))
    if not m: return None, []
    d = {}; bad = []
    for e in m.group(1).split(';'):
        e = norm(e)
        if not e: continue
        x = re.match(r'^(.*?)\s+frames?\s+(\d+(?:\.\d+)?)$', e)
        if x: d[x.group(1)] = float(x.group(2))
        else: bad.append(e)
    return d, bad
def written(t):
    m = S2.search(think(t)); return [norm(x) for x in m.group(1).split(',')] if m else None
def match_opt(order, op):
    for k, v in op.items():
        if order == v: return k
    return None
def sort_by(fr, objs):
    if fr is None or any(o not in fr for o in objs): return None
    return sorted(objs, key=lambda o: (fr[o], objs.index(o)))
def pairs_ok(order, truth):
    """number of object pairs that `order` puts in the truth's relative order"""
    pos = {o: i for i, o in enumerate(order)}; n = 0; tot = 0
    for i in range(len(truth)):
        for j in range(i + 1, len(truth)):
            a, b = truth[i], truth[j]
            if a in pos and b in pos:
                tot += 1; n += pos[a] < pos[b]
    return n, tot
def parse(r):
    op = opts(r['options']); q = qobjs(r['question']); fr, bad = frames(r['text']); w = written(r['text'])
    truth = op.get(r['gt']); fo = sort_by(fr, q) if (fr and q) else None
    ties = 0
    if fr and q and all(o in fr for o in q):
        v = [fr[o] for o in q]; ties = len(v) - len(set(v))
    return dict(id=r['id'], q=q, op=op, gt=r['gt'], pred=r['pred'], score=r['score'], truth=truth, fr=fr, bad=bad, w=w,
                fo=fo, fo_opt=match_opt(fo, op) if fo else None, w_opt=match_opt(w, op) if w else None, ties=ties,
                ans=(r['text'] or '').split('</think>')[-1].strip()[:20], text=r['text'], room=r['room'])
def load(run, step):
    return {r['id']: parse(r) for r in K.direct(run, step, 'R0-dev', types=T)}
def all3():
    return load('S1', 544), load('R1', 100), load('R1', 200)
