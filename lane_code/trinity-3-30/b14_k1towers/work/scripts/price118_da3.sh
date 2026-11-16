G=/scratch/jjyeung/orch_n30/geo_k1
cat > $G/k1towers/decide.py <<'PYEOF'
"""Apply the pre-registered C-rule (GEO_TOWERS_K1_PREREG_20261116.md) to k1_price output at full precision.

Usage: python decide.py CAPTURES_DIR OUT.json [--heldout-go FILE]
Statistics follow E3's harness: item-weighted mean MRA x100; 95% percentile bootstrap over physical rooms,
10,000 draws from np.random.default_rng(20261116) keyed by the room count (paired arms share draws). R2 is
E3's fit_r2/add_r2 procedure, fitted per arm on K1 train rows only. Train tables are always computed; held-out
tables only with --heldout-go naming an ORCH note holding a line 'GO heldout'.
"""
import argparse, collections, glob, json, math
from pathlib import Path

import numpy as np

PRIMARY = {'moge2': 'moge2_scale', 'mapanything': 'mapanything_native', 'da3': 'da3_native', 'pi3x': 'pi3x_native'}
TYPES = {'object_abs_distance': '', 'room_size_estimation': '+R0'}
REF = 'S4+G1'
DIST_BAR, ROOM_BAR, ROOM_BAR_SENS, GUARD = 5.0, 73.4, 79.0, -2.0
PREREG = 'dd40e6d26a723300547c84b72add275bd2488993c2f70cd1b64fba7ae29b5c88'


def mra(pred, truth):
    # Identical to E3 harness.mra: integer thresholds avoid np.arange accumulation at exact boundaries.
    if pred is None or not math.isfinite(pred) or truth <= 0:
        return 0.0
    relative = abs(pred - truth) / abs(truth)
    return sum(relative < (100 - theta) / 100 for theta in range(50, 100, 5)) / 10


def fit_r2(rows):
    fits, grouped = {}, collections.defaultdict(list)
    for r in rows:
        if r['split'] == 'train' and r['type'] == 'room_size_estimation' and r['arm'].endswith('+R0') and not r['arm'].startswith('GT+'):
            grouped[r['arm'][:-3]].append(r)
    for arm, rs in grouped.items():
        ok = [r for r in rs if r['pred'] is not None and r['pred'] > 0 and r['refusal_code'] is None]
        fits[arm] = dict(k=float(np.median([r['gt'] / r['pred'] for r in ok])) if ok else None, n_used=len(ok),
                         n_refused=len(rs) - len(ok))
    added = []
    for r in rows:
        if r['type'] == 'room_size_estimation' and r['arm'].endswith('+R0') and not r['arm'].startswith('GT+'):
            k = (fits.get(r['arm'][:-3]) or {}).get('k')
            pred = None if r['pred'] is None or k is None else r['pred'] * k
            added.append(dict(r, arm=r['arm'][:-1] + '2', pred=pred, mra=mra(pred, r['gt']),
                              refusal_code=r['refusal_code'] or ('no_train_R2_fit' if k is None else None)))
    return fits, rows + added


class Draws(dict):
    def __missing__(self, n):
        self[n] = np.random.default_rng(20261116).integers(0, n, size=(10000, n))
        return self[n]


def interval(values, rooms, draws):
    names = sorted(set(rooms))
    idx = {n: i for i, n in enumerate(names)}
    cl = np.array([idx[r] for r in rooms])
    sums = np.bincount(cl, weights=np.asarray(values, float), minlength=len(names))
    counts = np.bincount(cl, minlength=len(names)).astype(float)
    d = draws[len(names)]
    est = sums[d].sum(1) / counts[d].sum(1)
    return [float(100 * np.percentile(est, 2.5)), float(100 * np.percentile(est, 97.5))]


