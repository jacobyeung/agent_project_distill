"""Pricing of the 115 wrong R0-dev toward items at step 200 by class; type points (denominator: all R0-dev items of the level) and ReVSI points (leaf = toward easy 126, toward hard 121; weight 1/4; /7)."""
import csv, collections
R = list(csv.DictReader(open('/scratch/jjyeung/orch_n30/san_dd_dirtw/work/tw_items.tsv'), delimiter='\t'))
TYPE_N = {'easy': 192, 'medium': 194, 'hard': 192}
LEAF_N = {'easy': sum(x['lv'] == 'easy' for x in R), 'hard': sum(x['lv'] == 'hard' for x in R)}
W = [x for x in R if x['s200'] == '0.0']
def cls(x, scheme):
    aw = x['s544'] == '0.0' and x['s100'] == '0.0'
    if scheme == 'geo': return x['geo']
    return ('always-wrong ' if aw else 'e_unstable ') + (x['geo'] if aw else '')
def price(items):
    tp = {lv: 100 * sum(1 for x in items if x['lv'] == lv) / TYPE_N[lv] for lv in TYPE_N}
    rv = sum(100 * sum(1 for x in items if x['lv'] == lv) / LEAF_N[lv] / 4 / 7 for lv in LEAF_N)
    return tp, rv
for scheme in ('geo', 'stab'):
    print('== scheme', scheme)
    g = collections.defaultdict(list)
    for x in W: g[cls(x, scheme)].append(x)
    for k in sorted(g):
        tp, rv = price(g[k]); n = collections.Counter(x['lv'] for x in g[k])
        print('  %-28s n=%3d (e %2d, m %2d, h %2d) | type points e %.1f m %.1f h %.1f | ReVSI %.2f' % (k, len(g[k]), n['easy'], n['medium'], n['hard'], tp['easy'], tp['medium'], tp['hard'], rv))
    tp, rv = price(W); print('  %-28s n=%3d | type points e %.1f m %.1f h %.1f | ReVSI %.2f' % ('all 115', len(W), tp['easy'], tp['medium'], tp['hard'], rv))
AW = [x for x in W if x['s544'] == '0.0' and x['s100'] == '0.0']; tp, rv = price(AW)
print('always-wrong 69: ReVSI %.2f, type points e %.1f m %.1f h %.1f' % (rv, tp['easy'], tp['medium'], tp['hard']))
