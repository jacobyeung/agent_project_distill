"""Re-price the K1 distance towers on corrected labels (lane tower_redecide).

1. Builds corrected copies of b14's merged per-capture files (out_merged_mdp, read-only copy in gt_audit/work/k1b) with
   K1_LABELS_CORRECTED.jsonl (rows with convention 'half' take the corrected label; MRA recomputed with decide.mra) and
   runs the registered decide.py (unchanged, sha checked) on them: the registered C-rule against S4+G1.
2. Adds E3's deployed G3T column GD_reviewed (and GD_sealed) from e3gd PER_ITEM.jsonl, corrected the same way, and
   reports every arm against S4+G1 (registered reference) and against GD_reviewed (deployed reference), on train and
   held-out, on all rows, on the unaffected rows (labels unchanged), on rows both arms answered, and per dataset.
Statistics are decide.py's: item-weighted mean MRA x100, 95% percentile bootstrap over physical rooms, 10,000 draws,
seed 20261116 keyed by room count (paired arms share draws).
"""
import collections, glob, hashlib, json, os, subprocess, sys
import importlib.util
import numpy as np

GA = '/scratch/jjyeung/orch_n30/gt_audit'
SRC = GA + '/work/k1b/orch_n30/geo_k1/harness/out_merged_mdp'
DEC = GA + '/work/k1b/orch_n30/geo_k1/k1towers/decide.py'
GD = GA + '/work/k1/orch_n30/k1_ops3/work/e3gd/out/PER_ITEM.jsonl'
LABF = GA + '/out/audit/k1/K1_LABELS_CORRECTED.jsonl'
GO = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/b14_k1towers/20261116T1453Z_ORCH_GO_heldout.md'
W = '/scratch/jjyeung/orch_n30/tower_redecide/work/reprice'
DECIDE_SHA = '9c1586b12db8558d9c6e3579957d8a3a2784c7c4ac5e800cd24544a7bc5c0615'

assert hashlib.sha256(open(DEC, 'rb').read()).hexdigest() == DECIDE_SHA, 'decide.py changed'
spec = importlib.util.spec_from_file_location('decide_copy', DEC); D = importlib.util.module_from_spec(spec); spec.loader.exec_module(D)
LAB = {json.loads(l)['id']: json.loads(l) for l in open(LABF)}
DRAWS = D.Draws()
DIST = 'object_abs_distance'
ARMS = ['GD_reviewed', 'S4+G1', 'pi3x_native', 'da3_native', 'moge2_scale', 'pi3x_scale', 'da3_scale', 'moge2_depth', 'SO+G1', 'GT', 'GD_sealed']


def fix(it, variant):
    if it['type'] != DIST:
        return it
    lab = LAB[it['row_id']]
    assert abs(lab['stored'] - it['gt']) < 1e-9, it['row_id']
    if variant == 'corrected' and lab['convention'] == 'half':
        return dict(it, gt=lab['corrected'], mra=D.mra(it['pred'], lab['corrected']))
    assert abs(D.mra(it['pred'], it['gt']) - it['mra']) < 1e-12
    return it


def build(variant):
    out = os.path.join(W, 'caps_' + variant); os.makedirs(out, exist_ok=True)
    rows = []
    for p in sorted(glob.glob(SRC + '/*.json')):
        cap = json.load(open(p)); items = [fix(it, variant) for it in cap['items']]
        json.dump(dict(cap, items=items), open(os.path.join(out, os.path.basename(p)), 'w'))
        rows += items
    return out, rows


def gd_rows(variant):
    rows = []
    for l in open(GD):
        r = json.loads(l)
        if r['arm'].startswith('GD_') and r['type'] == DIST:
            rows.append(fix(r, variant))
    return rows


def stat(vals, rooms):
    return dict(mean=float(100 * np.mean(vals)), ci95=D.interval(vals, rooms, DRAWS))