def tables(rows, split, draws):
    out = {}
    for typ, suf in TYPES.items():
        by = collections.defaultdict(dict)
        for r in rows:
            if r['type'] == typ:
                by[r['arm']]  # every arm seen in any split; an arm absent from this split scores 0 on every item
        for r in rows:
            if r['split'] == split and r['type'] == typ:
                by[r['arm']][r['row_id']] = r
        if not any(by.values()):
            continue
        ids = sorted(by['GT' + ('+R0' if suf else '')])
        rooms = [by['GT' + ('+R0' if suf else '')][i]['room'] for i in ids]
        vals = {a: np.array([by[a][i]['mra'] if i in by[a] else 0. for i in ids]) for a in by}
        missing = {a: sum(i not in by[a] for i in ids) for a in by}
        res = {}
        for a in sorted(by):
            rec = dict(mean=float(100 * vals[a].mean()), ci95=interval(vals[a], rooms, draws), n_items=len(ids),
                       n_rooms=len(set(rooms)), refusals=sum(1 for i in ids if i in by[a] and by[a][i]['refusal_code']),
                       missing_items=missing[a])
            ref = REF + ('+' + a.split('+')[-1] if typ == 'room_size_estimation' and '+' in a else '')
            if ref in vals and ref != a:
                diff = vals[a] - vals[ref]
                rec.update(vs=ref, diff=float(100 * diff.mean()), diff_ci95=interval(diff, rooms, draws))
            res[a] = rec
        out[typ] = res
    return out


def decide(tr, ho):
    dec = {}
    for m, arm in PRIMARY.items():
        d = {}
        for typ, suf in TYPES.items():
            t = tr.get(typ, {}).get(arm + suf)
            if t is None or 'diff' not in t:
                d[typ] = dict(status='absent')
                continue
            row = dict(train_mean=t['mean'], train_diff=t['diff'], train_diff_lo=t['diff_ci95'][0])
            if ho is not None:
                h, ref = ho[typ][arm + suf], ho[typ][REF + suf]
                row.update(heldout_mean=h['mean'], heldout_diff=h['diff'], heldout_diff_ci95=h['diff_ci95'],
                           vsi_points_heldout=h['diff'] / 8)
                row['qualifies'] = row['train_diff_lo'] > 0 and h['diff'] > 0
                row['bar'] = ref['mean'] + DIST_BAR if typ == 'object_abs_distance' else ROOM_BAR
                row['clears_bar'] = h['mean'] >= row['bar']
                if typ == 'room_size_estimation':
                    row['clears_sensitivity_bar'] = h['mean'] >= ROOM_BAR_SENS
            d[typ] = row
        if ho is not None:
            q = [t for t in TYPES if d[t].get('qualifies')]
            guard = all(d[o].get('train_diff_lo') is not None and d[o]['train_diff_lo'] >= GUARD
                        for t in q for o in TYPES if o != t)
            d['replaces_g3t'] = bool(q) and guard
        dec[m] = d
    if ho is None:
        return dec, None
    winners = {}
    for typ in TYPES:
        qual = sorted(((dec[m][typ]['train_mean'], m) for m in dec if dec[m][typ].get('qualifies')), reverse=True)
        if not qual or (len(qual) > 1 and qual[0][0] == qual[1][0]):
            winners[typ] = 'G3T'
        else:
            winners[typ] = qual[0][1] if dec[qual[0][1]]['replaces_g3t'] else 'G3T'
    gt_free = [REF + '+R0'] + [arm + '+R0' for arm in PRIMARY.values()]  # secondary arms are diagnostic, never decide
    room_path = sorted(a for a in gt_free if a in ho.get('room_size_estimation', {})
                       and ho['room_size_estimation'][a]['mean'] >= ROOM_BAR)
    return dec, dict(per_type_winner=winners, room_head_path_arms_at_bar=room_path,
                     note='Per-type winners; a candidate replaces G3T only if replaces_g3t holds (qualifies on one type, other-type train lower bound >= -2).')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('captures'); ap.add_argument('out')
    ap.add_argument('--heldout-go')
    a = ap.parse_args()
    rows = [r for p in sorted(glob.glob(a.captures + '/*.json')) for r in json.load(open(p))['items']]
    r2, rows = fit_r2(rows)
    draws = Draws()
    res = dict(prereg_sha256=PREREG, reference=REF, r2_fits=r2, tables={'train': tables(rows, 'train', draws)})
    ho = None
    if a.heldout_go:
        if not any(l.strip() == 'GO heldout' for l in Path(a.heldout_go).read_text().splitlines()):
            raise PermissionError('held-out tables need an ORCH note with a "GO heldout" line')
        ho = res['tables']['heldout'] = tables(rows, 'heldout', draws)
    res['decision'], res['verdict'] = decide(res['tables']['train'], ho)
    Path(a.out).write_text(json.dumps(res, indent=1))
    for typ, t in res['tables']['train'].items():
        print('##', typ, 'train')
        for arm, s in t.items():
            print(f"{arm:24s} {s['mean']:7.2f} [{s['ci95'][0]:6.2f},{s['ci95'][1]:6.2f}] ref={s['refusals']}"
                  + (f" | vs {s['vs']}: {s['diff']:+7.2f} [{s['diff_ci95'][0]:+7.2f},{s['diff_ci95'][1]:+7.2f}]" if 'diff' in s else ''))
    print(json.dumps(res['verdict']))


