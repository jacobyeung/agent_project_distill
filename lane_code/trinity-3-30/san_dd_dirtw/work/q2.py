"""Q2: do wrong answers match a role exchange more often than chance?  Chance = uniform over wrong options, and = the model's own answer marginals."""
import csv, collections, math, sys
R = list(csv.DictReader(open('/scratch/jjyeung/orch_n30/san_dd_dirtw/work/tw_items.tsv'), delimiter='\t'))
def binom_p(k, n, p):  # P(X >= k)
    return sum((math.factorial(n) // (math.factorial(i) * math.factorial(n - i))) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))
flip = {'left': 'right', 'right': 'left'}
def ft(lv, t):  # faced<->target exchange: theta -> -theta
    if lv == 'hard': f, s = t.split('-'); return {f + '-' + flip[s]}
    return {flip.get(t, t)}
def of(lv, t):  # observer<->faced (same set for observer<->target): side flips; back -> front; front -> front or back
    if lv == 'easy': return {flip[t]}
    if lv == 'medium': return {'left', 'right'} if t == 'back' else {flip[t], 'back'}
    f, s = t.split('-'); s2 = flip[s]
    return {'front-' + s2} if f == 'back' else {'front-' + s2, 'back-' + s2}
for lv in ('medium', 'hard'):
    Y = [x for x in R if x['lv'] == lv]; W = [x for x in Y if x['s200'] == '0.0']
    marg = collections.Counter(x['a200'] for x in Y)
    for name, fn in (('faced<->target', ft), ('observer<->faced or observer<->target', of)):
        for grp, sel in (('all', lambda x: True), ('truth back', lambda x: 'back' in x['truth']), ('truth not back', lambda x: 'back' not in x['truth'])):
            Z = [x for x in W if sel(x)]
            if not Z: continue
            k = sum(x['a200'] in fn(lv, x['truth']) for x in Z)
            eu = sum(len(fn(lv, x['truth']) - {x['truth']}) / (len(marg) - 1) for x in Z)
            em = sum(sum(marg[o] for o in fn(lv, x['truth']) if o != x['truth']) / sum(v for o, v in marg.items() if o != x['truth']) for x in Z)
            print('%-6s %-38s %-15s match %2d of %2d | uniform chance %.1f (p=%.3f) | model-marginal chance %.1f' % (lv, name, grp, k, len(Z), eu, binom_p(k, len(Z), eu / len(Z)), em))
    print('   %s answer marginals at 200: %s' % (lv, dict(marg)))
