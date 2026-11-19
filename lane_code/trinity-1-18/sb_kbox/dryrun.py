"""Run available CPU checks and fail closed when an all-arm prerequisite is missing."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import resource
import time
import traceback
import numpy as np
from adapters import ROOT, TREE, dependencies, reviewed_loader, source_hashes
from box_math import FUSIONS, CONSTANTS, fusion_box, gather, paired_bootstrap, mra
from pricing import lift_frames, session_distance, object_diagnostics

OUT = ROOT/'out/box_ladder'
PINS = {}


def read(path):
    p = Path(path)
    if not p.resolve().is_relative_to('/scratch'):
        raise PermissionError('Local input required: '+str(p))
    b = p.read_bytes()
    PINS[str(p)] = hashlib.sha256(b).hexdigest()
    return b


def clean(v):
    if isinstance(v, np.ndarray):
        return clean(v.tolist())
    if isinstance(v, np.generic):
        return clean(v.item())
    if isinstance(v, dict):
        return {str(k): clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [clean(x) for x in v]
    if isinstance(v, float) and not np.isfinite(v):
        return None
    return v


def write(path, obj):
    path.write_text(json.dumps(clean(dict(obj, input_sha256=dict(PINS))), indent=2, allow_nan=False)+'\n')


def fixed_tests(G):
    from types import SimpleNamespace as NS
    rng = np.random.default_rng(20261119)
    p = rng.normal(size=(50, 3))
    reference = G.min_area_box(p)
    equal = {rule: all(np.array_equal(v, fusion_box({3:p}, 3, rule, G.min_area_box)[k]) for k, v in reference.items()) for rule in FUSIONS}
    def proposal(frame, index, voxels, score=.8):
        return NS(frame=frame, index=index, score=score, voxels=frozenset(voxels))
    seed = proposal(1, 0, [0])
    # Frame 3 becomes eligible only after frame 2 joins; frame 2 has a competitor.
    result = gather([seed], [proposal(2,1,[0,1,2,3]), proposal(2,0,[0,9]), proposal(3,0,[9,10])])
    rows = [dict(row_id=str(i), room=str(i//2), prediction=1., label=1.) for i in range(6)]
    boot = paired_bootstrap(rows, rows)
    return dict(single_member_fusion=equal, gather_fixed_point=[(p.frame,p.index) for p in result],
                gather_pass=[(p.frame,p.index) for p in result] == [(1,0),(2,0),(3,0)],
                paired_identity_pass=boot['estimate'] == 0 and boot['ci95'] == [0,0])


def main():
    start = time.monotonic()
    h, l, G = dependencies()
    loader, guard, recorder = reviewed_loader()
    from student_pilot.scene_state import FrameMap
    from student_pilot.ground_profiles import load_geometry
    tests = fixed_tests(G)
    manifest = json.loads(read(ROOT/'train_manifest.json'))
    label_data = json.loads(read(ROOT/'train_labels.json'))
    PINS.update(manifest['input_sha256']); PINS.update(label_data['input_sha256'])
    labels = {r['id']:r for r in label_data['rows']}
    captures = manifest['captures']
    assert all(c['k1_split']=='train' for c in captures)
    selected = [next(c for c in captures if c['canonical'].startswith(ds+'/') and
                 any(r['type']=='object_abs_distance' for r in c['rows'])) for ds in ('arkitscenes','scannetpp')]
    missing = [c['gt']['path'] for c in captures if c.get('gt') and not Path(c['gt']['path']).is_file()]
    metrics, items, parity = [], [], []
    dependencies_missing = [n for n in ('torch','safetensors') if importlib.util.find_spec(n) is None]
    for c in selected:
        t0 = time.monotonic(); canonical = c['canonical']; slug = canonical.replace('/','__')
        print('CAPTURE_START', canonical, flush=True)
        rows = [r for r in c['rows'] if r['type']=='object_abs_distance']
        key = h.digest(canonical)[:16]
        folder = Path('/scratch/jjyeung/k1/run_tower_sam_2')/key
        gtbytes = read(c['gt']['path'])
        assert hashlib.sha256(gtbytes).hexdigest() == c['gt']['sha256']
        with np.load(io.BytesIO(gtbytes), allow_pickle=False) as z:
            gt = {k:z[k] for k in ('depth','K','K_frames','c2w','valid','frame_indices','inst')}
        del gtbytes
        with np.load(io.BytesIO(read(folder/'tower.npz')), allow_pickle=False) as z:
            tower = {k:z[k] for k in ('raw_pose','depth_grid','depth_conf_grid','frame_indices','anchor_slots','grid_uv')}
        receipt = json.loads(read(folder/'PHASE_COMPLETE.json'))
        assert np.array_equal(gt['frame_indices'],c['anchor_indices'])
        assert np.array_equal(tower['frame_indices'][tower['anchor_slots']],c['anchor_indices'])
        stored_path = Path('/scratch/jjyeung/orch_n30/b04host3/lift_price/harness/out_lift_train_v2')/(slug+'.json')
        stored = json.loads(read(stored_path))
        reference = {r['row_id']:r for r in stored['items'] if r['arm']=='S4+G1+bestspread'}
        g1 = h.gravities(tower,gt)['G1']
        reggeo = h.geometry_npz(c,tower,receipt['source_hw'],g1,stored['scales']['S4'],'dry_reference')
        for r in rows:
            got = h.item(c,r,'S4+G1+bestspread',h.attempt(lambda:l.reader_distance(r,reggeo,gt,l.lift_bestspread)))
            parity.append(dict(capture=canonical,row_id=r['id'],passed=got==reference[r['id']],got=got,expected=reference[r['id']]))
        gdpath = Path('/scratch/jjyeung/k1/run_convert_2')/key/'geometry.npz'
        read(gdpath)
        with guard.capture('K1_dry_GD',canonical):
            gd = loader(gdpath,FrameMap(tuple(c['anchor_indices'])),'tower_scaled')
        gtgeo = h.GTGeometry(gt)
        # frame_count() needs the camera-array alias; GT lifting stays unchanged.
        gtgeo.C = gtgeo.c2w
        geos = [('GD',gd),('GT',gtgeo)]
        for name in ('da3','pi3x'):
            path = Path('/scratch/jjyeung/orch_n30/geo_k1/geom')/(name+'_native')/(slug+'.npz')
            if not path.is_file():
                missing.append(str(path)); continue
            read(path)
            try:
                with guard.capture('K1_dry_'+name,canonical):
                    geo = loader(path,FrameMap(tuple(c['anchor_indices'])),'tower_scaled')
                geos.append((name,geo))
            except ValueError as exc:
                metrics.append(dict(capture=canonical,geometry=name,status='REFUSED',reason=str(exc)))
        for geom, geo in geos:
            print('GEOMETRY',canonical,geom,flush=True)
            cache = {}
            for row in rows:
                lifted, plain, masks = {}, {}, {}
                for name in row['operands']:
                    iid = row['gt_instances'][name]
                    if iid not in cache:
                        m = (gt['inst']==iid) & gt['valid'].astype(bool)[:,None,None]
                        spread = lift_frames(name,m,geo,G)
                        p = G.lift_plain(name,m,geo) if geom=='GT' else None
                        cache[iid] = (m,spread,p)
                    m,spread,p = cache[iid]
                    masks[name]=m; lifted[name]=dict(spread,name=name)
                    if p is not None: plain[name]=dict(p,name=name)
                rules = [('best1',False),('plain',True)] if geom=='GT' else [(rule,False) for rule in FUSIONS]
                for rule, use_plain in rules:
                    arm = ('A2_gt_masks' if rule=='best1' else 'A3_gt_fused_'+rule) if geom=='GD' else (
                           'A6_gtgeo_'+('fused' if use_plain else 'single') if geom=='GT' else 'DRY_A7_'+geom+'_'+rule)
                    try:
                        pred,refusal,raw,printed = session_distance(row,geo,plain if use_plain else lifted,G,rule='best1' if use_plain else rule,plain=use_plain)
                        status='OK'
                    except (ValueError,MemoryError) as exc:
                        pred=None;refusal=type(exc).__name__+':'+str(exc);raw={};printed={};status='ERROR'
                    label=labels.get(row['id'])
                    if label is None:
                        missing.append('corrected_label:'+row['id'])
                    items.append(dict(stage='dry_run',status=status,arm=arm,row_id=row['id'],room=c['room'],capture=canonical,
                        split='train',dataset=canonical.split('/')[0],prediction=pred,label=None if label is None else label['corrected'],
                        refusal_code=refusal,member_frames={n:lifted[n]['frames'] for n in lifted},box=printed,
                        diagnostics={n:object_diagnostics(masks[n],lifted[n],printed.get(n)) for n in lifted}))
                if geom=='GD':
                    for name in row['operands']:
                        single=next((f for f,p in lifted[name]['points'].items() if len(p)>=4),None)
                        if single is not None:
                            points={single:lifted[name]['points'][single]}
                            try:
                                boxes={r:fusion_box(points,int(single),r,G.min_area_box) for r in FUSIONS}
                                tests.setdefault('real_single_frame',[]).append(all(all(np.array_equal(b[k],boxes['best1'][k]) for k in b) for b in boxes.values()))
                            except ValueError:
                                pass
            metrics.append(dict(capture=canonical,geometry=geom,status='RAN',seconds=time.monotonic()-t0))
        print('CAPTURE_DONE',canonical,round(time.monotonic()-t0,3),flush=True)
    PINS.update(source_hashes())
    # Include dynamically loaded reference code, which is not registered in sys.modules.
    for path in [Path(h.programs.REFERENCE),Path(h.programs.T.__file__)]:
        read(path)
    with (OUT/'PER_ITEM.jsonl').open('w') as f:
        for item in items:
            item['input_sha256']=dict(PINS)
            f.write(json.dumps(clean(item),allow_nan=False)+'\n')
    tests['reference_row_equality']=dict(passed=all(r['passed'] for r in parity),matched=sum(r['passed'] for r in parity),total=len(parity))
    tests['gtgeo_fused']=dict(ran=sum(r['arm']=='A6_gtgeo_fused' for r in items),
        answered=sum(r['arm']=='A6_gtgeo_fused' and r['prediction'] is not None for r in items))
    tests['stage1_replay']=dict(status='MISSING',reason='Required interpreter dependencies missing: '+', '.join(dependencies_missing),matched=None,total=None,rate=None)
    tests['heldout_stage1_replay']=dict(status='DEFERRED',reason='Task requires train decision first; specification also requires prior reviewer code read.')
    tests['A0_deployed_row_reproduction']=dict(status='MISSING',reason='StageOne cannot import without torch; GT parity is not A0 parity.')
    result=dict(status='BLOCKED',passed=False,scope='two train captures; available geometry arms only',
        tests=tests,missing_inputs=sorted(set(missing)),missing_python_modules=dependencies_missing,
        captures=[c['canonical'] for c in selected],metrics=metrics,constants=CONSTANTS,
        full_train_started=False,heldout_evaluated=False,
        seconds=time.monotonic()-start,peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
    write(ROOT/'out/DRYRUN.json',result)
    write(OUT/'DRYRUN_PARITY.json',dict(rows=parity))
    print(json.dumps(clean(result),allow_nan=False),flush=True)
    (ROOT/'STATUS.md').write_text('Stage 4: Completed available two-capture CPU dry-run checks. The all-arm gate is BLOCKED because the specified interpreter lacks torch and safetensors; StageOne replay and A0 parity are unverified. No full train or held-out pass ran. Detailed checks, timing, and memory are in out/DRYRUN.json.\n')


if __name__=='__main__':
    main()