if __name__ == '__main__':
    main()
PYEOF
cat > $G/k1towers/merge_caps.py <<'PYEOF'
"""Merge per-capture k1_price outputs from several run folders (reference run + candidate-only runs) into one folder.
Usage: python merge_caps.py OUT_DIR REF_CAPTURES CAND_CAPTURES...   Every candidate folder must cover every reference
capture; a duplicate (row_id, arm) pair is an error. Diagnostics are merged under diagnostics.arms."""
import json, sys
from pathlib import Path
out, ref, *cands = map(Path, sys.argv[1:])
out.mkdir(parents=True, exist_ok=True)
if any(out.iterdir()):
    raise ValueError(f'output folder must be empty: {out}')
n = 0
for p in sorted(ref.glob('*.json')):
    d = json.loads(p.read_text())
    seen = {(r['row_id'], r['arm']) for r in d['items']}
    if len(seen) != len(d['items']):
        raise ValueError(f'duplicate (row_id, arm) in reference {p}')
    for c in cands:
        q = json.loads((c / p.name).read_text())
        assert q['diagnostics']['capture'] == d['diagnostics']['capture']
        for r in q['items']:
            k = (r['row_id'], r['arm'])
            if k in seen:
                raise ValueError(f'duplicate {k} in {c / p.name}')
            seen.add(k)
            d['items'].append(r)
        d['diagnostics'].setdefault('arms', {}).update(q['diagnostics'].get('arms', {}))
    (out / p.name).write_text(json.dumps(d))
    n += 1
print('merged', n, 'captures from', len(cands), 'candidate folders')
PYEOF
cat > $G/k1towers/tests/test_decide.py <<'PYEOF'
import json, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import decide as D


def T(mean, lo, diff=None, dlo=None):
    t = dict(mean=mean, ci95=[lo, mean + 1])
    if diff is not None:
        t.update(vs='ref', diff=diff, diff_ci95=[dlo, diff + 1])
    return t


def tabs(cands, ref_dist=50., ref_room=60.):
    out = {'object_abs_distance': {'S4+G1': T(ref_dist, 0)}, 'room_size_estimation': {'S4+G1+R0': T(ref_room, 0)}}
    for m, (dist, room) in cands.items():
        arm = D.PRIMARY[m]
        out['object_abs_distance'][arm] = T(*dist)
        out['room_size_estimation'][arm + '+R0'] = T(*room)
    return out


def test_small_positive_lower_bound_and_zero_guard():
    tr = tabs({'da3': ((60., 0, 1.0, 0.04), (55., 0, -1.0, 0.0))})
    ho = tabs({'da3': ((56., 0, 0.5, -3), (59., 0, -1.0, -5))})
    dec, v = D.decide(tr, ho)
    assert dec['da3']['object_abs_distance']['qualifies'] is True
    assert dec['da3']['replaces_g3t'] is True          # zero other-type lower bound passes the -2 guard
    assert v['per_type_winner']['object_abs_distance'] == 'da3'
    assert dec['da3']['object_abs_distance']['clears_bar'] is True  # 56 >= 50 + 5


def test_guard_rejects_below_minus_two():
    tr = tabs({'da3': ((60., 0, 1.0, 0.5), (55., 0, -3.0, -2.04))})
    ho = tabs({'da3': ((56., 0, 0.5, -3), (59., 0, -1.0, -5))})
    dec, v = D.decide(tr, ho)
    assert dec['da3']['replaces_g3t'] is False and v['per_type_winner']['object_abs_distance'] == 'G3T'


