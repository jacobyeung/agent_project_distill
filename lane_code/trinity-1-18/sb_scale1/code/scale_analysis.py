"""Frozen, training-only camera displacement experiment. CPU; no model forward."""
import os
for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '8'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import sys
sys.dont_write_bytecode = True
import ast
import hashlib
import io
import json
import math
import time
from pathlib import Path
from collections import defaultdict
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'out'
MANIFEST = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json')
HARNESS = Path('/scratch/jjyeung/orch_n30/e3_geom/work/harness/harness.py')
CAMERA = Path('/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872/student_pilot/camera_targets.py')
RULE = Path('/scratch/jjyeung/orch_n30/sb_records/work/policy_tree/student_pilot/tower_scale_rule.json')
RULE_CODE = RULE.with_suffix('.py')
ART544 = Path('/scratch/jjyeung/orch_cd/evalx/inbox/20261114T141906Z_cp2_m544_artifact.json')
ART400 = Path('/scratch/jjyeung/orch_n30/cont_ops20_b/hd400/in/A10b_export.json')
BOUNDARY = Path('/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit/boundaries.py')
K1 = Path('/scratch/jjyeung/k1')
TIMINGS = defaultdict(float)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')

def reuse(path, names):
    """Compile exact named functions; avoid importing harness startup and write hook."""
    tree = ast.parse(path.read_text(), filename=str(path))
    body = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in body} == set(names)
    exec(compile(ast.Module(body=body, type_ignores=[]), str(path), 'exec'), globals())

reuse(HARNESS, ['load_capture', 'mra'])
reuse(CAMERA, ['rotation_from_xyzw', 'gravity_reference_rotation', 'to_gravity_reference_frame'])
reuse(RULE_CODE, ['estimate'])

def refuse_scores(directory):
    for pattern in ('SCALE_RESULT.json', 'PAIR_SCORES.npz', 'ROOM_SCORES.json', 'CAPTURE_SCORES.json'):
        if (directory / pattern).exists():
            raise RuntimeError('Refuse scoring/freeze: score file exists: '+pattern)

def split_rooms(rooms):
    ordered = np.array(sorted(set(rooms)))
    np.random.default_rng(17).shuffle(ordered)
    n = len(ordered)//2
    return [sorted(ordered[:n].tolist()), sorted(ordered[n:].tolist())]

def training():
    # The combined manifest is read only to select train and bind capture digests.
    # No item row is evaluated; payload files are opened only after this filter.
    return [c for c in read(MANIFEST)['captures'] if c['k1_split'] == 'train']

