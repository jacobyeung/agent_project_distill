"""Labelling pilot, part 3: score a labeller's dev-S1 answers beside the student's (step 200, scored arm) on the same items.
usage: /usr/bin/python3 score_devs1.py TAG [TAG ...]     (results/TAG/<clip>.json from label_codex.py or label.py; truth in key_devs1.json)
Choice types: option-letter accuracy. Numeric types: mean relative accuracy (thresholds 0.50 to 0.95), as the student is scored.
Writes results/DEVS1_HEADROOM_<TAG>.json and prints one table per tag."""
import sys, json, glob, os, collections, re
P = '/scratch/jjyeung/orch_n30/swarm_an/work/pilot/'
key = json.load(open(P + 'key_devs1.json'))
def num(x):
    m = re.search(r'-?\d+(?:\.\d+)?', str(x)); return float(m.group(0)) if m else None
def mra(p, g):
    if p is None or g is None or g == 0: return 0.0
    e = abs(p - g) / abs(g); return sum(e <= 1 - t + 1e-9 for t in [0.5 + 0.05 * i for i in range(10)]) / 10.0
for tag in sys.argv[1:]:
    t = collections.defaultdict(lambda: [0, 0.0, 0.0, 0]); clips = 0; sec = 0.0; rows = []
    for f in sorted(glob.glob(P + 'results/' + tag + '/*.json')):
        d = json.load(open(f)); ans = d.get('answers')
        if not isinstance(ans, dict) or 'error' in ans: print('  no answers:', d['clip']); continue
        clips += 1; sec += d.get('seconds') or 0
        for kq, k in key.items():
            clip, qid = kq.split('/')
            if clip != d['clip']: continue
            a = ans.get(qid); x = t[k['type']]; x[0] += 1; x[2] += k['student_score'] or 0.0
            if a is None: x[3] += 1; s = 0.0
            elif k['options']: s = float(str(a).strip()[:1].upper() == str(k['gt']).strip()[:1].upper())
            else: s = mra(num(a), num(k['gt']))
            x[1] += s; rows.append(dict(id=k['id'], type=k['type'], clip=clip, gt=k['gt'], labeller=a, labeller_score=s, student=k['student_pred'], student_score=k['student_score']))
    print('== %s: %d clips, %d questions, %.0f wall seconds (%.0f per 1,000 answers), %.1f dispatches per 1,000 answers' % (
        tag, clips, len(rows), sec, 1000.0 * sec / max(1, len(rows)), 1000.0 * clips / max(1, len(rows))))
    print('  %-30s %4s %9s %9s %7s %s' % ('type', 'n', 'labeller', 'student', 'diff', 'unanswered'))
    tot = [0, 0.0, 0.0]
    for ty in sorted(t):
        n, a, s, u = t[ty]; tot[0] += n; tot[1] += a; tot[2] += s
        print('  %-30s %4d %9.1f %9.1f %+7.1f %d' % (ty, n, 100 * a / n, 100 * s / n, 100 * (a - s) / n, u))
    if tot[0]: print('  %-30s %4d %9.1f %9.1f %+7.1f' % ('all (item-weighted)', tot[0], 100 * tot[1] / tot[0], 100 * tot[2] / tot[0], 100 * (tot[1] - tot[2]) / tot[0]))
    both = collections.Counter((r['labeller_score'] >= 1, (r['student_score'] or 0) >= 1) for r in rows)
    print('  labeller right, student wrong: %d | labeller wrong, student right: %d | both right: %d | both wrong: %d' % (both[(True, False)], both[(False, True)], both[(True, True)], both[(False, False)]))
    json.dump(dict(tag=tag, clips=clips, seconds=sec, by_type=dict((ty, dict(n=v[0], labeller=100 * v[1] / v[0], student=100 * v[2] / v[0], unanswered=v[3])) for ty, v in t.items()), rows=rows),
              open(P + 'results/DEVS1_HEADROOM_%s.json' % tag, 'w'), indent=0)
