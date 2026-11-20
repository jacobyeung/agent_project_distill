"""K1-X registered parity gate. A failed gate stops all geometry ablations.

This receipt audit uses saved per-item predictions, not a fresh raster replay.
The input references disagree on the gravity guard. Full cell execution and
geometry-swap tests remain unimplemented because registration rule 0 stops here.
"""
import os
for _name in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
              'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[_name] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import argparse
import ast
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
import time
import types

import numpy as np

ROOT = Path(__file__).resolve().parent
SEED = 20261120
DRAWS = 10000
STOP = 'NOT_RUN_PARITY_STOP'
REFUSAL = 'reference_camera_up_opposes_gravity'


def declaration(path, name, bindings=None):
    """Load a pure declaration without executing a harness's writers/imports."""
    tree = ast.parse(Path(path).read_text())
    nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))
             and n.name == name]
    if len(nodes) != 1:
        raise ValueError(f'Expected one declaration: {name}')
    namespace = dict(math=math, np=np, **(bindings or {}))
    exec(compile(ast.Module(nodes, []), str(path), 'exec'), namespace)
    return namespace[name]


mra = declaration(ROOT / 'vendor/gd_harness.py', 'mra')


class Inputs:
    def __init__(self):
        self.hashes = {}
        self.bytes = 0

    def read(self, path):
        p = Path(path).resolve()
        if not p.is_relative_to('/scratch'):
            raise ValueError(f'Only local scratch inputs are allowed: {p}')
        data = p.read_bytes()
        self.bytes += len(data)
        self.hashes[str(p)] = dict(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
        return data

    def json(self, path):
        return json.loads(self.read(path))

    def selected_jsonl(self, path, arms):
        """Sequential local-file pass; unrelated contrasts are never decoded."""
        p = Path(path).resolve()
        if not p.is_relative_to('/scratch'):
            raise ValueError('Only local scratch inputs are allowed')
        result, h, size = [], hashlib.sha256(), 0
        tokens = [f'"arm": "{a}"'.encode() for a in arms]
        with p.open('rb') as stream:
            for line in stream:
                h.update(line)
                size += len(line)
                if any(token in line for token in tokens):
                    row = json.loads(line)
                    if row['arm'] in arms:
                        result.append(row)
        self.hashes[str(p)] = dict(sha256=h.hexdigest(), bytes=size)
        self.bytes += size
        return result


def parity_check(key, rows, target):
    value = 100 * math.fsum(r['score'] for r in rows) / len(rows)
    return dict(key=key, rows=len(rows), rooms=len({r['room'] for r in rows}),
                expected=target, observed=value, delta=value-target, tolerance=.2,
                passed=abs(value-target) <= .2)


def bootstrap(rows):
    """Item-weighted mean under physical-room resampling, common seeded draws."""
    rooms = sorted({r['room'] for r in rows})
    if not rooms:
        return dict(n=0, rooms=0, mean=None, ci95=None)
    index = {room:i for i,room in enumerate(rooms)}
    counts = np.zeros(len(rooms))
    sums = np.zeros(len(rooms))
    for row in rows:
        i = index[row['room']]
        counts[i] += 1
        sums[i] += row['score'] * 100
    rng = np.random.default_rng(SEED)
    draws = rng.integers(len(rooms), size=(DRAWS, len(rooms)))
    values = sums[draws].sum(1) / counts[draws].sum(1)
    return dict(n=len(rows), rooms=len(rooms), mean=float(sums.sum()/counts.sum()),
                ci95=np.percentile(values, [2.5,97.5]).tolist())


def guarded_row(row, label, refused, source):
    prediction = row.get('prediction', row.get('pred'))
    reason = row.get('refusal_code')
    original = prediction
    if refused:
        prediction, reason = None, 'GeometryError:' + REFUSAL
    return dict(row_id=row['row_id'], capture=row['capture'], room=row['room'],
                dataset=row['dataset'], split=row['split'], source_arm=row['arm'],
                source=source, prediction=prediction, source_prediction=original,
                corrected_label=label, score=mra(prediction,label),
                source_score=mra(original,label), refusal_code=reason,
                reviewed_guard_refused=refused)


def options():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['run','test'], nargs='?', default='run')
    paths = dict(
        labels='/scratch/jjyeung/n30_mirror/gt_audit/gt_audit/work/k1audit/K1_LABELS_CORRECTED.jsonl',
        rowsets='/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS',
        train1012='/scratch/jjyeung/orch_n30/sb_k1012/out/K1_TRAIN_1012.txt',
        manifest='/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json',
        e3='/scratch/jjyeung/orch_n30/e3_geom/work/harness',
        gd='/scratch/jjyeung/orch_n30/k1_ops3/work/e3gd',
        ladder='/scratch/jjyeung/orch_n30/sb_kbox4',
        convert='/scratch/jjyeung/k1/run_convert_2',
        out=str(ROOT/'out'))
    for name, default in paths.items():
        p.add_argument('--'+name, type=Path, default=Path(default))
    return p.parse_args()


