"""Markdown tables for the record: pooled rule (item weights, registered) against the card's dev-S1 rule, same pseudo-reads."""
import json, sys
ARMS = [a for a in ('D0m200', 'H1m100', 'D0m100') if __import__('os').path.exists('POOLED_POWER_%s.json' % a)]
D = {a: json.load(open('POOLED_POWER_%s.json' % a))['results'] for a in ARMS}


def cell(x, key='stop'):
    if x is None:
        return 'n/a'
    v = x[key] if isinstance(x, dict) else x
    return '%.3f ± %.3f' % (v[0], v[1])


def get(arm, rule, look, k):
    r = D[arm][rule][look]
    if rule == 'devS1_rule':
        alias = {'b: loss 9.5 on object_size (flips)': None,
                 'b: loss 9.5 on route_planning(dev-S1 only) (flips)': 'b: loss 9.5 on route_planning (flips)'}
        if k in alias:
            k = alias[k]
        if k is None:
            return None
        if k.startswith('dilution') and 'dev-S1 only' in k:
            t = k.split(' on ')[1].split(',')[0]
            k = 'a: size loss dev-S1 9.5 + R0-dev 4.3 (flips)' if t == 'object_size' else 'b: loss 9.5 on %s (flips)' % t
        elif k.startswith('dilution'):
            k = 'dilution: any loss on R0-dev only'
    return r.get(k)


ROWS = [
    ('Unchanged model, arms exchanged per room', 'no change (exchange)'),
    ('Unchanged model, D0 noise centred', 'no change (centred, D0 noise)'),
    ('(a) size: dev-S1 -9.5 and R0-dev -4.3, item flips', 'a: size loss dev-S1 9.5 + R0-dev 4.3 (flips)'),
    ('(a) the same, exchange null shifted', 'a: size loss dev-S1 9.5 + R0-dev 4.3 (shift on exchange)'),
    ('(a) the same, D0 noise shifted', 'a: size loss dev-S1 9.5 + R0-dev 4.3 (shift on centred, D0 noise)'),
    ('(b) -9.5 on counting, both sets', 'b: loss 9.5 on counting (flips)'),
    ('(b) -9.5 on direction easy, both sets', 'b: loss 9.5 on direction_easy (flips)'),
    ('(b) -9.5 on direction medium, both sets', 'b: loss 9.5 on direction_medium (flips)'),
    ('(b) -9.5 on direction hard, both sets', 'b: loss 9.5 on direction_hard (flips)'),
    ('(b) -9.5 on relative distance, both sets', 'b: loss 9.5 on rel_distance (flips)'),
    ('(b) -9.5 on route planning (dev-S1 only)', 'b: loss 9.5 on route_planning(dev-S1 only) (flips)'),
    ('(b) -9.5 on appearance order (R0-dev only)', 'b: loss 9.5 on appearance_order(R0-dev only) (flips)'),
    ('(c) -2 on every type, item flips', 'c: uniform loss 2 (flips)'),
    ('(c) the same, exchange null shifted', 'c: uniform loss 2 (shift on exchange)'),
    ('-3 on every type, H2 alone', 'uniform loss 3, H2 alone (shift on exchange)'),
    ('-4 on every type, H2 alone', 'uniform loss 4, H2 alone (shift on exchange)'),
    ('Size drift -3 on both sets, size test alone', 'size drift 3 on both sets, size test alone (shift on exchange)'),
    ('Size drift -6 on both sets, size test alone', 'size drift 6 on both sets, size test alone (shift on exchange)'),
    ('Dilution: -9.5 on size, dev-S1 only', 'dilution: loss 9.5 on object_size, dev-S1 only (flips)'),
    ('Dilution: -9.5 on size, R0-dev only', 'dilution: loss 9.5 on object_size, R0-dev only (flips)'),
    ('Dilution: -9.5 on counting, dev-S1 only', 'dilution: loss 9.5 on counting, dev-S1 only (flips)'),
    ('Dilution: -9.5 on counting, R0-dev only', 'dilution: loss 9.5 on counting, R0-dev only (flips)'),
    ('Dilution: -9.5 on direction hard, dev-S1 only', 'dilution: loss 9.5 on direction_hard, dev-S1 only (flips)'),
    ('Dilution: -9.5 on direction hard, R0-dev only', 'dilution: loss 9.5 on direction_hard, R0-dev only (flips)'),
    ('Dilution: -9.5 on relative distance, dev-S1 only', 'dilution: loss 9.5 on rel_distance, dev-S1 only (flips)'),
    ('Dilution: -9.5 on relative distance, R0-dev only', 'dilution: loss 9.5 on rel_distance, R0-dev only (flips)'),
]
out = []
arm = ARMS[0]
out.append('| Scenario (noise: %s against step 544) | dev-S1 rule, step 200 | pooled rule, step 200 | dev-S1 rule, later look | pooled rule, later look |' % arm)
out.append('|---|---|---|---|---|')
for name, k in ROWS:
    out.append('| %s | %s | %s | %s | %s |' % (name, cell(get(arm, 'devS1_rule', 'step200', k)), cell(get(arm, 'pooled_item', 'step200', k)),
                                             cell(get(arm, 'devS1_rule', 'later', k)), cell(get(arm, 'pooled_item', 'later', k))))
out.append('')
out.append('| Split of the unchanged-model rate | H1 | H2 | H1 or H2 |')
out.append('|---|---|---|---|')
for rule, nm in (('devS1_rule', 'dev-S1 rule'), ('pooled_item', 'pooled rule')):
    for look in ('step200', 'later'):
        x = D[arm][rule][look]['no change (exchange)']
        out.append('| %s, %s | %s | %s | %s |' % (nm, look, cell(x, 'H1'), cell(x, 'H2'), cell(x, 'stop')))
out.append('')
out.append('| Sensitivity to the noise model (step 200 / later look) | ' + ' | '.join('%s: dev-S1 rule | %s: pooled rule' % (a, a) for a in ARMS) + ' |')
out.append('|---|' + '---|' * (2 * len(ARMS)))
for name, k in ROWS[:5] + ROWS[12:14]:
    cells = []
    for a in ARMS:
        for rule in ('devS1_rule', 'pooled_item'):
            x, y = get(a, rule, 'step200', k), get(a, rule, 'later', k)
            cells.append('%.3f / %.3f' % ((x['stop'] if isinstance(x, dict) else x)[0], (y['stop'] if isinstance(y, dict) else y)[0]))
    out.append('| %s | %s |' % (name, ' | '.join(cells)))
out.append('')
out.append('| Weights compared on %s noise, step 200 | item-proportional, rooms drawn inside each set (registered) | equal 0.5 / 0.5 | items concatenated, rooms drawn from the union |' % arm)
out.append('|---|---|---|---|')
for name, k in ROWS[:1] + ROWS[2:3] + ROWS[5:10] + ROWS[12:13] + ROWS[18:22]:
    out.append('| %s | %s | %s | %s |' % (name, cell(get(arm, 'pooled_item', 'step200', k)), cell(get(arm, 'pooled_equal', 'step200', k)), cell(get(arm, 'pooled_unstrat', 'step200', k))))
open('POOLED_TABLES.md', 'w').write('\n'.join(out) + '\n')
print('\n'.join(out))
