"""Validate output contracts without reopening evaluation payloads."""
import os
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'): os.environ[k]='8'
import sys
sys.dont_write_bytecode=True
import json,hashlib,subprocess
from pathlib import Path
import numpy as np
import scale_drift as a
ROOT=a.ROOT; OUT=a.OUT
checks=[]
def check(name,condition,details=None):
    checks.append(dict(test=name,passed=bool(condition),details=details))
    if not condition: raise AssertionError(name)
def main():
    b=a.read(OUT/'BARS_FROZEN.json'); r=a.read(OUT/'ITEMS12.json'); f=a.read(OUT/'SCALE_DRIFT.json')
    base=a.read(a.BASE/'out/BARS_FROZEN.json')
    check('exact_sb_scale1_folds',b['folds']==base['folds'] and b['room_halves']==base['room_halves'])
    original=a.read(OUT/'BARS_FROZEN_pre_refusal_fix.json')
    check('implementation_fix_preserves_rules',all(original[k]==b[k] for k in ('folds','room_halves','metrics','fit','dataset_fit','calibration_transfer','arms','bootstrap','decisions','missing_policy')))
    check('frozen_code_hash',b['code_sha256']==a.sha(ROOT/'code/scale_drift.py'))
    check('room_disjoint',all(not set(x['fit_rooms'])&set(x['test_rooms']) for x in b['folds']))
    for fold,fit in zip(b['folds'],r['displacement']['fit_audit']):
        fitrooms=set(fold['fit_rooms']); testrooms=set(fold['test_rooms'])
        check(fold['name']+'_fit_only',set(fit['global_fit_rooms'])<=fitrooms)
        for ds,rooms in fit['dataset_fit_rooms'].items():
            check(fold['name']+'_'+ds+'_fit_isolation',set(rooms)<=fitrooms and not set(rooms)&testrooms)
    check('baseline_reproduced',abs(r['displacement']['combined']['all']['arms']['A']['mra']-83.800)<.001)
    check('global_reproduced',abs(r['displacement']['combined']['all']['paired_differences']['G-A']['points']-.153)<.001)
    rows=a.read(OUT/'DISTANCE_ROWS.json')['rows']; by={}
    for arm in ('A','G','D'): by[arm]={(v['capture'],v['row_id']) for v in rows if v['arm']==arm}
    check('distance_positive_GT',all(v['gt']>0 for v in rows))
    check('distance_same_rows_all_arms',by['A']==by['G']==by['D'],len(by['A']))
    check('distance_refusal_records',all(v['refusal'] is not None for v in rows if v['pred'] is None))
    for kind,w in [('displacement',.2),('distance',.125)]:
        check(kind+'_conversion',all(abs(v['benchmark_contribution_delta']['points']-v['paired_vs_A']['points']*w)<1e-12 for arm in f['prices'].values() for v in arm[kind]))
    check('only_train_capture_pins',all(v['k1_split']=='train' for v in b['captures']))
    check('no_source_mapping_invented',all(v['dataset_mapping'].startswith('MISSING') for v in r['pose_stream']['sources'].values()))
    try: a.refuse()
    except RuntimeError: refused=True
    else: refused=False
    check('production_score_refusal',refused)
    # The actual scorer must refuse before opening any evaluation input.
    result=subprocess.run([sys.executable,'-B',str(ROOT/'code/scale_drift.py'),'score'],capture_output=True,text=True)
    check('entrypoint_refuses_existing_scores',result.returncode!=0 and 'Refuse scoring/freeze: score file exists' in result.stderr)
    freeze_result=subprocess.run([sys.executable,'-B',str(ROOT/'code/scale_drift.py'),'freeze'],capture_output=True,text=True)
    check('freeze_refuses_existing_scores',freeze_result.returncode!=0 and 'Refuse scoring/freeze: score file exists' in freeze_result.stderr)
    # Check an exported geometry for every dataset: the loader scales exactly once.
    caps=a.read(OUT/'CAPTURE_SCORES.json')['captures']
    geometry_inputs=[]
    for ds in ('arkitscenes','scannet','scannetpp'):
        for c in [c for c in caps if c['dataset']==ds]:
            path=OUT/'geometry'/c['capture'].replace('/','__')/'A.npz'
            if not path.exists(): continue
            geometry_inputs.append(path)
            with np.load(path,allow_pickle=False) as z:
                rawdepth=z['depth_grid']; rawC=z['camera_to_world']; sc=float(z['scale']); anchors=z['anchor_frame_indices']
            try: geo=a.load_geometry(path,a.FrameMap(tuple(map(int,anchors))),'tower_scaled')
            except ValueError: continue
            check(ds+'_scale_once',geo.depth_scale_count==1 and geo.pose_scale_count==1 and np.allclose(geo.depth_grid,rawdepth*sc) and np.allclose(geo.C[:,:3,3],rawC[:,:3,3]*sc))
            break
        else: raise AssertionError('No valid geometry for '+ds)
    resource_text=(OUT/'resources.log').read_text()
    peak=int(next(line.split(':',1)[1] for line in resource_text.splitlines() if 'Maximum resident set size' in line))
    check('peak_memory_below_40_GB',peak < 40*1024*1024,dict(peak_KiB=peak))
    paths=[ROOT/'code/validate_outputs.py',ROOT/'code/test_scale_drift.py',OUT/'BARS_FROZEN.json',OUT/'ITEMS12.json',OUT/'ITEMS12.md',OUT/'SCALE_DRIFT.json',OUT/'SCALE_DRIFT_REPORT.md',OUT/'CAPTURE_SCORES.json',OUT/'DISTANCE_ROWS.json',OUT/'resources.log',OUT/'tests.log']
    paths.extend(geometry_inputs+[a.BASE/'out/BARS_FROZEN.json',OUT/'BARS_FROZEN_pre_refusal_fix.json'])
    pins={**r['input_sha256'],**{str(p):a.sha(p) for p in paths}}
    a.dump(OUT/'VALIDATION.json',dict(input_sha256=pins,command='env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B code/validate_outputs.py',checks=checks))
    (ROOT/'STATUS.md').write_text('All requested deliverables are complete: ITEMS12.md/JSON and SCALE_DRIFT_REPORT.md/SCALE_DRIFT.json. Validation passed for exact sb_scale1 folds, fit-room isolation, baseline reproduction, matched distance rows, benchmark conversion, one scale application, input provenance and refusal to score over existing outputs. Step400 and source-removal prices remain explicitly MISSING with the required tests and GPU-hour estimates.\n')
    print('PASS',len(checks),'checks')
if __name__=='__main__': main()