def freeze():
    refuse_scores(OUT)
    if (OUT/'BARS_FROZEN.json').exists():
        raise RuntimeError('Bars already frozen; will not overwrite')
    cs = training()
    provenance = {str(p): sha(p) for p in [Path(__file__), ROOT/'code/test_scale.py', MANIFEST, HARNESS, CAMERA, RULE, RULE_CODE, ART544, ART400, BOUNDARY]}
    assert read(ART544)['step'] == 544 and read(ART400)['step'] == 400
    captures = []
    sets = defaultdict(lambda: dict(train_captures=0, checkpoint_manifests={}))
    for c in cs:
        key = digest(c['canonical'])[:16]
        record = dict(canonical=c['canonical'], room=c['room'], k1_split='train', key=key,
                      capture_sha256=digest(c), gt=c.get('gt'), anchor_indices=c['anchor_indices'])
        record['gt_present'] = bool(c.get('gt') and Path(c['gt']['path']).is_file())
        for name, root, receipt_name, payload in [
            ('tower', K1/'run_tower_sam_2', 'PHASE_COMPLETE.json', 'tower.npz'),
            ('own544', K1/'own_170235/native/probe', 'PHASE_COMPLETE.json', 'own.npz'),
            ('own_canary544', Path('/scratch/jjyeung/orch_n30/k1_ops3/work/own7/canary/native/probe'), 'PHASE_COMPLETE.json', 'own.npz'),
            ('convert1', K1/'run_convert_1', 'CACHE_COMPLETE.json', 'geometry.npz'),
            ('convert2', K1/'run_convert_2', 'CACHE_COMPLETE.json', 'geometry.npz')]:
            p = root/key/receipt_name
            if not p.exists():
                record[name] = dict(status='MISSING', expected=str(p))
                continue
            r = read(p)
            assert r['capture_sha256'] == digest(c), (name, c['canonical'])
            assert not r['synthetic']
            cp = r['checkpoint']
            assert cp['sha256'] == provenance[str(ART544)], (name, cp)
            provenance[str(p)] = sha(p)
            if payload not in r['files']:
                record[name] = dict(status='MISSING payload pin', receipt=str(p), checkpoint_step=544)
                continue
            pin = r['files'][payload]
            pin = pin['sha256'] if isinstance(pin, dict) else pin
            record[name] = dict(path=str(root/key/payload), sha256=pin, receipt=str(p), checkpoint_step=544)
            sets[str(root)]['train_captures'] += 1
            sets[str(root)]['checkpoint_manifests'][cp['path']] = cp['sha256']
        captures.append(record)
    halves = split_rooms(c['room'] for c in cs)
    bars = dict(schema='sb-scale1-bars-v1', frozen_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        input_sha256=provenance, code_sha256=sha(__file__), captures=captures,
        split_seed=17, room_halves=halves,
        folds=[dict(name='fold1', fit_rooms=halves[0], test_rooms=halves[1]),
               dict(name='fold2', fit_rooms=halves[1], test_rooms=halves[0])],
        metric='100 * mean over rooms of mean over eligible pairs in each room of mean[abs(pred-gt)/gt < 1-theta]',
        thresholds=[x/100 for x in range(50,100,5)],
        pairs='All i<j among 32 anchors with both GT poses valid and GT displacement >=0.1 m; prompt rule, not dev-S1 generator.',
        pose='Decode G3T world-to-camera encodings to centres with harness camera_targets; Euclidean centre distances.',
        fit='Room-balanced least squares log(gt/pred): exp(mean_room(mean_pair(log(gt/pred)))); no bounds; zeros excluded only from fitting.',
        E='Per-capture zero-intercept least squares on eligible pair distance: sum(raw*gt)/sum(raw**2); GT diagnostic, not deployable or a guaranteed MRA maximum.',
        F='Same room-balanced log fit, using raw G3T and fit-half GT only; one constant per fold.',
        ratio='Pooled median of eligible pair served/GT ratios; also median of per-room pair medians.',
        bootstrap=dict(draws=10000, seed=17, confidence=.95, unit='room', paired=True,
                       fitting='Conditional on frozen fit-half coefficient; no refit within bootstrap',
                       combined='Out-of-fold room records, each room scored once'),
        decision_rule='Improvement supported only if paired 95% CI lower bound >0 in both folds and combined; harm if upper bound <0; otherwise inconclusive. Q2 step544 beats400 iff B-A upper bound <0 in both folds and combined. Missing arm => MISSING.',
        missing_policy='No imputations; list every unavailable GT/own capture. Each paired contrast uses identical pairs/rooms. E/F use all locally available training GT.',
        arms=dict(A='G3T x own544 rule scale', B='MISSING: step400 own depth', C='c_A x A', D='MISSING: c_B x B', E='G3T x GT per-capture LS scale', F='G3T x global fit-half constant'),
        own_depth_sets=dict(sets), step400=dict(status='MISSING', artifact_sha256=read(ART400)['artifact']['sha256'], expected_export=read(ART400)['object']))
    dump(OUT/'BARS_FROZEN.json', bars)
    (ROOT/'STATUS.md').write_text('The bars are frozen before displacement scoring. The split assigns '+str(len(halves[0]))+' and '+str(len(halves[1]))+' training rooms to swapped folds. The analysis uses room-balanced log calibration, paired room bootstrap intervals, verified step-544 cache receipts, and explicit missing-input records. No step-400 K1 depth predictions are available in the inspected locations.\n')
    print('FROZEN', len(captures), 'captures;', [len(x) for x in halves], 'rooms;', dict(sets), flush=True)