def table(rows, split, subset=None, label=''):
    by = collections.defaultdict(dict)
    for r in rows:
        if r['type'] == DIST and r['split'] == split:
            by[r['arm']][r['row_id']] = r
    ids = sorted(i for i in by['GT'] if subset is None or subset(LAB[i]))
    rooms = [by['GT'][i]['room'] for i in ids]
    ds = collections.Counter(by['GT'][i]['dataset'] for i in ids)
    vals = {a: np.array([by[a][i]['mra'] if i in by[a] else 0. for i in ids]) for a in ARMS}
    ans = {a: np.array([i in by[a] and by[a][i]['refusal_code'] is None and by[a][i]['pred'] is not None for i in ids]) for a in ARMS}
    res = dict(label=label, split=split, n_items=len(ids), n_rooms=len(set(rooms)), datasets=dict(ds), arms={})
    for a in ARMS:
        rec = stat(vals[a], rooms); rec['refused_or_missing'] = int((~ans[a]).sum())
        for ref in ('S4+G1', 'GD_reviewed'):
            if ref == a:
                continue
            rec['vs_' + ref] = stat(vals[a] - vals[ref], rooms)
            both = ans[a] & ans[ref]
            if both.sum() and not both.all():
                rr = [rooms[k] for k in np.flatnonzero(both)]
                rec['vs_' + ref + '_both_answered'] = dict(stat(vals[a][both] - vals[ref][both], rr), n_items=int(both.sum()))
        rec['by_dataset'] = {d: float(100 * np.mean([vals[a][k] for k, i in enumerate(ids) if by['GT'][i]['dataset'] == d])) for d in sorted(ds)}
        res['arms'][a] = rec
    for x, y in (('pi3x_native', 'da3_native'), ('pi3x_native', 'moge2_scale'), ('da3_native', 'moge2_scale')):
        res['arms'][x]['vs_' + y] = stat(vals[x] - vals[y], rooms)
    return res


def show(t):
    print(f"### {t['label']} {t['split']}: {t['n_items']} rows / {t['n_rooms']} rooms {t['datasets']}")
    for a, s in t['arms'].items():
        line = f"{a:12s} {s['mean']:6.2f} [{s['ci95'][0]:6.2f},{s['ci95'][1]:6.2f}] ref={s['refused_or_missing']:3d}"
        for ref in ('S4+G1', 'GD_reviewed'):
            k = 'vs_' + ref
            if k in s:
                line += f" | vs {ref}: {s[k]['mean']:+6.2f} [{s[k]['ci95'][0]:+6.2f},{s[k]['ci95'][1]:+6.2f}]"
                if k + '_both_answered' in s:
                    b = s[k + '_both_answered']; line += f" (both {b['n_items']}: {b['mean']:+6.2f} [{b['ci95'][0]:+6.2f},{b['ci95'][1]:+6.2f}])"
        print(line)
        if a in ('pi3x_native', 'da3_native'):
            print('             by dataset', {d: round(v, 2) for d, v in s['by_dataset'].items()},
                  {k: (round(v['mean'], 2), [round(x, 2) for x in v['ci95']]) for k, v in s.items() if k in ('vs_da3_native', 'vs_moge2_scale')})
    sys.stdout.flush()


def main():
    os.makedirs(W, exist_ok=True)
    allres = {}
    for variant in ('stored', 'corrected'):
        capdir, rows = build(variant)
        r = subprocess.run([sys.executable, '-B', DEC, capdir, os.path.join(W, f'decide_{variant}.json'), '--heldout-go', GO], capture_output=True, text=True)
        open(os.path.join(W, f'decide_{variant}.stdout'), 'w').write(r.stdout + r.stderr)
        print(variant, 'decide.py rc', r.returncode, r.stdout.strip().splitlines()[-1], flush=True)
        rows = rows + gd_rows(variant)
        for split in ('train', 'heldout'):
            for lab, sub in (('all', None), ('unaffected', lambda l: not l['affected']), ('scannetpp', lambda l: l['dataset'] == 'scannetpp')):
                if variant == 'stored' and lab != 'all':
                    continue
                t = table(rows, split, sub, f'{variant}/{lab}'); show(t); allres[f'{variant}/{lab}/{split}'] = t
    json.dump(allres, open(os.path.join(W, 'REPRICE_TABLES.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