def test_tie_goes_to_g3t_and_bar_full_precision():
    tr = tabs({'da3': ((60., 0, 1.0, 0.5), (73.36, 0, 1., .1)), 'moge2': ((60., 0, 1.0, 0.5), (50., 0, 1., .1))})
    ho = tabs({'da3': ((56., 0, 0.5, -3), (73.36, 0, 1., -5)), 'moge2': ((56., 0, 0.5, -3), (50., 0, 1., -5))})
    dec, v = D.decide(tr, ho)
    assert v['per_type_winner']['object_abs_distance'] == 'G3T'
    assert dec['da3']['room_size_estimation']['clears_bar'] is False   # 73.36 < 73.4
    assert v['per_type_winner']['room_size_estimation'] == 'da3'


def test_tables_match_agg_and_gate():
    rng = np.random.default_rng(0)
    with tempfile.TemporaryDirectory() as d:
        caps = Path(d) / 'captures'; caps.mkdir()
        for c in range(12):
            items = []
            for k in range(3):
                gt = float(rng.uniform(1, 5))
                for arm, noise in (('GT', .05), ('S4+G1', .3), ('da3_native', .2)):
                    p = gt * (1 + rng.normal(0, noise))
                    items.append(dict(row_id=f'{c}-{k}', capture=f'x/{c}', room=f'r{c // 2}', split='train', dataset='scannet',
                                      type='object_abs_distance', arm=arm, pred=p, gt=gt, mra=D.mra(p, gt), refusal_code=None))
            gt = float(rng.uniform(10, 30))
            for arm in ('GT', 'S4+G1', 'da3_native'):
                for r in ('R0', 'R1'):
                    p = gt * (1 + rng.normal(0, .2))
                    items.append(dict(row_id=f'{c}-room', capture=f'x/{c}', room=f'r{c // 2}', split='train', dataset='scannet',
                                      type='room_size_estimation', arm=arm + '+' + r, pred=p, gt=gt, mra=D.mra(p, gt), refusal_code=None))
            (caps / f'x__{c}.json').write_text(json.dumps(dict(items=items)))
        out = Path(d) / 'res.json'
        subprocess.run([sys.executable, str(HERE / 'decide.py'), str(caps), str(out)], check=True, capture_output=True)
        res = json.loads(out.read_text())
        agg = subprocess.run([sys.executable, str(HERE / 'agg.py'), str(caps), 'train', '-', 'S4+G1'], check=True,
                             capture_output=True, text=True).stdout
        for line in agg.splitlines():
            if line.startswith('da3_native ') and '| vs S4+G1:' in line:
                mean = float(line.split()[1])
                assert abs(res['tables']['train']['object_abs_distance']['da3_native']['mean'] - mean) < .051
        assert 'da3_native+R2' in res['tables']['train']['room_size_estimation']
        go = Path(d) / 'go.md'; go.write_text('no\n')
        p = subprocess.run([sys.executable, str(HERE / 'decide.py'), str(caps), str(out), '--heldout-go', str(go)], capture_output=True)
        assert p.returncode != 0 and b'PermissionError' in p.stderr


def test_room_path_ignores_secondary_and_missing_heldout_arm_scores_zero():
    tr = tabs({'da3': ((60., 0, 1.0, 0.5), (55., 0, 1., .1))})
    ho = tabs({'da3': ((56., 0, 0.5, -3), (60., 0, 1., -5))})
    ho['room_size_estimation']['SO+G1+R0'] = T(90., 0, 30., 1.)
    ho['room_size_estimation']['da3_native+R2'] = T(90., 0, 30., 1.)
    dec, v = D.decide(tr, ho)
    assert v['room_head_path_arms_at_bar'] == []
    rows = []
    for split, arms in (('train', ('GT', 'S4+G1', 'da3_native')), ('heldout', ('GT', 'S4+G1'))):
        for k in range(4):
            for a in arms:
                rows.append(dict(row_id=f'{split}{k}', room=f'{split}r{k}', split=split, type='object_abs_distance', arm=a,
                                 pred=1., gt=1., mra=1., refusal_code=None))
    t = D.tables(rows, 'heldout', D.Draws())['object_abs_distance']
    assert t['da3_native']['mean'] == 0 and t['da3_native']['missing_items'] == 4 and t['da3_native']['diff'] == -100


