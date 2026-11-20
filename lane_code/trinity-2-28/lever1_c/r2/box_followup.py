"""Frozen BOX arms; all fitting uses train rows only."""
import copy
import numpy as np
import k1x as K

FLOORS=(0,50,100,200,400,800)


def restrict(obj,areas,floor):
    out=dict(obj,boxes={})
    out['visible']=[f for f in obj['visible'] if areas[f-1]>=floor]
    out['frames']=[f for f in obj['frames'] if areas[f-1]>=floor]
    out['areas']={str(f):obj['areas'][str(f)] for f in out['visible']}
    out['points']={str(f):obj['points'][str(f)] for f in out['frames']}
    out['seen']=bool(out['frames'])
    if out['seen']:out['best']=min(out['frames'],key=lambda f:(-out['areas'][str(f)],f))
    else:out.pop('best',None)
    return out


def capture_box(c,geo,masks,objects,D,M):
    assert M.freeze=='vote_10_3_best'
    result={r['id']:{} for r in c['rows']}
    for m,ms in masks.items():
        obs=objects[m]
        robust={}
        for n,obj in obs.items():
            new=dict(obj,boxes={})
            if obj['seen']:
                try:
                    base=D.mathv.fusion_box(obj['points'],obj['best'],'best1',D.G.min_area_box)
                    points=np.concatenate([obj['points'][str(f)] for f in sorted(obj['frames'])])
                    new['boxes']['robust']=dict(base,centroid=np.median(points,axis=0))
                except ValueError:
                    new['oracle_error']='served_box_unavailable'
            robust[n]=new
        for r in c['rows']:
            result[r['id']][m+'/base']=K.predict(r,geo,obs,D)
            result[r['id']][m+'/fused']=K.predict(r,geo,obs,D,M.freeze)
            result[r['id']][m+'/robust']=K.predict(r,geo,robust,D,'robust')
        floors=FLOORS if c.get('k1_split','train')=='train' else (M.box_floor,)
        for floor in floors:
            # Both orientations have the same 240*320 served-grid area.
            areas={n:np.asarray(mask).sum(axis=(1,2))*np.prod(D.F.OUTPUT_SHAPE)/np.prod(mask.shape[1:]) for n,mask in ms.items()}
            restricted={n:restrict(obj,areas[n],floor) for n,obj in obs.items()}
            for r in c['rows']:result[r['id']][m+f'/floor_{floor}']=K.predict(r,geo,restricted,D)
    return result


def select_floor(rows,train_ids):
    train=[r for r in rows if r['row_id'] in train_ids]
    rooms=sorted({r['room'] for r in train})
    order=np.random.default_rng(K.SEED).permutation(len(rooms))
    folds={rooms[int(i)]:j%5 for j,i in enumerate(order)}
    scores={};details={}
    for floor in FLOORS:
        k='deployed/floor_'+str(floor)
        vals=[100*K.mra(r['box'][k]['prediction'],r['label']) for r in train]
        scores[floor]=float(np.mean(vals))
        details[floor]=[dict(fold=f,n=sum(folds[r['room']]==f for r in train),
            score=float(np.mean([v for r,v in zip(train,vals) if folds[r['room']]==f]))) for f in range(5)]
    best=min(FLOORS,key=lambda f:(-scores[f],f))
    return dict(floor=best,grid=FLOORS,seed=K.SEED,training_population='train1012',
                selection='item-weighted held-fold mean; smallest floor breaks ties; each candidate is fixed and has no fitted parameters',
                scores=scores,fold_scores=details,room_folds=folds,heldout_used=False)


def summarize(records,M):
    rows=[dict(r,box=rec['box'][r['row_id']]) for rec in records for r in rec['rows']]
    freeze=select_floor(rows,M.sets['train1012'])
    tables={};contrasts={};checks=[]
    for r in rows:
        for m in ('deployed','GT'):
            a=r['box'][m+'/base'];b=r['cells'][K.cell_name(m,'G3T','G3T','own')]
            checks.append(dict(row_id=r['row_id'],masks=m,passed=all(a[k]==b[k] for k in ('prediction','refusal','printed'))))
            r['box'][m+'/floor']=r['box'][m+'/floor_'+str(freeze['floor'])]
    assert all(c['passed'] for c in checks)
    for split,ids in M.sets.items():
        tables[split]={};contrasts[split]={}
        for ds,keep in K.BUCKETS.items():
            rs=[r for r in rows if r['row_id'] in ids and keep(r)]
            tables[split][ds]={};contrasts[split][ds]={}
            for m in ('deployed','GT'):
                for arm in ('base','fused','robust','floor'):
                    name=m+'/'+arm
                    scores=[100*K.mra(r['box'][name]['prediction'],r['label']) for r in rs]
                    tables[split][ds][name]=dict(K.bootstrap(rs,scores)[0],answered=sum(r['box'][name]['prediction'] is not None for r in rs))
                    if arm=='base':continue
                    diff=[v-100*K.mra(r['box'][m+'/base']['prediction'],r['label']) for r,v in zip(rs,scores)]
                    stat=K.bootstrap(rs,diff)[0]
                    passed=stat['mean']>=3 and stat['ci95'][0]>0
                    contrasts[split][ds][name]=dict(stat,heldout_bar_passed=passed,
                        dev_item_check='pending rank 1 dump',propose=False,
                        verdict='held-out bar passes; proposal pending rank 1 dump' if passed else 'box rule waits for better masks too')
    return dict(status='COMPLETE',rows=rows,freeze=freeze,base_parity=checks,tables=tables,contrasts=contrasts,
                statistics=dict(draws=K.DRAWS,seed=K.SEED,unit='physical room',paired=True),
                rules=dict(base='served best1',fused='frozen vote_10_3_best, 10 cm voxels, 3-frame support plus best-frame points',
                           robust='coordinatewise median of post-spread lifted points over all grounded frames; served axes and lengths',
                           floor='mask pixel area at the served 240x320 grid; same selected train-only floor in both mask columns'),
                dev_item_check='pending rank 1 dump')