def interval(values):
    a = np.asarray(values, float)
    rng = np.random.default_rng(17)
    samples = np.mean(a[rng.integers(0, len(a), size=(10000,len(a)))], axis=1)
    return [float(x) for x in np.quantile(samples, [.025,.975])]

def pair_scores(pred, gt):
    rel = np.abs(pred-gt)/gt
    return np.mean(rel[:,None] < np.array([(100-t)/100 for t in range(50,100,5)])[None,:], axis=1)*100

def fit(records, rooms, arm):
    byroom = defaultdict(list)
    for r in records:
        if r['room'] not in rooms or arm not in r['pred']:
            continue
        pred = r['pred'][arm]
        valid = np.isfinite(pred) & (pred > 0)
        byroom[r['room']].extend(np.log(r['gt'][valid]/pred[valid]).tolist())
    return float(np.exp(np.mean([np.mean(v) for v in byroom.values()])))

def summarize(records):
    byroom = defaultdict(list)
    ratios = defaultdict(list)
    for r in records:
        for arm, p in r['pred'].items():
            byroom[(arm,r['room'])].extend(pair_scores(p,r['gt']).tolist())
            ratios[(arm,r['room'])].extend((p/r['gt']).tolist())
    roomrows = {arm:{room:float(np.mean(v)) for (a,room),v in byroom.items() if a==arm} for arm in 'ACEF'}
    out = {}
    for arm in 'ABCDEF':
        if arm not in roomrows or not roomrows[arm]:
            out[arm] = dict(status='MISSING')
            continue
        vals = [roomrows[arm][room] for room in sorted(roomrows[arm])]
        rr = [v for (a,room),v in ratios.items() if a==arm]
        out[arm] = dict(status='OK', mra=float(np.mean(vals)), ci95=interval(vals), rooms=len(vals),
                        pairs=sum(len(v) for v in rr), median_ratio=float(np.median(np.concatenate(rr))),
                        median_room_ratio=float(np.median([np.median(v) for v in rr])))
    diff = {}
    for name,left,right in [('B-A','B','A'),('C-A','C','A'),('D-B','D','B')]:
        if left not in roomrows or right not in roomrows:
            diff[name] = dict(status='MISSING')
            continue
        rooms = sorted(set(roomrows[left]) & set(roomrows[right]))
        # C and A are created together on the same capture/pair population.
        vals = [roomrows[left][r]-roomrows[right][r] for r in rooms]
        diff[name] = dict(status='OK', points=float(np.mean(vals)), ci95=interval(vals), rooms=len(rooms))
    return dict(arms=out, paired_differences=diff), roomrows