def audit(args):
    started = time.monotonic()
    inputs = Inputs()
    raw = inputs.read(args.labels)
    if not hashlib.sha256(raw).hexdigest().startswith('d781ac7b'):
        raise ValueError('Corrected-label SHA256 must start d781ac7b')
    labels = {r['id']:r for r in map(json.loads, raw.splitlines())}
    sets = {split:set(inputs.read(args.rowsets/name).decode().splitlines())
            for split,name in [('heldout','K1_HELDOUT_216.txt'),('train','K1_TRAIN_1037.txt')]}
    train1012 = set(inputs.read(args.train1012).decode().splitlines())
    assert len(sets['heldout']) == 216 and len(sets['train']) == 1037
    assert len(train1012) == 1012 and train1012 <= sets['train']
    assert not sets['heldout'] & sets['train']
    manifest = inputs.json(args.manifest)
    capture_by_row = {r['id']:c for c in manifest['captures'] for r in c['rows']}
    manifest_rows = {r['id']:r for c in manifest['captures'] for r in c['rows']}
    for split, ids in sets.items():
        assert len({capture_by_row[i]['room'] for i in ids}) == (48 if split=='heldout' else 192)
        for rid in ids:
            assert labels[rid]['corrected'] is not None
            assert capture_by_row[rid]['k1_split'] == split
            assert labels[rid]['capture'] == capture_by_row[rid]['canonical']
    assert not ({capture_by_row[i]['room'] for i in sets['heldout']} &
                {capture_by_row[i]['room'] for i in sets['train']})
    e3_path = args.gd/'out/PER_ITEM.jsonl'
    e3 = inputs.selected_jsonl(e3_path, {'GT','GD_reviewed'})
    e3 = [r for r in e3 if r['type']=='object_abs_distance' and r['row_id'] in sets[r['split']]]
    by = {arm:{r['row_id']:r for r in e3 if r['arm']==arm} for arm in ['GT','GD_reviewed']}
    for arm in by:
        assert set(by[arm]) == sets['train'] | sets['heldout']
    # Use the reviewed harness's saved refusals, independently of ladder flags.
    refused = {r['capture'] for r in by['GD_reviewed'].values()
               if REFUSAL in (r['refusal_code'] or '')}
    groups = {}
    for arm in by:
        key = 'heldout_gt_geometry' if arm=='GT' else 'heldout_served_gt_masks'
        groups[key] = [guarded_row(by[arm][i],labels[i]['corrected'],False,str(e3_path))
                       for i in sorted(sets['heldout'])]
    print('Loaded held-out parity references; auditing train guard.', flush=True)
    ladder_path = args.ladder/'out/box_ladder/PER_ITEM.jsonl'
    ladder = inputs.selected_jsonl(ladder_path, {'A0_deployed','A2_gt_masks'})
    lb = {arm:{r['row_id']:r for r in ladder if r['arm']==arm}
          for arm in ['A0_deployed','A2_gt_masks']}
    for arm in lb:
        assert len(lb[arm]) == sum(r['arm']==arm for r in ladder) == 1037
        assert set(lb[arm]) == sets['train']
        key = 'train_deployed_masks' if arm=='A0_deployed' else 'train_gt_masks'
        values = []
        for i in sorted(sets['train']):
            row = lb[arm][i]
            assert row['label'] == labels[i]['corrected']
            assert row['capture'] == capture_by_row[i]['canonical']
            assert row['reviewed_guard_refused'] == (row['capture'] in refused)
            values.append(guarded_row(row,labels[i]['corrected'],row['capture'] in refused,str(ladder_path)))
        groups[key] = values
    targets = dict(heldout_served_gt_masks=75.05,heldout_gt_geometry=91.99,
                   train_deployed_masks=56.8,train_gt_masks=74.0)
    parity = [parity_check(k,groups[k],v) for k,v in targets.items()]
    if all(r['passed'] for r in parity):
        raise RuntimeError('Unexpected parity pass: ablation implementation requires a consistent reference contract')
    # Registration rule 0: no ablation, contrast, or downstream verdict is evaluated.
    sources = inputs.json(args.ladder/'out/box_ladder/BASE_TABLE.json')['arms']
    attribution = []
    for key, arm in [('train_deployed_masks','A0_deployed'),('train_gt_masks','A2_gt_masks')]:
        rows = groups[key]
        original = math.fsum(r['source_score'] for r in rows)*100/len(rows)
        assert abs(original-sources[arm]['mra']) < 1e-10
        removed = [r for r in rows if r['reviewed_guard_refused']]
        attribution.append(dict(cell=key, original=original,
            reviewed=math.fsum(r['score'] for r in rows)*100/len(rows),
            affected_rows=len(removed), removed_score_sum=math.fsum(r['source_score'] for r in removed),
            captures=sorted({r['capture'] for r in removed}), per_row=removed))
    # Preserve source files without executing their global side effects.
    for path in [args.e3/'harness.py', args.gd/'harness.py',args.gd/'gravity_guard.py',
                 args.ladder/'reader_src/e2e_reader/geometry.py',
                 args.ladder/'reader_src/e2e_reader/grounding.py',
                 args.ladder/'train_pricing.py', args.ladder/'out/REPORT.md']:
        inputs.read(path)
    copies = inputs.json(ROOT/'vendor/COPIES.json')
    for entry in copies:
        inputs.read(entry['copy'])
        assert hashlib.sha256(inputs.read(entry['source'])).hexdigest() == entry['source_sha256']
    buckets = dict(all=lambda r:True, arkitscenes=lambda r:r['dataset']=='arkitscenes',
                   scannet_scannetpp=lambda r:r['dataset'] in ('scannet','scannetpp'),
                   scannet=lambda r:r['dataset']=='scannet',scannetpp=lambda r:r['dataset']=='scannetpp')
    tables = {key:{ds:bootstrap([r for r in rows if keep(r)]) for ds,keep in buckets.items()}
              for key,rows in groups.items()}
    cells = [dict(masks=m,depth=d,relative_pose=p,scale=s,status=STOP)
             for m,d,p,s in itertools.product(['GT','deployed'],['G3T','GT'],['G3T','GT'],['own rule','GT'])]
    verdicts = {name:dict(status=STOP,estimate=None,ci95=None,verdict='WITHHELD')
                for name in ['C1','C3_pose','C3_depth','C3_interaction','arm_B_full_gate','C5','C6','Pi3X','DA3']}
    missing = []
    for cap in sorted(refused):
        key=hashlib.sha256(json.dumps(cap,sort_keys=True,allow_nan=False).encode()).hexdigest()[:16]
        for name in ['REFUSED_GEOMETRY.npz','CACHE_COMPLETE.json']:
            path=args.convert/key/name
            if not path.exists():
                missing.append(str(path))
    return dict(status='PARITY_STOP',mode='saved_prediction_receipt_audit',
        parity=parity,parity_rows=groups,parity_tables=tables,guard_attribution=attribution,
        registered_cells=cells,contrasts=verdicts,
        depth_absrel=dict(status=STOP),relative_pose_error=dict(status=STOP),same_frame_share=dict(status=STOP),
        own_depth=dict(status=STOP),tower_coverage=dict(status=STOP),oracle_boxes=dict(status=STOP),
        tests=dict(synthetic_cell_swaps=STOP,raw_geometry_replay=STOP),
        populations={s:dict(rows=len(ids),rooms=len({capture_by_row[i]['room'] for i in ids})) for s,ids in
                     [('heldout',sets['heldout']),('train1037',sets['train']),('train1012',train1012)]},
        scale_matching=dict(status=STOP,reason='No mixed-geometry cell was built after the parity gate failed'),
        missing_refused_capture_files=missing,copied_sources=copies,
        input_sha256=inputs.hashes,
        statistics=dict(draws=DRAWS,seed=SEED,interval='percentile 95%',unit='physical room',
                        weighting='item weighted',contrasts_evaluated=False),
        resource_use=dict(input_bytes_read=inputs.bytes,seconds=time.monotonic()-started,threads=1),
        limitations=['The saved reference predictions were rescored; geometry and selector inference were not rerun.',
          'The E3 and box-ladder references use different lifting and box providers as well as different guards.',
          'All factorial cells, tower/own-depth rows, diagnostics, and endpoint-swap tests are withheld by rule 0.',
          'The 1012-row set is validated but has no post-gate cell estimates.',
          'The listed refused-capture geometry/receipt files are absent; guard provenance comes from saved E3 and ladder records.'])


