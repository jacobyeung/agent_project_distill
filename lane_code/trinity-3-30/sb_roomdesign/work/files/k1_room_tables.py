"""K1 room rows re-read by dataset (no GPU, no GT beyond what the stored per-item rows carry).

Usage: python k1_room_tables.py MERGED_DIR GD_PER_ITEM_JSONL
  MERGED_DIR          geo_k1/harness/out_merged_mdp (296 per-capture JSON; lane b14_k1towers)
  GD_PER_ITEM_JSONL   k1_ops3/work/e3gd/out/PER_ITEM.jsonl (deployed own-depth column of E3)
Labels are room_v314 on GT geometry of the same 32 frames; refusals score 0; intervals resample rooms.
"""
import glob, json, random, statistics as st, sys

merged, gd_path = sys.argv[1:3]
rows, diag = [], []
for p in sorted(glob.glob(merged + '/*.json')):
    d = json.load(open(p))
    rows += [i for i in d['items'] if i['type'] == 'room_size_estimation']
    g = d['diagnostics']
    for arm, a in g.get('arms', {}).items():
        if isinstance(a, dict) and a.get('absrel') is not None:
            diag.append((g['capture'].split('/')[0], arm, a['absrel'], a['absrel_median_aligned'], a['gt_over_pred_median']))
gd = [r for r in (json.loads(l) for l in open(gd_path)) if r['type'] == 'room_size_estimation' and r['arm'].startswith('GD_reviewed')]
rows += gd

def boot(pairs, n=10000, seed=20261119):
    rooms = {}
    for room, v in pairs:
        rooms.setdefault(room, []).append(v)
    g = [(sum(v), len(v)) for v in rooms.values()]
    rng, s = random.Random(seed), []
    for _ in range(n):
        d = [g[rng.randrange(len(g))] for _ in g]
        s.append(sum(x[0] for x in d) / sum(x[1] for x in d))
    s.sort()
    return 100 * sum(x[0] for x in g) / sum(x[1] for x in g), 100 * s[int(.025 * n)], 100 * s[int(.975 * n)]

ARMS = ['GT+R0', 'SO+G1+R0', 'da3_native+R0', 'da3_native+R2', 'da3_scale+R0', 'GD_reviewed+R0', 'GD_reviewed+R2',
        'S4+G1+R0', 'pi3x_native+R0', 'moge2_depth+R0']
print('K1 room rows, MRA x100 [95% room bootstrap]; n rows; refused; median signed and absolute relative error')
for split in ('train', 'heldout'):
    for ds in ('all', 'scannetpp', 'scannet'):
        print('== %s / %s' % (split, ds))
        for arm in ARMS:
            s = [r for r in rows if r['arm'] == arm and r['split'] == split and ds in ('all', r['dataset'])]
            if not s:
                continue
            ok = [r for r in s if r['pred'] is not None]
            rel = [(r['pred'] - r['gt']) / r['gt'] for r in ok]
            m, lo, hi = boot([(r['room'], r['mra']) for r in s])
            print('%-16s %6.2f [%5.1f, %5.1f]  n %3d  refused %2d  median rel %+.3f  median |rel| %.3f  within 15%% %.2f' % (
                arm, m, lo, hi, len(s), len(s) - len(ok), st.median(rel), st.median(abs(x) for x in rel),
                sum(abs(x) < .15 for x in rel) / len(s)))
print('\nPaired differences (same rows), MRA points [95%]')
tab = lambda arm: {r['row_id']: r for r in rows if r['arm'] == arm}
for a, b in [('da3_native+R0', 'GD_reviewed+R0'), ('da3_native+R0', 'SO+G1+R0'), ('da3_native+R0', 'da3_scale+R0'), ('da3_scale+R0', 'GD_reviewed+R0')]:
    A, B = tab(a), tab(b)
    for split in ('train', 'heldout'):
        for ds in ('all', 'scannetpp', 'scannet'):
            ids = [i for i in A if i in B and A[i]['split'] == split and ds in ('all', A[i]['dataset'])]
            m, lo, hi = boot([(A[i]['room'], A[i]['mra'] - B[i]['mra']) for i in ids])
            print('%-14s minus %-15s %-7s %-9s n %3d  %+6.2f [%+6.2f, %+6.2f]' % (a, b, split, ds, len(ids), m, lo, hi))
print('\nDepth of the candidate towers on K1 anchors against GT (296 captures; raw metric output)')
for ds in ('scannet', 'scannetpp', 'arkitscenes'):
    for arm in ('da3_native', 'pi3x_native', 'moge2_depth'):
        s = [r for r in diag if r[0] == ds and r[1] == arm]
        gp = [r[4] for r in s]
        print('%-12s %-12s n %3d  median AbsRel %.3f (median-aligned %.3f)  median GT/pred %.3f  scale within 5%% %.2f, within 10%% %.2f' % (
            ds, arm, len(s), st.median(r[2] for r in s), st.median(r[3] for r in s), st.median(gp),
            sum(abs(x - 1) < .05 for x in gp) / len(gp), sum(abs(x - 1) < .10 for x in gp) / len(gp)))
