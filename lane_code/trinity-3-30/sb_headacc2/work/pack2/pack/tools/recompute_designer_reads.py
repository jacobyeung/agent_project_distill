"""Recompute the head-accuracy record's gap and camera reads from the staged per-item records alone (no other input).
Usage: python3 recompute_designer_reads.py <pack dir>   (the folder that holds ROUTED_FULL_*_devS1_*.jsonl.gz and ROUTED_544_devS1.jsonl.gz)
Ports work/gapdiag.py and work/camdiag.py of lane sb_headacc; same rules, inputs read from the pack."""
import sys, json, re, gzip, statistics as st
P = sys.argv[1].rstrip('/') + '/'
fac = {'m': 1.0, 'cm': 100.0, 'ft': 1 / .3048, 'in': 1 / .0254}
def unit(q):
    q = q.lower()
    if re.search(r'centimet|\bcm\b', q): return 'cm'
    if re.search(r'\bfeet\b|\bfoot\b|\bft\b', q): return 'ft'
    if re.search(r'\binch', q): return 'in'
    return 'm'
def mra(p, g):
    if g == 0: return 0.0
    e = abs(p - g) / abs(g); return sum(e <= 1 - t / 100 + 1e-12 for t in range(50, 100, 5)) / 10
def jl(name): return [json.loads(l) for l in gzip.open(P + name)]
def gaps(step):
    out = []
    for rec in jl('ROUTED_FULL_%d_devS1_distance.jsonl.gz' % step):
        recs = rec['output']['calls']['records']
        g = [r for r in recs if r.get('family') == 'ground' and r.get('stage1')]
        gp = [re.search(r'distance ([\d.]+) m', r.get('response') or '') for r in recs if r.get('family') == 'gap']
        gp = [float(x.group(1)) for x in gp if x]
        if not gp: continue
        truth = float(rec['answer']) / fac[unit(rec['question'])]
        objs = {}
        for r in g:
            s = r['stage1']; resp = r.get('response') or ''
            m = re.search(r'frames ([\d,]+) \(best (\d+)\)', resp); z = re.search(r'size ([\d.]+) x ([\d.]+) x ([\d.]+) m', resp)
            if not m or not z: continue
            c = s['candidates']; lg = sorted([x['logit'] for x in c if x.get('logit') is not None], reverse=True)
            objs[s['name_key']] = dict(nfr=len(m.group(1).split(',')), size=sorted(map(float, z.groups()), reverse=True), ncand=s['linked_candidates'],
                                       margin=(lg[0] - lg[1]) if len(lg) > 1 else None, sam_frames=sum(1 for n in s['sam3']['kept_per_frame'] if n > 0))
        if len(objs) < 2: continue
        out.append(dict(truth=truth, gap=gp[-1], s=mra(gp[-1], truth), ratio=gp[-1] / truth, objs=objs))
    return out
def tab(rows, key, label):
    b = {}
    for r in rows: b.setdefault(key(r), []).append(r)
    print(' --', label)
    for k in sorted(b, key=str):
        v = b[k]; print('    %-14s n=%3d gapMRA=%5.1f overestimated=%d' % (k, len(v), 100 * sum(x['s'] for x in v) / len(v), sum(x['ratio'] > 1 for x in v)))
for step in (544, 200):
    R = gaps(step); print('== step', step, 'gaps with two boxed objects', len(R), 'gap MRA %.1f' % (100 * sum(r['s'] for r in R) / len(R)))
    mn = lambda r, f: min(o[f] for o in r['objs'].values())
    tab(R, lambda r: ('1' if mn(r, 'nfr') == 1 else '2' if mn(r, 'nfr') == 2 else '3-4' if mn(r, 'nfr') <= 4 else '5+'), 'minimum grounded frames of the two objects')
    tab(R, lambda r: 'under 3' if mn(r, 'nfr') < 3 else '3 or more', 'minimum grounded frames, two bands')
    def amb(r):
        ms = [o['margin'] for o in r['objs'].values() if o['margin'] is not None]
        return 'no rival' if not ms else ('margin<1' if min(ms) < 1 else 'margin>=1')
    tab(R, amb, 'selector logit margin, minimum over the two objects (no rival counted with margin>=1 in the record)')
    tab(R, lambda r: ('<1m' if r['truth'] < 1 else '1-2m' if r['truth'] < 2 else '2-4m' if r['truth'] < 4 else '4m+'), 'truth band')
    O2 = [o for r in R for o in r['objs'].values()]
    print('    operands', len(O2), '| median frames of the chosen candidate', st.median(o['nfr'] for o in O2), '| median frames with any SAM 3 proposal', st.median(o['sam_frames'] for o in O2),
          '| chosen candidates with one frame', sum(o['nfr'] == 1 for o in O2))
    print('    operands with 1 linked candidate: %d; 2-3: %d; 4+: %d' % (sum(o['ncand'] == 1 for o in O2), sum(1 < o['ncand'] <= 3 for o in O2), sum(o['ncand'] > 3 for o in O2)))
    print('    share of boxes with longest edge under 0.3 m: %.2f' % (sum(o['size'][0] < .3 for o in O2) / len(O2)))
R = [r for r in jl('ROUTED_544_devS1.jsonl.gz') if r['type'] in ('camera_displacement', 'camera_rotation')]
for t in ('camera_displacement', 'camera_rotation'):
    rows = []
    for r in R:
        if r['type'] != t or not r['calls']: continue
        c = r['calls'][-1]; m = re.search(r'from=(\d+) to=(\d+)', c['call'] or '')
        try: g = float(r['gt']); a = float(r['answer'])
        except Exception: continue
        if not m: continue
        rows.append(dict(i=int(m.group(1)), j=int(m.group(2)), g=g, a=a, s=r['score']))
    tot = sum(1 - x['s'] for x in rows)
    print('== step 544', t, len(rows), 'score %.1f' % (100 * sum(x['s'] for x in rows) / len(rows)), '| median abs error %.3f' % st.median(abs(x['a'] - x['g']) for x in rows))
    def tabc(key, label):
        b = {}
        for x in rows: b.setdefault(key(x), []).append(x)
        print(' --', label)
        for k in sorted(b):
            v = b[k]; print('    %-10s n=%3d score=%5.1f median abs error=%.3f share of lost points=%.2f' % (k, len(v), 100 * sum(x['s'] for x in v) / len(v), st.median(abs(x['a'] - x['g']) for x in v), sum(1 - x['s'] for x in v) / tot))
    tabc(lambda x: 'gap 1' if abs(x['j'] - x['i']) <= 1 else 'gap 2-3' if abs(x['j'] - x['i']) <= 3 else 'gap 4+', 'frame gap')
    if t == 'camera_displacement':
        tabc(lambda x: 'a<=0.25' if x['g'] <= .25 else 'b<=0.5' if x['g'] <= .5 else 'c<=1' if x['g'] <= 1 else 'd<=2' if x['g'] <= 2 else 'e>2', 'truth band (m)')
    else:
        tabc(lambda x: 'a<5' if abs(x['g']) < 5 else 'b<10' if abs(x['g']) < 10 else 'c<20' if abs(x['g']) < 20 else 'd<45' if abs(x['g']) < 45 else 'e>=45', 'absolute truth band (deg)')