def test_mra_boundary_matches_e3():
    assert D.mra(0.55, 1.0) == 0.2 and D.mra(None, 1.0) == 0.0 and D.mra(float('nan'), 1.0) == 0.0


def test_merge_requires_empty_output_and_rejects_reference_duplicates():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d); ref = d / 'ref'; cand = d / 'cand'; ref.mkdir(); cand.mkdir()
        item = dict(row_id='a', arm='GT')
        (ref / 'x.json').write_text(json.dumps(dict(diagnostics=dict(capture='x'), items=[item])))
        (cand / 'x.json').write_text(json.dumps(dict(diagnostics=dict(capture='x', arms={}), items=[dict(row_id='a', arm='c')])))
        out = d / 'out'
        subprocess.run([sys.executable, str(HERE / 'merge_caps.py'), str(out), str(ref), str(cand)], check=True)
        p = subprocess.run([sys.executable, str(HERE / 'merge_caps.py'), str(out), str(ref), str(cand)], stderr=subprocess.PIPE)
        assert p.returncode != 0 and b'must be empty' in p.stderr
        (ref / 'x.json').write_text(json.dumps(dict(diagnostics=dict(capture='x'), items=[item, item])))
        p = subprocess.run([sys.executable, str(HERE / 'merge_caps.py'), str(d / 'out2'), str(ref), str(cand)], stderr=subprocess.PIPE)
        assert p.returncode != 0 and b'duplicate' in p.stderr


if __name__ == '__main__':
    for k, f in list(globals().items()):
        if k.startswith('test_'):
            f(); print('PASS', k)
PYEOF
cd $G && sha256sum -c <<"S"
e2748156b00b957d49a1f851abad07d802cd80c12278b5532a034b36f2da264c  k1towers/k1_convert.py
9e7e205ecf207c6eee32a8386bfc68ed39457c7c144bae721f73242b0ee40324  k1towers/k1_price.py
9c1586b12db8558d9c6e3579957d8a3a2784c7c4ac5e800cd24544a7bc5c0615  k1towers/decide.py
6b97e80f48a25769caa5024c298e269b91ec47d26f473069bd0167c5b5afe9ca  k1towers/merge_caps.py
S
python3 -c "import json,collections;print(collections.Counter(json.loads(l)[\"state\"] for l in open(\"$G/pred_gpu/da3/progress.jsonl\")))"
MODEL=da3
# header sets MODEL; runs on trinity-1-18
set -u
G=/scratch/jjyeung/orch_n30/geo_k1; cd $G; date -u
M=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json; T=/scratch/jjyeung/k1/run_tower_sam_2; PY=/scratch/jjyeung/envs/planner_local_v1/bin/python
ls pred_gpu/$MODEL | wc -l
cat > logs/price_$MODEL.sh <<EOS
cd $G
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1 TMPDIR=$G/tmp MPLCONFIGDIR=$G/tmp/mpl
$PY -B k1towers/k1_convert.py --model $MODEL --pred pred_gpu/$MODEL --manifest $M --towers $T --out $G/geom > logs/convert_$MODEL.log 2>&1
echo EXIT \$? >> logs/convert_$MODEL.log
ARMS=""; for a in \$(ls -d $G/geom/${MODEL}_*/); do n=\$(basename \$a); ARMS="\$ARMS --arm \$n=\$a"; done
echo ARMS \$ARMS >> logs/convert_$MODEL.log
cd harness
for i in 0 1 2 3; do $PY -B k1_price.py --out out_$MODEL --fits e3_FITS.json --no-reference --shard \$i/4 \$ARMS > ../logs/price_${MODEL}_\$i.log 2>&1 & done
wait
echo PRICE_DONE >> ../logs/convert_$MODEL.log
EOS
tmux new-session -d -s b14_price_$MODEL "bash $G/logs/price_$MODEL.sh"
sleep 60; cat logs/convert_$MODEL.log | tail -5; tail -n1 logs/price_${MODEL}_0.log
