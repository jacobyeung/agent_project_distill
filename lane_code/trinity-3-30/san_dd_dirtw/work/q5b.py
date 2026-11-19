"""Q5b: do rooms with always-wrong toward items also fail away, relative distance and appearance order at step 200?  Seen: frame numbers vs video seconds."""
import sys, re, json, math, collections; sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_dirtw/work'); from tw_lib import *
D = load(); c = D[200]
allr = K.direct('R1', 200, 'R0-dev')
aw = collections.Counter(r['room'] for i, r in c.items() if r['subtype'] == 'toward' and r['score'] == 0 and D[544][i]['score'] == 0 and D[100][i]['score'] == 0)
SEL = (('toward', lambda r: r['type'] in T and r['subtype'] == 'toward'), ('away', lambda r: r['type'] in T and r['subtype'] == 'away'),
       ('rel. distance', lambda r: r['type'] == 'object_rel_distance'), ('appearance order', lambda r: r['type'] == 'obj_appearance_order'),
       ('counting', lambda r: r['type'] == 'object_counting'))
for name, f in (('>=2 always-wrong toward items', lambda k: aw[k] >= 2), ('1 always-wrong', lambda k: aw[k] == 1), ('0 always-wrong', lambda k: aw[k] == 0)):
    keys = {r['room'] for r in allr if f(r['room'])}; out = []
    for lab, sel in SEL:
        z = [r['score'] or 0 for r in allr if r['room'] in keys and sel(r)]; out.append('%s %.1f (%d)' % (lab, 100 * sum(z) / len(z), len(z)))
    print('rooms with %-30s %2d rooms: %s' % (name, len(keys), '; '.join(out)))
def pear(x, y):
    mx, my = sum(x) / len(x), sum(y) / len(y); sx = math.sqrt(sum((a - mx) ** 2 for a in x)); sy = math.sqrt(sum((b - my) ** 2 for b in y)); return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)
keys = sorted({r['room'] for r in allr}); per = collections.defaultdict(dict)
for k in keys:
    for lab, sel in SEL[:4]:
        z = [r['score'] or 0 for r in allr if r['room'] == k and sel(r)]
        if z: per[k][lab] = sum(z) / len(z)
for lab in ('away', 'rel. distance', 'appearance order'):
    ks = [k for k in keys if 'toward' in per[k] and lab in per[k]]
    print('per-room Pearson r, toward accuracy vs %s accuracy: %.2f over %d rooms' % (lab, pear([per[k]['toward'] for k in ks], [per[k][lab] for k in ks]), len(ks)))
TM = K.timing('R1', 200, 'R0-dev'); z = collections.Counter(); ratio = []
for i, r in c.items():
    t = r['text'] or ''
    if not t.startswith('Seen:'): continue
    fr = [int(x) for x in re.findall(r'in frame (\d+)', t.split('\n')[0])]; dur = TM[i]['total_frames'] / TM[i]['fps']
    for f in fr:
        z['<=32' if f <= 32 else ('33..video seconds' if f <= dur else '>video seconds')] += 1; ratio.append(f / dur)
print('Seen: cited numbers (R0-dev, step 200, toward and away):', dict(z), '; cited / video seconds quartiles', [round(sorted(ratio)[int(p * (len(ratio) - 1))], 2) for p in (.25, .5, .75, 1)])