def score():
    refuse_scores(OUT)
    bars = read(OUT/'BARS_FROZEN.json')
    assert bars['code_sha256'] == sha(__file__), 'Code changed after freeze'
    for p, h in bars['input_sha256'].items():
        assert sha(p) == h, 'Changed input '+p
    cs = {c['canonical']:c for c in training()}
    records, capture_rows, missing = [], [], []
    pins = dict(bars['input_sha256'])
    pins[str(OUT/'BARS_FROZEN.json')] = sha(OUT/'BARS_FROZEN.json')
    start = time.monotonic()
    for n, r in enumerate(bars['captures']):
        c = cs[r['canonical']]
        assert c['k1_split']=='train' and digest(c)==r['capture_sha256']
        if not r['gt_present']:
            missing.append(dict(capture=c['canonical'], reason='GT archive MISSING', expected=c['gt']))
            continue
        folder = Path(r['tower']['path']).parent
        receipt = read(r['tower']['receipt'])
        assert sha(r['tower']['path']) == r['tower']['sha256']
        pins[r['tower']['path']] = r['tower']['sha256']
        gt,tower,hw = load_capture(c,(folder,receipt),False)
        pins[c['gt']['path']] = c['gt']['sha256']
        _, centres, _ = to_gravity_reference_frame(tower['raw_pose'][tower['anchor_slots']], [0.,-1.,0.])
        i,j = np.triu_indices(32,1)
        truth = np.linalg.norm(gt['c2w'][i,:3,3]-gt['c2w'][j,:3,3],axis=1)
        valid = gt['valid'][i].astype(bool) & gt['valid'][j].astype(bool) & np.isfinite(truth) & (truth>=.1)
        raw = np.linalg.norm(centres[i]-centres[j],axis=1)[valid]
        truth = truth[valid]
        if not len(truth):
            missing.append(dict(capture=c['canonical'], reason='No valid eligible GT pairs'))
            continue
        assert np.isfinite(raw).all() and np.dot(raw,raw)>0
        oracle = float(np.dot(raw,truth)/np.dot(raw,raw))
        pred = dict(raw=raw,E=raw*oracle)
        row = dict(capture=c['canonical'],room=c['room'],pairs=len(truth),scale_E=oracle)
        if 'path' in r['own544']:
            own = r['own544']
            assert sha(own['path']) == own['sha256']
            pins[own['path']] = own['sha256']
            with np.load(own['path'],allow_pickle=False) as z:
                depth=z['depth']
            scale,mask,threshold = estimate(tower['depth_grid'],tower['depth_conf_grid'],depth)
            pred['A'] = raw*scale
            row.update(scale_A=scale, scale_points=int(mask.sum()))
        else:
            missing.append(dict(capture=c['canonical'],reason='own544 MISSING',expected=r['own544']['expected']))
        records.append(dict(capture=c['canonical'],room=c['room'],gt=truth,pred=pred))
        capture_rows.append(row)
        if (n+1)%30==0:
            print('Loaded',n+1,'training captures',flush=True)
    folds, outfold = [], []
    for fold in bars['folds']:
        fitrooms=set(fold['fit_rooms']); testrooms=set(fold['test_rooms'])
        assert not fitrooms & testrooms
        ca=fit(records,fitrooms,'A'); cf=fit(records,fitrooms,'raw')
        test=[]
        for r in records:
            if r['room'] not in testrooms:
                continue
            pred={k:v for k,v in r['pred'].items() if k!='raw'}
            pred['F']=r['pred']['raw']*cf
            if 'A' in pred:
                pred['C']=pred['A']*ca
            test.append(dict(capture=r['capture'],room=r['room'],gt=r['gt'],pred=pred))
        summary, roomrows=summarize(test)
        folds.append(dict(name=fold['name'],fit_rooms=len(fitrooms),test_rooms=len(testrooms),
                          coefficients=dict(C=ca,D='MISSING',F=cf),**summary))
        outfold.extend(test)
    combined, rooms=summarize(outfold)
    result=dict(schema='sb-scale1-result-v1',input_sha256=pins,code_sha256=sha(__file__),
                command='env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python code/scale_analysis.py score',
                captures=len(records),rooms=len(set(r['room'] for r in records)),pairs=sum(len(r['gt']) for r in records),
                missing=missing, folds=folds,combined=combined,elapsed_seconds=time.monotonic()-start,
                Q2='MISSING: step400 K1 own depth; no paired B-A or D-B claim',
                scope='K1 train only; manifest split/identity metadata read, no held-out payload or scored item rows opened')
    ci=[f['paired_differences']['C-A']['ci95'] for f in folds]+[combined['paired_differences']['C-A']['ci95']]
    result['Q1']='SUPPORTED' if all(x[0]>0 for x in ci) else ('HARM' if all(x[1]<0 for x in ci) else 'INCONCLUSIVE')
    dump(OUT/'CAPTURE_SCORES.json',dict(input_sha256=pins,captures=capture_rows))
    dump(OUT/'ROOM_SCORES.json',dict(input_sha256=pins,rooms=rooms))
    dump(OUT/'SCALE_RESULT.json',result)
    (ROOT/'STATUS.md').write_text(f'The CPU scoring stage completed on {len(records)} training captures. Both swapped folds and the out-of-fold aggregate include A, C, E, and F, with paired C-A room bootstrap intervals. Step-400 arms and contrasts are MISSING. The result records every verified input hash and all missing captures; report generation and final validation remain.\n')
    print(json.dumps(dict(folds=folds,combined=combined,Q1=result['Q1']),indent=2),flush=True)

if __name__=='__main__':
    {'freeze':freeze,'score':score}[sys.argv[1]]()
