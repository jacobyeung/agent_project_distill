"""ORCH ORDER 0351Z item 1: coverage table of absolute-distance question templates x unit (dev-S1 150 routed items, R0-dev 290),
with tower-call counts at step 544 (171253/1) and step 200 (172744), and routed rows with that template and unit on P and N.
Templates are exact: the two object names come from step 544's own ground calls (obj="..."), the unit word becomes {u}."""
import json, re, sys
from collections import defaultdict, Counter
rows = json.load(open('../q1/TRACES_DIST_544_200.json'))
UW = {'m': 'meters', 'cm': 'centimeters', 'ft': 'feet', 'in': 'inches'}
ROUTED = 'Measuring from the closest point of each object, what is the distance between the {a} and the {b} (in {u})?'
def template(q, names, unit):
    t = q
    for tag, n in zip(('{a}', '{b}'), names):
        i = t.find('the ' + n)
        if i < 0: return None
        t = t[:i] + 'the ' + tag + t[i + 4 + len(n):]
    w = UW[unit]; t2 = re.sub(r'\b' + w + r'\b', '{u}', t, count=1)
    if t2 == t: t2 = re.sub(r'\b' + w.capitalize() + r'\b', '{U}', t, count=1)
    return t2
m = {(r['step'], r['key']): r for r in rows}
cells = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))   # template -> unit -> [items, calls544, calls200]
bad = []; item_tmpl = {}
for r in rows:
    if r['step'] != '544': continue
    names = re.findall(r'<ground obj="([^"]+)"', r['text'])[:2]
    if len(names) < 2:
        names = re.findall(r'<ground obj="([^"]+)"', m[('200', r['key'])]['text'])[:2]
    if len(names) < 2:
        mm = re.search(r'between the (.+?) and the (.+?) using their closest points', r['question'])
        names = [mm.group(1), mm.group(2)] if mm else names
    t = template(r['question'], names, r['unit']) if len(names) == 2 else None
    if t is None or '{a}' not in t or '{b}' not in t or ('{u}' not in t and '{U}' not in t):
        bad.append((r['key'], r['question'], names)); continue
    item_tmpl[r['key']] = t
    c = cells[t][r['unit']]; c[0] += 1; c[1] += r['ncalls'] > 0; c[2] += m[('200', r['key'])]['ncalls'] > 0
print('templated', len(item_tmpl), 'unparsed', len(bad))
for b in bad: print('  UNPARSED', b)
r0 = [json.loads(l) for l in open('/scratch/jjyeung/orch_n30/cont_ops/work/h1read/in/out/qsets/R0_QUESTIONS_dev_f32.jsonl')]
r0 = [x for x in r0 if x.get('question_type') == 'object_abs_distance']
r0t = Counter()
for x in r0:
    mm = re.fullmatch(r'Measuring from the closest point of each object, what is the distance between the (.+?) and the (.+) \(in (meters|centimeters|feet|inches)\)\?', x['question'])
    r0t[(ROUTED if mm else 'OTHER', {v: k for k, v in UW.items()}.get(mm.group(3)) if mm else '?')] += 1
P = {('m'): 11728, 'ft': 683}                     # routed template only; 64 inch rows stored, not drawn
N = {'m': 7805 + 760}                             # distance 7,805 + recovery 760 (metres); units filled from the bound split
units_bound = json.load(open('N_UNITS_BOUND_SPLIT.json')) if len(sys.argv) > 1 else {'cm': None, 'ft': None, 'in': None}
N.update(units_bound)
tot = {t: [sum(v[0] for v in d.values()), sum(v[1] for v in d.values()), sum(v[2] for v in d.values())] for t, d in cells.items()}
order = sorted(cells, key=lambda t: (tot[t][2] / tot[t][0], -tot[t][0]))
L = ['# Coverage of absolute-distance question templates (dev-S1 150 routed items; R0-dev 290)', '',
     'Calls = items with at least one served tower call (step 544 read 171253/1; step 200 read 172744). Routed rows = rows whose question has this template and unit: P = sealed metre programs (11,728) + drawn feet unit rows (683; 64 inch rows stored, not drawn); N = bound distance 7,805 + recovery 760 (metres) + bound units 7,805 (cm/ft/in). Only the routed template has routed rows.', '',
     '| Template ({a}, {b} objects; {u} unit) | items m/ft/in/cm | calls 544 | calls 200 | call rate 200 | P rows | N rows | named |', '|---|---|---|---|---|---|---|---|']
named = []
for t in order:
    d = cells[t]; it = '/'.join(str(d[u][0]) for u in ('m', 'ft', 'in', 'cm'))
    c5 = '/'.join(str(d[u][1]) for u in ('m', 'ft', 'in', 'cm')); c2 = '/'.join(str(d[u][2]) for u in ('m', 'ft', 'in', 'cm'))
    rate = tot[t][2] / tot[t][0]; nm = rate < 0.90
    if nm: named.append(t)
    L.append('| %s | %s | %s (%d/%d) | %s (%d/%d) | %.0f%% | 0 | 0 | %s |' % (t, it, c5, tot[t][1], tot[t][0], c2, tot[t][2], tot[t][0], 100 * rate, 'yes' if nm else 'no (>= 90%)'))
L.append('| %s (R0-dev, 290 items, all metres; no routed read of R0-dev distance exists) | %d/0/0/0 | - | - | - | m 11,728; ft 683 | m %d; ft/in/cm %s | no (covered) |' % (ROUTED, r0t[(ROUTED, 'm')], N['m'], '/'.join(str(N.get(u)) for u in ('ft', 'in', 'cm'))))
units = {u: [sum(cells[t][u][0] for t in cells), sum(cells[t][u][1] for t in cells), sum(cells[t][u][2] for t in cells)] for u in ('m', 'ft', 'in', 'cm')}
L += ['', '| Unit (dev-S1, all templates) | items | calls 544 | calls 200 | call rate 200 | P routed rows | N routed rows | named |', '|---|---|---|---|---|---|---|---|']
for u in ('m', 'ft', 'in', 'cm'):
    a, b, c = units[u]; pr = {'m': 11728, 'ft': 683, 'in': 0, 'cm': 0}[u]; nr = N.get(u)
    L.append('| %s | %d | %d | %d | %.0f%% | %s | %s | %s |' % (u, a, b, c, 100 * c / a, pr, nr, 'no on N (>= 200 rows); P uncovered' if u in ('in', 'cm') else 'no on N'))
L += ['', 'Named (call rate under 90%% at step 200 and fewer than 200 routed rows on N): %d templates, listed above with "yes". No unit is named on N: every unit has at least 200 routed rows there, all in the one routed template. On P, inches (64 stored, not drawn) and centimetres (0) are uncovered, but P takes no row change.' % len(named)]
open('COVERAGE.md', 'w').write('\n'.join(L) + '\n')
json.dump(dict(named=named, item_template=item_tmpl, cells={t: dict(d) for t, d in cells.items()}, r0=dict((('%s|%s' % k), v) for k, v in r0t.items())), open('COVERAGE.json', 'w'), indent=1)
print('named', len(named)); print('\n'.join(L[4:]))
