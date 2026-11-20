"""CPU-only audit of saved tower diagnostics; no inference or GT-derived flags."""
import os
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[name] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import json, hashlib, time, resource
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
from gpkg.capture_io import Records
from orchard_tower2x_c.score import relative

ROOT = Path(__file__).resolve().parent
CAP = ROOT.parent / 'cap'
OUT = CAP / 'score_conf'
START = time.monotonic()
resource.setrlimit(resource.RLIMIT_AS, (18*1024**3, 18*1024**3))
PINS = {}

def read(path):
    path = Path(path)
    raw = path.read_bytes()
    PINS[str(path)] = hashlib.sha256(raw).hexdigest()
    return json.loads(raw)

def stats(value):
    a = np.asarray(value, float)
    assert a.size and np.isfinite(a).all()
    return dict(n=int(a.size), mean=float(a.mean()), min=float(a.min()), max=float(a.max()),
                std=float(a.std()), range=float(np.ptp(a)), rms=float(np.sqrt(np.mean(a*a))))

def angles(r):
    return np.degrees(np.arccos(np.clip((np.trace(r, axis1=-2, axis2=-1)-1)/2, -1, 1)))

def category(row):
    f = row['rigid_fit']
    return 'pass' if f['accepted'] else 'gross' if f['rotation_max_deg'] > 60 else 'moderate'

def schemas(value, prefix='', out=None):
    out = out if out is not None else set()
    if isinstance(value, dict):
        for k,v in value.items():
            p = prefix+'.'+k if prefix else k
            out.add(p)
            schemas(v,p,out)
    elif isinstance(value,list):
        for v in value:
            if isinstance(v,dict): schemas(v,prefix+'[]',out)
    return out

def diagnostics(g, indices=None):
    c = np.asarray(g['camera_to_world_metric'],float)
    if indices is not None: c=c[indices]
    r,t = c[:,:3,:3],c[:,:3,3]
    up = r[:,2,:]  # R^T [0,0,1]; predicted gravity, not GT.
    rot = angles(r[:-1].transpose(0,2,1) @ r[1:])
    trans = np.linalg.norm(np.diff(t,axis=0),axis=1)
    d = dict(scale=stats([g['scale']]), world_gravity_norm=stats([np.linalg.norm(g['gravity_up'])]),
             camera_upright_angle_deg=stats(np.degrees(np.arccos(np.clip(-up[:,1],-1,1)))),
             consecutive_rotation_deg=stats(rot), consecutive_translation_m=stats(trans),
             translation_second_difference_m=stats(np.linalg.norm(np.diff(t,n=2,axis=0),axis=1)),
             rotation_step_change_deg=stats(np.abs(np.diff(rot))))
    for i,axis in enumerate('xyz'):
        d['world_gravity_'+axis]=stats([g['gravity_up'][i]])
        d['origin_gravity_'+axis]=stats([up[0,i]])
        d['camera_gravity_'+axis]=stats(up[:,i])
    d['origin_upright_angle_deg']=stats([np.degrees(np.arccos(np.clip(-up[0,1],-1,1)))])
    return d,c