def fmt(value):
    return f"{value['mean']:.2f} [{value['ci95'][0]:.2f}, {value['ci95'][1]:.2f}]"


def report(result):
    lines = [
        'K1-X stops at registered parity rule 0. No ablation contrast or scientific verdict is available.',
        'The reviewed gravity guard refuses two train captures that the box-ladder reference accepts.',
        'This audit rescores saved per-item predictions against corrected labels; it does not replay raw geometry.',
        '', '| Parity reference | Rows / rooms | Target | Reviewed guard | Gap | Gate |',
        '|---|---:|---:|---:|---:|---|']
    for r in result['parity']:
        lines.append(f"| {r['key']} | {r['rows']} / {r['rooms']} | {r['expected']:.2f} | {r['observed']:.4f} | {r['delta']:+.4f} | {'PASS' if r['passed'] else 'FAIL'} |")
    lines += ['', 'The corrected-label SHA256 is `d781ac7bf2313a3942020c17f3c0858eab4fbe4a349627e553d2c328da74f8c4`.',
              'Both train arms contain the same 1,037 rows / 192 rooms. Train selector scores are in-sample.',
              'The 1,012 decision-row set is validated as a subset; it is not substituted for the parity population.',
              '', '| Guard audit | Box-ladder source | Reviewed guard | Affected rows | Removed score sum |',
              '|---|---:|---:|---:|---:|']
    for r in result['guard_attribution']:
        lines.append(f"| {r['cell']} | {r['original']:.4f} | {r['reviewed']:.4f} | {r['affected_rows']} | {r['removed_score_sum']:.2f} |")
    lines += ['', 'The affected captures are `scannetpp/0f69aefe3d` (2 rows) and `scannetpp/2c7c10379b` (10 rows).',
        'E3 records `reference_camera_up_opposes_gravity`; the ladder records `reviewed_guard_refused=true` while retaining answers.',
        'The reader contract removes the terminal up-axis check. The reviewed guard retains its capture-level convention check.',
        'The resulting train gaps exceed 0.2 before any mixed geometry is evaluated. Refused rows stay in the denominator.',
        '', '| Parity reference, reviewed guard | All | ARKit | ScanNet/ScanNet++ |',
        '|---|---:|---:|---:|']
    for key, table in result['parity_tables'].items():
        lines.append('| '+key+' | '+' | '.join(fmt(table[d]) for d in ['all','arkitscenes','scannet_scannetpp'])+' |')
    lines += ['','Scores are MRA ×100 with 95% room-bootstrap intervals, 10,000 draws, seed 20261120.',
        'K1X.json also separates ScanNet and ScanNet++. No paired ablation contrast was computed.',
        '', '| Masks | Depth | Relative pose | Scale | Held-out / train / dataset cells |',
        '|---|---|---|---|---|']
    for cell in result['registered_cells']:
        lines.append('| '+' | '.join(cell[k] for k in ['masks','depth','relative_pose','scale'])+' | NOT RUN: parity stop |')
    lines += ['', 'C1, C3, the full arm-B gate, C5, C6, Pi3X and DA3: WITHHELD; parity failed.',
        'Own-depth, oracle extent/centre, voted GT box, AbsRel, pose errors and same-frame share: NOT RUN.',
        'Scale matching and synthetic geometry-swap tests: NOT IMPLEMENTED after the parity stop.',
        '', 'The tests check unchanged copied declarations, scorer parity, strict thresholds, guard behavior,',
        'room bootstrap behavior, source per-item scores, row-set identity, and the exact guard attribution.',
        'They do not establish raw-geometry replay parity or a working factorial evaluator.',
        '', 'What might not work: the E3 and ladder also use different lifting/box rules; their numbers do not define one fixed program.',
        'The restored refused-capture folders lack the geometry and cache receipt files listed in K1X.json.',
        'A complete K1-X run requires a consistent program/guard contract and parity targets for that contract.',
        'The current implementation intentionally ends at the failed gate and cannot execute the downstream cells.',
        'No heavy raster pass ran. The pending heavy-I/O approval is not needed for this saved-prediction audit.',
        '', 'Run: `nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B k1x.py run` (exit 2 means registered parity stop).',
        'Tests: `nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B k1x.py test`.',
        'Files: `k1x.py`, `tests/test_k1x.py`, `vendor/COPIES.json`, `out/K1X.json`, `out/REPORT_R2.md`, `out/SHA256SUMS`.'
    ]
    assert len(lines) <= 100
    return '\n'.join(lines)+'\n'


