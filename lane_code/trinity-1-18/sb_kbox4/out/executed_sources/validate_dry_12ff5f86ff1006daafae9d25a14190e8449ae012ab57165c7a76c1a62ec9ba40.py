"""Stored-label and corrected-label parities; no GT-geometry execution."""
import gzip,json,re,resource,time
import numpy as np
import torch
import serving_reference as R
import train_pricing as T
from serving_reference import read,write,PINS,ROOT,OUT,G
import math_v2 as M

def main():
    started=time.monotonic()
    caps,labels,rowids,tableids,folds,truth,head=T.setup()
    checks=[];parity=[]
    for c in caps:
        if c['canonical'] not in ['arkitscenes/41048124','scannetpp/036bce3393']:continue
        dry=json.loads(read(OUT/'dry'/(c['canonical'].replace('/','__')+'.json')));checks+=dry['checks']
        geo,cache,meta,tower,receipt=R.geometry(c);gt,raw=R.gt_arrays(c)
        gt['raster']=raw['inst'];gt['valid']=raw['valid'].astype(bool)
        stored=json.loads(read('/scratch/jjyeung/orch_n30/b04host3/lift_price/harness/out_lift_train_v2/'+c['canonical'].replace('/','__')+'.json'))
        from student_pilot import camera_targets
        pose=tower['raw_pose'][tower['anchor_slots']]
        rot=np.array([camera_targets.rotation_from_xyzw(p[3:7]).T for p in pose]);gravity=np.mean(-rot[:,:,1],axis=0);gravity/=np.linalg.norm(gravity)
        sgeo=R.from_tower(tower['raw_pose'],tower['anchor_slots'],tower['frame_indices'],tower['depth_grid'],tower['grid_uv'],gravity,stored['scales']['S4'],receipt['source_hw'])
        rows=[r for r in c['rows'] if r['id'] in rowids];names={n for r in rows for n in r['operands']}
        objs={n:T.lifted(n,(raw['inst']==c['gt_name_ids'][n][0])&raw['valid'].astype(bool)[:,None,None],sgeo) for n in names}
        result=T.evaluate(c,rows,sgeo,objs,'stored_s4_parity','best1',labels,folds,truth,gt)
        expected={r['row_id']:r for r in stored['items'] if r['arm']=='S4+G1+bestspread'}
        for r in result:
            e=expected[r['row_id']]
            parity.append(dict(row_id=r['row_id'],prediction=r['prediction'],expected=e['pred'],passed=r['prediction']==e['pred'] and M.mra(r['prediction'],e['gt'])==e['mra']))
    expected={'GD_reviewed':74.30,'GT':93.07};scores={a:{} for a in expected};diff=[]
    for line in read('/scratch/jjyeung/orch_n30/k1_ops3/work/e3gd/out/PER_ITEM.jsonl').decode().splitlines():
        if '"split": "train"' not in line:continue
        r=json.loads(line);a=r['arm'];rid=r['row_id']
        if a not in scores or rid not in rowids:continue
        label=labels[rid]['corrected'];score=M.mra(r['pred'],label);scores[a][rid]=score
        alt=0. if r['pred'] is None else np.mean([abs(r['pred']-label)/abs(label)<1-t for t in [.50,.55,.60,.65,.70,.75,.80,.85,.90,.95]])
        if score!=alt:diff.append(dict(arm=a,row_id=rid,harness=score,decimal_theta=float(alt)))
    correction={a:dict(rows=len(s),mra=100*np.mean(list(s.values())) if s else None,expected=expected[a],passed=len(s)==1037 and round(100*np.mean(list(s.values())),2)==expected[a]) for a,s in scores.items()}
    gate=json.loads(read(OUT/'REFERENCE_REBUILD.json'))
    sample=json.loads(read(OUT/'REPLAY_SAMPLE.json'))['captures'];a0replay=[]
    for c in caps:
        if c['canonical'] not in sample:continue
        geo,cache,meta,_,_=R.geometry(c)
        ref=json.loads(gzip.decompress(read(R.TABLES/(c['canonical'].replace('/','__')+'.json.gz'))))
        stage=R.StageOne(R.cache_detect(cache),head,geo,rule='candidates_argmax')
        for name in sample[c['canonical']]:
            inputs=[i for i in ref['inputs'] if i['name']==name]
            cand,features=stage.features(name)
            with torch.no_grad():
                k=int(torch.argmax(head.with_null(torch.tensor([i['x'] for i in inputs],dtype=torch.float64),None,name)[:-1])) if inputs else -1
            j=stage.select(dict(x=torch.tensor(features,dtype=torch.float64),name=name)) if features else -1
            expected=None if k<0 else inputs[k]['candidate_id'];got=None if j<0 else cand[j]['candidate_id']
            a0replay.append(dict(capture=c['canonical'],dataset=c['canonical'].split('/')[0],name=name,expected=expected,got=got,passed=expected==got))
    a0summary=dict(matched=sum(r['passed'] for r in a0replay),total=len(a0replay),captures=len({r['capture'] for r in a0replay}))
    a0summary['rate']=a0summary['matched']/a0summary['total']
    a0pass=a0summary['total']>=149 and a0summary['captures']>=45 and a0summary['rate']>=.95
    write(OUT/'A0_REPLAY.json',dict(status='PASS' if a0pass else 'BLOCKED',rule='candidates_argmax',summary=a0summary,rows=a0replay))
    passed=gate['status']=='PASS' and a0pass and all(c['passed'] for c in checks+parity) and all(c['passed'] for c in correction.values())
    R.code_pins()
    write(ROOT/'out/DRYRUN.json',dict(status='PASS' if passed else 'BLOCKED',passed=passed,stage1_replay=gate['summary'],
        A0_candidates_argmax_replay=a0summary,tests=checks,stored_label_parity=parity,corrected_label_parity=correction,scorer_boundary_differences=diff,
        A6_status='DEFERRED by orchestrator order 0654Z; GT stored predictions are scored only for parity',heldout_evaluated=False,full_train_started=False,
        seconds=time.monotonic()-started,peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024))
    (ROOT/'STATUS.md').write_text(f'CPU dry-run gate {"PASS" if passed else "FAIL"}. Serving replay, copied-reader A0 reproduction, stored S4/G1 parity, corrected-label scorer parity, one-frame fusion and no-merge checks are recorded in out/DRYRUN.json. Held-out and A6 remain deferred.\n')
    print(json.dumps(dict(passed=passed,correction=correction,failed=[c for c in checks+parity if not c['passed']]),indent=2))

if __name__=='__main__':main()
