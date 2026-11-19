# Prints the five numbers the san_dd_vsticam report rests on. Read-only; scratch files only under /tmp/san_dd_vsticam.
# Run: /usr/bin/python3 /scratch/jjyeung/orch_n30/san_dd_vsticam/work/reproduce.py   (number 5 runs in a child process of
# /scratch/jjyeung/envs/planner_local_v1/bin/python, because san_kit.routed needs Python 3.8+ and that env's sqlite3 is broken; the parent waits)
import os, sys, io, json, re, math, sqlite3, statistics, runpy, contextlib, itertools
from collections import defaultdict, Counter
W = '/scratch/jjyeung/orch_n30/san_dd_vsticam/work'; T = '/tmp/san_dd_vsticam'
os.makedirs(T, exist_ok=True); sys.path.insert(0, W)
DB = 'file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro'
FAMS = json.load(open('/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json'))['families']
def fetch(fam):
    db = sqlite3.connect(DB, uri=True); ids = [i for a, b in FAMS[fam] for i in range(a, b + 1)]
    for s in range(0, len(ids), 200):
        for i, row in db.execute('select i,row from rows where i in (%s)' % ','.join(map(str, ids[s:s + 200]))):
            yield i, json.loads(row)
def quiet(path):
    with contextlib.redirect_stdout(io.StringIO()): runpy.run_path(path, run_name='__main__')
if not os.path.isfile(T + '/dev.json'): quiet(W + '/parse_dev.py')
if not os.path.isfile(T + '/rows_cam_nf.json'):
    out = {}
    for fam in ('camera_obj_rel_dist_v1', 'camera_obj_rel_dist_v2', 'camera_obj_rel_dist_v3', 'obj_obj_relative_pos_nf'):
        out[fam] = []
        for i, d in fetch(fam):
            p = d['provenance']
            out[fam].append(dict(i=i, qid=d['qid'], qt=d['question_type'], pool=d['pool'], retrace=d.get('retrace'), scene=d['scene'],
                canonical=p.get('canonical'), q=d['student_input']['question'], opts=d['student_input'].get('options'), ans=d['answer'],
                k=p.get('camera_frame'), fs=p.get('first_seen'), share=p.get('frame_n_share'), gv=p.get('geometry_values'),
                inst=p.get('instances'), floor=p.get('visibility_floor'), dd=p.get('distance_definition'), target=d['target'],
                nfi=len(d['student_input'].get('frame_indices') or [])))
    json.dump(out, open(T + '/rows_cam_nf.json', 'w'))
if not os.path.isfile(T + '/size_medians.json'):
    pats = [r'longest (?:edge|side|dimension)(?: \(length, width, or height\))? of the (.+?)(?:,| in centimeters| measured|\?)',
            r'(?:length, width, and height|height, width, and length|width, length, and height)[a-z ,]*? of the (.+?),',
            r'^Measure the (.+?) along its longest', r'of the (.+?)(?:,| in centimeters| measured|\?)']
    vals = defaultdict(list)
    for i, d in fetch('object_size_estimation'):
        q = d['student_input']['question']
        try: a = float(d['answer'])
        except Exception: continue
        for p in pats:
            m = re.search(p, q)
            if m: vals[m.group(1).strip().lower()].append(a); break
    json.dump(dict(med={k: statistics.median(v) for k, v in vals.items()}, n={k: len(v) for k, v in vals.items()}), open(T + '/size_medians.json', 'w'))
quiet(W + '/q1.py')
from common import *
Q = json.load(open(T + '/q1_rules.json'))
def pick(v, n):
    w, u = v['r'][n]
    return w if n in ('last', 'first') else (w if (w is not None and u) else None)
def dl(v, order):
    for n in order:
        p = pick(v, n)
        if p is not None: return p