def checksums(out):
    paths = [ROOT/'k1x.py', ROOT/'tests/test_k1x.py', *sorted((ROOT/'vendor').glob('*')),
             out/'K1X.json',out/'REPORT_R2.md']
    if (out/'TESTS.json').exists():
        paths.append(out/'TESTS.json')
    (out/'SHA256SUMS').write_text(''.join(
        f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT)}\n' for p in paths if p.is_file()))


def main():
    args=options()
    if not args.out.resolve().is_relative_to(ROOT):
        raise ValueError('Output must stay inside r2')
    args.out.mkdir(parents=True,exist_ok=True)
    if args.command=='test':
        import unittest
        sys.path.insert(0,str(ROOT))
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
        outcome=unittest.TextTestRunner(verbosity=2).run(suite)
        result=dict(tests=outcome.testsRun,failures=len(outcome.failures),errors=len(outcome.errors),
                    skipped=len(outcome.skipped),passed=outcome.wasSuccessful(),
                    scope='Parity audit only; raw geometry and factorial endpoint tests not implemented')
        (args.out/'TESTS.json').write_text(json.dumps(result,indent=2)+'\n')
        checksums(args.out)
        return 0 if outcome.wasSuccessful() else 1
    result=audit(args)
    (args.out/'K1X.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    (args.out/'REPORT_R2.md').write_text(report(result))
    checksums(args.out)
    print(json.dumps(dict(status=result['status'],parity=result['parity']),indent=2),flush=True)
    return 2


if __name__=='__main__':
    raise SystemExit(main())
