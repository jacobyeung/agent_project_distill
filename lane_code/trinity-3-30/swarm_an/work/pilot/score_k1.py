"""Labelling pilot, part 1: score a labeller's answers on the K1 training-capture calibration set against raster truth.
usage: /usr/bin/python3 score_k1.py TAG [TAG ...]   (results/TAG/<alias>.json from label_codex.py; truth in work/pilot_key/key_k1.json)
Visibility: accuracy, with the share of "yes" in truth and in the answers, per dataset and per pixel-share bin of the truth.
First-seen: exact, within one frame, mean absolute error; the "clean" subset has zero pixels of the class in every earlier frame.
Count: exact, mean relative accuracy (thresholds 0.50 to 0.95), by truth count, and the direction of the errors.
Writes results/K1_CALIBRATION_<TAG>.json (every question with truth and answer)."""
import sys, json, glob, collections, re
P = '/scratch/jjyeung/orch_n30/swarm_an/work/pilot/'
key = json.load(open('/scratch/jjyeung/orch_n30/swarm_an/work/pilot_key/key_k1.json'))
def num(x):
    m = re.search(r'-?\d+(?:\.\d+)?', str(x)); return float(m.group(0)) if m else None
def mra(p, g):
    if p is None or g is None or g == 0: return 0.0
    e = abs(p - g) / abs(g); return sum(e <= 1 - t + 1e-9 for t in [0.5 + 0.05 * i for i in range(10)]) / 10.0
def pct(a, b): return '%5.1f (%d/%d)' % (100.0 * a / b, a, b) if b else '   -'
for tag in sys.argv[1:]:
    rows = []; clips = 0; sec = 0.0; noans = []
    for f in sorted(glob.glob(P + 'results/' + tag + '/*.json')):
        d = json.load(open(f)); ans = d.get('answers')
        if not isinstance(ans, dict) or 'error' in ans: noans.append(d['clip']); continue
        clips += 1; sec += d.get('seconds') or 0
        for kq, k in key.items():
            clip, qid = kq.split('/')
            if clip == d['clip']: rows.append(dict(k, clip=clip, qid=qid, ans=ans.get(qid)))
    print('== %s: %d captures answered (%d without answers), %d questions, %.0f wall seconds = %.0f s and %.1f dispatches per 1,000 labels' % (
        tag, clips, len(noans), len(rows), sec, 1000.0 * sec / max(1, len(rows)), 1000.0 * clips / max(1, len(rows))))
    V = [r for r in rows if r['kind'] == 'visible']
    for r in V: r['a'] = str(r['ans']).strip().lower()[:3].rstrip('.') if r['ans'] is not None else None; r['ok'] = r['a'] == r['gt']
    def vis(name, S):
        if not S: return
        y = [r for r in S if r['gt'] == 'yes']; n = [r for r in S if r['gt'] == 'no']
        print('  %-34s acc %s | truth yes: right %s | truth no: right %s | answered yes %d of %d' % (name, pct(sum(r['ok'] for r in S), len(S)), pct(sum(r['ok'] for r in y), len(y)),
              pct(sum(r['ok'] for r in n), len(n)), sum(r['a'] == 'yes' for r in S), len(S)))
    print(' VISIBILITY (bar 90)'); vis('all', V)
    for ds in sorted(set(r['dataset'] for r in V)): vis(ds, [r for r in V if r['dataset'] == ds])
    for lo, hi in [(0.002, 0.01), (0.01, 0.05), (0.05, 2)]:
        S = [r for r in V if r['gt'] == 'yes' and lo <= r['share'] < hi]
        print('  truth yes, pixel share %.3f to %.2f : right %s' % (lo, hi, pct(sum(r['ok'] for r in S), len(S))))
    lab = collections.defaultdict(list)
    for r in V: lab[r['label']].append(r)
    worst = sorted(lab.items(), key=lambda t: (sum(r['ok'] for r in t[1]) / float(len(t[1])), -len(t[1])))
    print('  classes with 6+ questions, lowest accuracy:', ', '.join('%s %d/%d' % (l, sum(r['ok'] for r in S), len(S)) for l, S in worst if len(S) >= 6)[:330])
    F = [r for r in rows if r['kind'] == 'first']
    for r in F: r['a'] = num(r['ans']); r['d'] = None if r['a'] is None else r['a'] - r['gt']
    def fst(name, S):
        if not S: return
        A = [r for r in S if r['d'] is not None]
        print('  %-34s exact %s | within 1 %s | within 2 %s | mean abs error %.2f frames | labeller later %d, earlier %d' % (name, pct(sum(r['d'] == 0 for r in A), len(S)),
              pct(sum(abs(r['d']) <= 1 for r in A), len(S)), pct(sum(abs(r['d']) <= 2 for r in A), len(S)), sum(abs(r['d']) for r in A) / max(1, len(A)), sum(r['d'] > 0 for r in A), sum(r['d'] < 0 for r in A)))
    print(' FIRST-SEEN FRAME'); fst('all', F); fst('clean (no earlier pixels)', [r for r in F if r['clean']]); fst('not clean (earlier sliver)', [r for r in F if not r['clean']])
    for ds in sorted(set(r['dataset'] for r in F)): fst(ds, [r for r in F if r['dataset'] == ds])
    fst('truth frame 1', [r for r in F if r['gt'] == 1]); fst('truth frame 2 or later', [r for r in F if r['gt'] > 1])
    Cn = [r for r in rows if r['kind'] == 'count']
    for r in Cn: r['a'] = num(r['ans']); r['m'] = mra(r['a'], float(r['gt']))
    def cnt(name, S):
        if not S: return
        A = [r for r in S if r['a'] is not None]
        print('  %-34s exact %s | MRA %5.1f | labeller over %d, under %d | mean answer %.2f against truth %.2f' % (name, pct(sum(r['a'] == r['gt'] for r in A), len(S)), 100.0 * sum(r['m'] for r in S) / len(S),
              sum(r['a'] > r['gt'] for r in A), sum(r['a'] < r['gt'] for r in A), sum(r['a'] for r in A) / max(1, len(A)), sum(r['gt'] for r in A) / float(max(1, len(A)))))
    print(' COUNT'); cnt('all', Cn)
    for lo, hi, nm in [(1, 1, 'truth 1'), (2, 2, 'truth 2'), (3, 4, 'truth 3 to 4'), (5, 999, 'truth 5 or more')]: cnt(nm, [r for r in Cn if lo <= r['gt'] <= hi])
    for ds in sorted(set(r['dataset'] for r in Cn)): cnt(ds, [r for r in Cn if r['dataset'] == ds])
    json.dump(dict(tag=tag, captures=clips, seconds=sec, rows=rows), open(P + 'results/K1_CALIBRATION_%s.json' % tag, 'w'), indent=0)