res = [v for k, v in Q.items() if k.endswith('|200')]
o = ('room', 'early', 'neark', 'last')
print('1. Q1: decision list %s predicts the step-200 answer on %d of %d camera-object items' % ('>'.join(o), sum(dl(v, o) == v['a'] for v in res), len(res)))
print('2. Q1/Q3: largest-object prior equals the dev truth on v1/v2/v3 %s of 150 each; model right on %s' % (
    '/'.join(str(sum(v['r']['large'][0] == v['t'] for v in res if v['type'] == t)) for t in CAM),
    '/'.join(str(int(sum(v['score'] for v in res if v['type'] == t))) for t in CAM)))
R = rows(); sc = defaultdict(list)
for f in R:
    for r in R[f]: sc[r['canonical']].append(r)
def row_prefs(r):
    ids = [(r['canonical'], x['id']) for x in r['inst']]; g = r['gv']
    return [((ids[i], ids[j]) if g[i] < g[j] else (ids[j], ids[i])) for i in range(len(ids)) for j in range(i + 1, len(ids)) if g[i] != g[j]]
ch = Counter()
for s, rs in sc.items():
    g = defaultdict(list)
    for r in rs:
        for a, b in row_prefs(r):
            key = tuple(sorted([a, b])); g[key].append((r['k'], a == key[0]))
    for key, ss in g.items():
        for x in range(len(ss)):
            for y in range(x + 1, len(ss)):
                dk = abs(ss[x][0] - ss[y][0])
                if 9 <= dk <= 16: ch['n'] += 1; ch['changed'] += ss[x][1] != ss[y][1]
print('3. Q2(b): on store-v7 rows the truly nearer object changes on %d of %d same-scene statement pairs 9-16 frames apart' % (ch['changed'], ch['n']))
fam = 'camera_obj_rel_dist_v1'; exp = 0.0
for r in R[fam]:
    ids = [(r['canonical'], x['id']) for x in r['inst']]
    prefs = [p for o2 in sc[r['canonical']] if o2['qid'] != r['qid'] and o2['k'] != r['k'] for p in row_prefs(o2)]
    w, u, n = copeland(ids, prefs)
    exp += (w == ids[0]) if w is not None else 1 / len(ids)
print('4. Q2(c): a fixed order per scene (leave one row out, siblings at other k) scores %.1f%% on the %d v1 rows' % (100 * exp / len(R[fam]), len(R[fam])))
CHILD = r"""
import sys, re, math, json
import numpy as np
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
R = json.load(open('/tmp/san_dd_vsticam/rows_cam_nf.json')); fam = 'camera_obj_rel_dist_v1'
U = {'feet': 0.3048, 'meters': 1.0, 'inches': 0.0254, 'centimeters': 0.01, None: 1.0}
gap = []
for r in K.routed(200, types=['object_abs_distance']):
    g = [c for c in r['calls'] if c['family'] == 'gap' and c['served']]
    m = re.search(r'distance ([\d.]+) m', (g[0]['response'] or '') if g else '')
    u = re.search(r'(centimeters|meters|feet|inches)', r['question']); u = u.group(1) if u else None
    if m and float(r['gt']) > 0 and float(m.group(1)) > 0: gap.append(math.log(float(m.group(1)) / (float(r['gt']) * U[u])))
rng = np.random.default_rng(7); errs = np.array(gap); hits = n = 0
for r in R[fam]:
    d = np.array(r['gv'])
    for _ in range(20):
        hits += int(np.argmin(d * np.exp(rng.choice(errs, size=len(d)))) == 0); n += 1
print("5. Q4: a routed form whose head prints each camera-object distance with the gap head's errors (%d served proxies, independent per object) would score %.1f%% on v1 rows" % (len(gap), 100 * hits / n))
"""
import subprocess
print(subprocess.run(['/scratch/jjyeung/envs/planner_local_v1/bin/python', '-c', CHILD], stdout=subprocess.PIPE, universal_newlines=True).stdout.strip())
