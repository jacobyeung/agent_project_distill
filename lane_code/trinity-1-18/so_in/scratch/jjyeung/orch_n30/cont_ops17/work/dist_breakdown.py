"""ORCH ASK 0312Z item 2: where the +22 pp routed distance MRA (step 544 read 171253/1 -> step 200 read 172744) comes from.
a) metre vs non-metre (107) split with room-bootstrap paired intervals; conversions right (score_r1route.unit_count);
b) tower scale (output.scale) at both steps; MRA of the last gap call's lifted distance, as is and rescaled by scale544/scale200;
c) items whose call arguments differ (call strings + grounded frames) and their MRA difference. Run from r1route/out3s."""
import sys, json, re, statistics as st
sys.argv = ['x']; sys.path.insert(0, '.')
import score_r5 as S
sc = S.scorers
a, items, _, _ = S.load(S.O.parent/'out3/A4/ret', S.O/'A', 0, 200, 'candidates_argmax')
bd, _, _, _ = S.load(S.BASE/'b1/work/ret', S.BASE/'b1', 1, 544, 'candidates_argmax')
keys = sorted(k for k, i in items.items() if i['question_type'] == S.DISTANCE and k in a and k in bd)
mra = lambda k, rows: float(sc.accuracy(rows[k]['output'], items[k])['task_accuracy'])
def mra_value(pred, gt):
    if pred is None: return 0.0
    th = [0.5 + 0.05 * i for i in range(10)]
    return sum(abs(pred - gt) / gt < 1 - t for t in th) / len(th)
def paired(ks, f, g):
    return S.bootstrap([(items[k]['room_key'], 100 * (f(k) - g(k))) for k in ks])
fmt = lambda b: '%+.2f [95%% %+.2f,%+.2f]' % (b['value'], b['ci95'][0], b['ci95'][1]) if b['n'] else 'n=0'
out = {}
metre = [k for k in keys if sc.unit_factor(items[k]['question']) == 1]; nonm = [k for k in keys if k not in metre]
for name, ks in (('all', keys), ('metre', metre), ('non_metre', nonm)):
    out[name] = dict(n=len(ks), mra544=100 * st.mean(mra(k, bd) for k in ks), mra200=100 * st.mean(mra(k, a) for k in ks),
                     paired=paired(ks, lambda k: mra(k, a), lambda k: mra(k, bd)))
ua = S.unit_count(a, items, keys)['per_item']; ub = S.unit_count(bd, items, keys)['per_item']
out['non_metre']['conversion_right'] = dict(s544=sum(map(bool, ub.values())), s200=sum(map(bool, ua.values())), of=len(nonm))
def gap(rows, k):
    vs = [sc.printed(c) for c in sc.records(rows[k]['output'])]; vs = [v for v in vs if v and v['kind'] == 'gap']
    return vs[-1]['distance'] if vs else None
sa = {k: a[k]['output'].get('scale') for k in keys}; sb = {k: bd[k]['output'].get('scale') for k in keys}
both = [k for k in keys if isinstance(sa[k], (int, float)) and isinstance(sb[k], (int, float))]
ratio = [sa[k] / sb[k] for k in both if sb[k]]
out['scale'] = dict(items_with_scale=len(both), median544=st.median(sb[k] for k in both) if both else None,
                    median200=st.median(sa[k] for k in both) if both else None, median_ratio_200_over_544=st.median(ratio) if ratio else None)
g = [k for k in keys if gap(a, k) is not None and gap(bd, k) is not None and k in both]
gt = lambda k: float(items[k]['ground_truth'])
f = lambda k: sc.unit_factor(items[k]['question'])
out['gap_value'] = dict(n=len(g),
    mra544_gap=100 * st.mean(mra_value(gap(bd, k) * f(k), gt(k)) for k in g) if g else None,
    mra200_gap=100 * st.mean(mra_value(gap(a, k) * f(k), gt(k)) for k in g) if g else None,
    mra200_gap_rescaled_to_544=100 * st.mean(mra_value(gap(a, k) * sb[k] / sa[k] * f(k), gt(k)) for k in g) if g else None,
    paired_rescale_effect=paired(g, lambda k: mra_value(gap(a, k) * f(k), gt(k)), lambda k: mra_value(gap(a, k) * sb[k] / sa[k] * f(k), gt(k))) if g else None)
def args(rows, k):
    rs = sc.records(rows[k]['output'])
    return tuple((c.get('call'), tuple(re.findall(r'frames ([0-9,]+)', c.get('response') or '')[:1])) for c in rs)
diff = [k for k in keys if args(a, k) != args(bd, k)]; same = [k for k in keys if k not in diff]
nocall = dict(s544=sum(1 for k in keys if not sc.records(bd[k]['output'])), s200=sum(1 for k in keys if not sc.records(a[k]['output'])))
out['call_args'] = dict(differ=len(diff), same=len(same), items_without_calls=nocall,
    differ_paired=paired(diff, lambda k: mra(k, a), lambda k: mra(k, bd)) if diff else None,
    same_paired=paired(same, lambda k: mra(k, a), lambda k: mra(k, bd)) if same else None)
json.dump(out, open('DIST_BREAKDOWN_m200.json', 'w'), indent=1, default=str)
for name in ('all', 'metre', 'non_metre'):
    o = out[name]; print('%-9s n=%3d  544 %.2f  200 %.2f  delta %s' % (name, o['n'], o['mra544'], o['mra200'], fmt(o['paired'])))
print('non-metre conversions right: 544 %(s544)d, 200 %(s200)d of %(of)d' % out['non_metre']['conversion_right'])
print('scale:', json.dumps(out['scale']))
gv = out['gap_value']; print('gap-value MRA (n=%d): 544 %s  200 %s  200 rescaled to 544 scale %s; rescale effect %s' % (gv['n'], gv['mra544_gap'], gv['mra200_gap'], gv['mra200_gap_rescaled_to_544'], fmt(gv['paired_rescale_effect']) if gv['paired_rescale_effect'] else '-'))
ca = out['call_args']; print('call args differ on %d items (same %d; without calls 544 %d, 200 %d): differ delta %s; same delta %s' % (ca['differ'], ca['same'], nocall['s544'], nocall['s200'], fmt(ca['differ_paired']) if diff else '-', fmt(ca['same_paired']) if same else '-'))
# d) step-200 items answered without any tower call vs with calls, by unit
for name, ks in (('metre', metre), ('non_metre', nonm)):
    nc = [k for k in ks if not sc.records(a[k]['output'])]; wc = [k for k in ks if k not in nc]
    for lab, s in (('no_call_at_200', nc), ('calls_at_200', wc)):
        if s: print('%-9s %-15s n=%3d  544 %.2f  200 %.2f  delta %s' % (name, lab, len(s), 100 * st.mean(mra(k, bd) for k in s), 100 * st.mean(mra(k, a) for k in s), fmt(paired(s, lambda k: mra(k, a), lambda k: mra(k, bd)))))
        out.setdefault('by_call', {})['%s/%s' % (name, lab)] = dict(n=len(s), mra544=100 * st.mean(mra(k, bd) for k in s) if s else None, mra200=100 * st.mean(mra(k, a) for k in s) if s else None)
json.dump(out, open('DIST_BREAKDOWN_m200.json', 'w'), indent=1, default=str)