def main():
    OUT.mkdir(exist_ok=True)
    split=read(CAP/'score_t1/CAMERA_SPLIT.json')['captures']
    rows={r['capture']:dict(capture=r['capture'], dataset=r['dataset'], classification=category(r),
        distance_items=r['items'], diagnostics={}, observations={}, series={}) for r in split}
    assert Counter(r['classification'] for r in rows.values())=={'pass':6,'moderate':22,'gross':10}
    geoms={}; inventories={}; validations={}; all_items={}
    for arm,receipt in [('t1','t1ret'),('t2','t2ret'),('dense','dret')]:
        rec=Records(CAP/(arm+'.gz'),CAP/receipt/'CAPTURE.json')
        PINS[str(CAP/(arm+'.gz'))]=rec.report['raw_sha256']
        observations=defaultdict(list); keys=set(); primary=[]; geoms[arm]={}
        for x in rec:
            schemas(x,out=keys)
            if x.get('pass_index',0)!=0 or x.get('excluded',False): continue
            primary.append((x['item_id'],x['capture']))
            if x['capture'] not in rows or not x.get('geometry'): continue
            observations[x['capture']].append((x['item_id'],x['geometry']))
        all_items[arm]=primary
        for cap in rows:
            oo=observations[cap]; assert oo
            g=oo[0][1]
            # All primary reads must carry the same geometry for capture-level averaging.
            for _,other in oo:
                for k in ('camera_to_world_metric','scale','gravity_up'):
                    assert np.array_equal(np.asarray(g[k]),np.asarray(other[k])), (arm,cap,k)
            geoms[arm][cap]=g
            slots=g.get('anchor_slots') if arm=='dense' else None
            ds,c=diagnostics(g,slots)
            rows[cap]['diagnostics'][arm]=ds
            rows[cap]['observations'][arm]=dict(primary_records=len(oo), geometry_frames=len(g['K']),
                summary_frames=len(c), item_ids=[i for i,_ in oo], across_read_scale=stats([v['scale'] for _,v in oo]))
            rows[cap]['series'][arm]=dict(predicted_up_in_camera=c[:,:3,:3][:,2,:].tolist(),
                consecutive_rotation_deg=angles(c[:-1,:3,:3].transpose(0,2,1)@c[1:,:3,:3]).tolist(),
                consecutive_translation_m=np.linalg.norm(np.diff(c[:,:3,3],axis=0),axis=1).tolist())
        inventories[arm]=sorted(keys); validations[arm]=rec.report
        assert len(primary)==150 and len(set(i for i,_ in primary))==150
    # Repeat-run disagreement is available without any GT, but needs a second tower run.
    for cap,row in rows.items():
        a=np.asarray(geoms['t1'][cap]['camera_to_world_metric'])
        b=np.asarray(geoms['t2'][cap]['camera_to_world_metric'])
        rr=relative(a,b)
        row['diagnostics']['t2_vs_t1']={k:stats(v['residuals']) for k,v in rr.items() if isinstance(v,dict)}
        dense=geoms['dense'][cap]
        dc=np.asarray(dense['camera_to_world_metric'])[dense.get('anchor_slots',list(range(32)))]
        assert np.array_equal(a,dc)
        row['diagnostics']['dense_vs_t1']={'anchor_camera_max_abs':stats([float(np.max(np.abs(a-dc)))])}
    kr=read(ROOT/'orchard_tower2x_c/returned/5.json')
    ref=read(ROOT/'orchard_tower2x_c/REFERENCE.json')
    scored=read(ROOT/'orchard_tower2x_c/returned/scored/TOWER2X_B.json')
    kmap={r['key']:r for r in ref['captures']}
    smap={r['capture']:r for r in scored['rows']}
    assert kr['complete'] and not kr['stub']
    inventories['k3d']=sorted(schemas(kr))
    for x in kr['rows']:
        rf=kmap[x['key']];cap=rf['capture'];row=rows[cap]
        for label,a in zip(('k3d_Aprime','k3d_B'),x['arms']):
            assert a['status']=='ok' and a['scale']==rf['scale'] and a['gravity']==rf['gravity']
            g=dict(camera_to_world_metric=a['c2w'],scale=a['scale'],gravity_up=[0,0,1])
            dd,c=diagnostics(g,a['slots'])
            dd['saved_origin_gravity_norm']=stats([np.linalg.norm(a['gravity'])])
            for i,axis in enumerate('xyz'):dd['saved_origin_gravity_'+axis]=stats([a['gravity'][i]])
            row['diagnostics'][label]=dd
            assert np.allclose(c[0,:3,:3].T@np.array([0,0,1]),np.array(a['gravity'])/np.linalg.norm(a['gravity']),atol=1e-7)
            rr=relative(c,np.asarray(geoms['t1'][cap]['camera_to_world_metric']))
            row['diagnostics'][label+'_vs_t1']={k:stats(v['residuals']) for k,v in rr.items() if isinstance(v,dict)}
            if label=='k3d_Aprime':
                assert abs(rr['rotation_deg']['rms']-smap[cap]['control']['relative_rotation_rms_deg'])<1e-7
            row['observations'][label]=dict(frames=len(a['ids']),summary_frames=len(c),
                raw_matches=a['raw_match_count'],raw_frames=len(a['raw_matches']), frozen_scale_and_gravity=True)
    # Attach candidate scalar scores, including all requested mean/min/spread summaries.
    feature_info={}
    for row in rows.values():
        row['features']={}
        for source,ds in row['diagnostics'].items():
            for name,ss in ds.items():
                suffixes=['mean'] if ss['n']==1 else ['mean','min','max','std','range','rms']
                for stat in suffixes:
                    key=source+'.'+name+'.'+stat
                    row['features'][key]=round(ss[stat],10)
                    feature_info[key]=dict(source=source,quantity=name,summary=stat,
                        single_read=source in ('t1','t2','dense'), direction='larger value is positive; reverse AUC also explicit')
    auc=[]
    for key in sorted(feature_info):
        for ds in ('all','arkitscenes'):
            for comparison,classes in [('gross_vs_pass',{'gross'}),('failing_vs_passing',{'gross','moderate'})]:
                pool=[r for r in rows.values() if key in r['features'] and (ds=='all' or r['dataset']==ds)]
                pos=[r['features'][key] for r in pool if r['classification'] in classes]
                neg=[r['features'][key] for r in pool if r['classification']=='pass']
                v=float(np.mean(np.array(pos)[:,None]>np.array(neg))+0.5*np.mean(np.array(pos)[:,None]==np.array(neg))) if pos and neg else None
                auc.append(dict(feature=key,dataset=ds,comparison=comparison,n_positive=len(pos),n_pass=len(neg),auc_high=v,auc_low=None if v is None else 1-v))
    cams=read(CAP/'score_cam/CAMERA_ITEMS_R8.json')['items']
    # Zero observed pass false positives is an explicit, descriptive threshold convention.
    rules=[]
    for z in auc:
        if z['comparison']!='gross_vs_pass' or z['auc_high'] is None:continue
        if max(z['auc_high'],z['auc_low'])<.9:continue
        key=z['feature'];ds=z['dataset'];sign=1 if z['auc_high']>=z['auc_low'] else -1
        available=[r for r in rows.values() if key in r['features'] and (ds=='all' or r['dataset']==ds)]
        threshold=max(sign*r['features'][key] for r in available if r['classification']=='pass')
        flagged=[r['capture'] for r in available if sign*r['features'][key]>threshold]
        unavailable=[r['capture'] for r in rows.values() if (ds=='all' or r['dataset']==ds) and key not in r['features']]
        cc=Counter(rows[c]['classification'] for c in flagged)
        distance=[i for i,c in all_items['t1'] if c in flagged]
        camera={str(step):[r['item_key'] for r in cams if r['step']==step and r['capture'] in flagged] for step in (544,400)}
        rules.append(dict(feature=key,scope=ds,operator='>' if sign==1 else '<',threshold=sign*threshold,
            selected_direction_auc=max(z['auc_high'],z['auc_low']),n_positive=z['n_positive'],n_pass=z['n_pass'],
            flagged_captures=flagged,flagged_class_counts=dict(cc),unmeasured_captures=unavailable,
            distance_items=len(distance),distance_item_ids=distance,
            camera_items={k:len(v) for k,v in camera.items()},camera_item_keys=camera,
            single_read=feature_info[key]['single_read'],threshold_convention='strictly beyond worst observed pass; sign selected descriptively',
            evidence='descriptive n=38, no held-out threshold validation; feature coverage may be smaller'))
    gtfeatures=read(CAP/'score_cam/CAPTURE_FEATURES_R8.json')
    gt_only=[r for r in gtfeatures['AUC'] if r['feature'] in ('gravity_mean_deg','gravity_max_deg') and r['dataset'] in ('all','arkitscenes')]
    result=dict(schema='tower-confidence-r10',cohort=dict(n=38,classes=dict(Counter(r['classification'] for r in rows.values())),
        arkit_classes=dict(Counter(r['classification'] for r in rows.values() if r['dataset']=='arkitscenes')),
        arkit_authority='REPORT9 classes remain conditional on unresolved native pose/RGB binding'),
        summary_definition='Population std and max-min range; scalar capture outputs have n=1. Every arm uses the same 32 anchors. Captures receive equal AUC weight. Primary repeated reads are checked identical.',
        auc_definition='P(positive>pass)+0.5 ties, values rounded to 10 decimals to avoid float noise; both high and low directions shown. No multiple-comparison correction.',
        captures=list(rows.values()),features=feature_info,AUC=auc,rules=rules,GT_only_gravity_AUC=gt_only,
        schemas=inventories,validation=validations,input_sha256=PINS,
        unavailable=dict(depth_confidence='No pixel values in any requested capture/return; n=0, AUC undefined; valid-pixel/frame averages cannot be recovered from a hash.',
            depth_reprojection='Depth grids absent; n=0, AUC undefined.',
            world_point_confidence='Computed then discarded; absent everywhere; n=0, AUC undefined.',
            pose_confidence='No confidence output in either camera head; n=0, AUC undefined.',
            own_pose_disagreement='Own pose head absent from these captures and K3d; n=0. R8 own-head logs are different camera-question reads, not paired distance-read evidence.',
            tower_vs_own_gravity='Tower gravity_up conversion result discarded; saved gravity is own-head gravity or world [0,0,1], so independent comparison unavailable.',
            tokens='Activations and LayerNorm internals are not exported; no scalar token norms recorded.'),
        runtime_seconds=time.monotonic()-START,peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    with (OUT/'CONF_R10.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(runtime=result['runtime_seconds'],rss_KiB=result['peak_rss_KiB'],features=len(feature_info),rules=len(rules),
        primary_auc=[z for z in auc if z['feature'] in ('t1.scale.mean','t1.camera_upright_angle_deg.mean','t2_vs_t1.rotation_deg.rms','k3d_Aprime_vs_t1.rotation_deg.rms')],
        high_t1=[r for r in rules if r['feature'].startswith('t1.')],GT_only_gravity_AUC=gt_only)))

if __name__=='__main__': main()
