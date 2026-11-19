"""Reproduce the five numbers REPORT.md rests on (lane san_dd_size). Read-only; computes in memory.
Run: /usr/bin/python3 /scratch/jjyeung/orch_n30/san_dd_size/work/reproduce.py
"""
import math, os, statistics as st, sys, collections
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sddlib as L

D = L.dev(cache=False)
R = L.rows(cache=False)
base, _ = L.train_stats(R)
N = {'dev-S1': 150, 'R0-dev': 293}

def items(step_key, s):
    out = []
    for x in D['%s|%d|%s' % (step_key[0], step_key[1], s)]:
        u = L.unit(x['question']); f = L.UNIT_CM[u]; c = L.dcls(x['question']); tr = base.get(c, [])
        out.append(dict(id=x['id'], set=s, c=c, u=u, g=float(x['gt']) * f, p=float(x['pred']) * f, pred=x['pred'], score=x['score'],
                        ntr=len(tr), med=st.median(tr) if tr else None))
    return out

I = {s: items(('R1', 200), s) for s in N}

# 1. Pooled within-class log-log slope and correlation, ten largest classes per set (ties included), step 200
out1 = []
for s in N:
    cc = collections.Counter(a['c'] for a in I[s]); cut = cc.most_common(10)[-1][1]
    top = [c for c, n in cc.items() if n >= cut]; v = []
    for c in top:
        w = [a for a in I[s] if a['c'] == c]
        mg = st.mean(math.log(a['g']) for a in w); mp = st.mean(math.log(a['p']) for a in w)
        v += [(math.log(a['g']) - mg, math.log(a['p']) - mp) for a in w]
    sxy = sum(a * b for a, b in v); sxx = sum(a * a for a, b in v); syy = sum(b * b for a, b in v)
    out1.append('%s %d classes, %d items: slope %.2f, corr %.2f' % (s, len(top), len(v), sxy / sxx, sxy / (sxx * syy) ** .5))
print('1. Q1 pooled within-class log answer on log truth (step 200):', ' | '.join(out1), '[report: 0.64/0.56 dev-S1, 0.56/0.50 R0-dev]')

# 2. Truth convention: median of dev truth / v7 class median (items whose class has >= 1 base row)
out2 = []
for s in N:
    r = [a['g'] / a['med'] for a in I[s] if a['ntr'] >= 1]
    out2.append('%s %d items: %.3f' % (s, len(r), st.median(r)))
print('2. Q3 median truth / v7 class median:', ' | '.join(out2), '[report: 0.997 dev-S1 (119), 0.938 R0-dev (213)]')

# 3. R0-dev small objects (truth under 30 cm)
sm = [a for a in I['R0-dev'] if a['g'] < 30]
def grp(a):  # Table E rules, applied in order
    if a['score'] >= 0.9: return 'fine'
    if a['ntr'] >= 3 and a['med'] >= 30 and abs(math.log(a['p'] / a['med'])) < abs(math.log(a['p'] / a['g'])): return 'prior too large'
    if a['g'] < 10 and a['p'] >= 10: return 'floor'
    return 'over, no large prior' if a['p'] > a['g'] else 'under'
G = collections.defaultdict(list)
for a in sm: G[grp(a)].append(a)
print('3. Q4 R0-dev truth < 30 cm: %d items, MRA %.1f, %.2f tp (%.2f ReVSI); groups: %s [report: 88, 48.0, 15.63; fine 22, prior too large 10 (3.17), floor 5 (1.64), over 36 (8.36), under 15 (2.15)]'
      % (len(sm), 100 * st.mean(a['score'] for a in sm), 100 * sum(1 - a['score'] for a in sm) / 293, 100 * sum(1 - a['score'] for a in sm) / 293 / 7,
         ', '.join('%s %d (%.2f tp)' % (k, len(v), 100 * sum(1 - a['score'] for a in v) / 293) for k, v in sorted(G.items()))))

# 4. Units: inch answers whose implied cm is a multiple of 10; wrong-factor rescues at step 200
inch = [a for a in I['dev-S1'] if a['u'] == 'in']
rnd = [a for a in inch if abs(a['p'] - 10 * round(a['p'] / 10)) <= 0.13]; oth = [a for a in inch if a not in rnd]
two = [a for a in inch if '.' in a['pred'] and len(a['pred'].split('.')[1]) == 2]
hit = sum(abs(float(a['pred']) * 2.54 - round(float(a['pred']) * 2.54)) <= 0.0128 for a in two)
print('4. Q5 inch answers that are a round cm value converted: %d of %d, MRA %.1f against %.1f for the rest, %.2f dev-S1 tp (%.2f VSI); two-decimal inch answers equal to integer cm / 2.54: %d of %d [report: 16 of 47, 46.9 vs 69.0, 5.67; 19 of 21]'
      % (len(rnd), len(inch), 100 * st.mean(a['score'] for a in rnd), 100 * st.mean(a['score'] for a in oth), 100 * sum(1 - a['score'] for a in rnd) / 150,
         100 * sum(1 - a['score'] for a in rnd) / 150 / 8, hit, len(two)))

# 5. Bottom 100 across both sets: loss held, and the two implausible R0-dev labels
allit = I['dev-S1'] + I['R0-dev']
allit.sort(key=lambda a: (a['score'], -abs(math.log(a['p'] / a['g']))))
low = allit[:100]
lab = [a for a in I['R0-dev'] if a['id'] in ('bd27924bbd5cdff459ad0fea', 'f1e39efcfa15c404beecbb56')]
print('5. Q2/Q7 bottom 100 hold %.2f of %.2f dev-S1 tp and %.2f of %.2f R0-dev tp (%d dev-S1, %d R0-dev items); implausible labels cost %.2f R0 tp (%.2f ReVSI) [report: 16.53 of 30.60, 23.45 of 41.71; 27/73; 0.68]'
      % (100 * sum(1 - a['score'] for a in low if a['set'] == 'dev-S1') / 150, 100 * sum(1 - a['score'] for a in I['dev-S1']) / 150,
         100 * sum(1 - a['score'] for a in low if a['set'] == 'R0-dev') / 293, 100 * sum(1 - a['score'] for a in I['R0-dev']) / 293,
         sum(a['set'] == 'dev-S1' for a in low), sum(a['set'] == 'R0-dev' for a in low),
         100 * sum(1 - a['score'] for a in lab) / 293, 100 * sum(1 - a['score'] for a in lab) / 293 / 7))
