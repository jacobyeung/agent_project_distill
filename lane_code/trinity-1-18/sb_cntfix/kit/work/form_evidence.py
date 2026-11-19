"""Lane sb_countdesign: two trace-form facts on the 93 large items. (1) At step 544 (count-first after a visibility list) does the announced
count follow the length of the frame list or the truth? (2) Items where R1 step 100 wrote the generic no-inventory form: its score against
the other checkpoints on the same items. CPU, read-only."""
import sys, json, collections, statistics
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_count/work'); import cnt
sys.path.insert(0, '../files'); import score_count_pricing as S
out = {}
rows = {}
for s in ('dev-S1', 'R0-dev'):
    for run, step in cnt.CK:
        for r in cnt.load(run, step, s): rows.setdefault(r['id'], {})['%s_%d' % (run, step)] = r
big = {i: d for i, d in rows.items() if float(d['R1_200']['gt']) >= 5}
print('large items', len(big))
# (1) step 544
v = [(d['S1_544']['P']['vis'], d['S1_544']['P']['inst'], float(d['S1_544']['gt']), d['S1_544']) for d in big.values() if d['S1_544']['P']['form'] == 'F544' and d['S1_544']['P']['vis'] and d['S1_544']['P']['inst']]
print('step 544 large items with a parsed visibility list and announced count:', len(v), 'forms', collections.Counter(d['S1_544']['P']['form'] for d in big.values()))
if len(v) >= 5:
    r1 = S.spearman([a for a, b, c, _ in v], [b for a, b, c, _ in v]); r2 = S.spearman([b for a, b, c, _ in v], [c for a, b, c, _ in v]); r3 = S.spearman([a for a, b, c, _ in v], [c for a, b, c, _ in v])
    print('  rank correlation: announced count with frames listed %.2f; announced count with truth %.2f; frames listed with truth %.2f' % (r1, r2, r3))
    print('  frames listed: median %d, above 32 on %d of %d; announced count median %d' % (statistics.median(a for a, b, c, _ in v), sum(a > 32 for a, b, c, _ in v), len(v), statistics.median(b for a, b, c, _ in v)))
    out['step544'] = dict(n=len(v), rho_count_frames=r1, rho_count_truth=r2, rho_frames_truth=r3)
pc = collections.Counter(str(d['S1_544']['pred']) for d in big.values()); print('  step 544 answers on the 93 items, most common:', pc.most_common(8))
def num(p):
    try: return float(p)
    except Exception: return None
a544 = [num(d['S1_544']['pred']) for d in big.values()]; t = [float(d['S1_544']['gt']) for d in big.values()]
print('  step 544: rank correlation of the answer with the truth on the 93 items: %.2f' % S.spearman([x if x is not None else 0 for x in a544], t))
a200 = [(num(d['R1_200']['pred']), float(d['R1_200']['gt'])) for d in big.values() if not d['R1_200']['forced_close'] and num(d['R1_200']['pred']) is not None]
print('  step 200 (not runaway, n %d): rank correlation %.2f' % (len(a200), S.spearman([x for x, _ in a200], [y for _, y in a200])))
# (2) generic form at step 100
gen = [d for d in big.values() if d['R1_100']['P']['form'] == 'GEN']
print('step 100 generic-form large items:', len(gen), 'runaway at step 100:', sum(d['R1_100']['forced_close'] for d in gen))
for k in ('S1_544', 'R1_100', 'R1_200'): print('   %s %.1f' % (k, 100 * statistics.mean(d[k]['score'] for d in gen)))
ag = [(num(d['R1_100']['pred']), float(d['R1_100']['gt'])) for d in gen if num(d['R1_100']['pred']) is not None]
print('   generic answers: rank correlation with truth %.2f; median answer/truth %.2f; constant 6 on these items %.1f' % (S.spearman([x for x, _ in ag], [y for _, y in ag]), statistics.median(x / y for x, y in ag), 100 * statistics.mean(S.mra(6, y) for _, y in ag)))
print('   examples (truth, answer):', sorted((int(y), int(x)) for x, y in ag))
oth = [d for d in big.values() if d['R1_100']['P']['form'] != 'GEN']
print('step 100 other-form large items:', len(oth), ' '.join('%s %.1f' % (k, 100 * statistics.mean(d[k]['score'] for d in oth)) for k in ('S1_544', 'R1_100', 'R1_200')))
out['generic'] = dict(n=len(gen), scores={k: 100 * statistics.mean(d[k]['score'] for d in gen) for k in ('S1_544', 'R1_100', 'R1_200')})
json.dump(out, open('FORM_EVIDENCE.json', 'w'), indent=1)
