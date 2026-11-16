"""Export selected candidate members to rk.programs' packed-mask schema."""
import argparse
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy import ndimage
from .io import rows, validate, mask_for, tower, sha, dump


def export(candidates, selections, out, arm='fusion', accept='calibrated'):
    groups=validate(rows(candidates)); selected={r['object_id']:r for r in rows(selections) if r['arm']==arm}
    by_scene=defaultdict(list)
    for g in groups:
        if g['object_id'] in selected:by_scene[g['scene']].append(g)
    root=Path(out);root.mkdir(parents=True,exist_ok=True);index={}
    for scene, gs in sorted(by_scene.items()):
        gs=sorted(gs,key=lambda g:g['name']);names=[g['name'] for g in gs]
        if len(set(names))!=len(names):raise ValueError('Use clip-name objects, not frame-specific pointing items, for rk export')
        n=len(gs); masks=np.zeros((n,32,80,112),bool);prob=np.zeros((n,32),np.float32)
        uv=np.zeros((n,32,2),np.float32);iou=np.zeros((n,32),np.float32)
        for q,g in enumerate(gs):
            sel=selected[g['object_id']]
            if sel['candidate_id'] is None or (accept=='calibrated' and not sel['accepted']):continue
            candidate=next(c for c in g['candidates'] if c['candidate_id']==sel['candidate_id'])
            members=candidate.get('members') or [candidate]
            seen=set()
            for member in members:
                k=member['slot']
                if k in seen:raise ValueError('A linked candidate has two members from the same frame')
                seen.add(k)
                m=mask_for(member);small=ndimage.zoom(m,(80/m.shape[0],112/m.shape[1]),order=0,prefilter=False)
                if not small.any():continue
                masks[q,k]=small;prob[q,k]=1.;iou[q,k]=np.clip(candidate['peak'],0,1)
                uv[q,k]=np.rint(tower().deepest(small))
        indices=gs[0]['frame_indices']
        if any(g['frame_indices']!=indices for g in gs):raise ValueError('Inconsistent frame indices')
        audit=dict(schema='verify-rk-export-v1',tau=.5,frame_indices=indices,gt_substitution=any(g.get('oracle') for g in gs),
            candidate_source=sorted({g['candidate_source'] for g in gs}),arm=arm,accept=accept,
            candidate_sha256=sha(candidates),selection_sha256=sha(selections),
            propagation='Selected linked members only; no geometry propagation is synthesized by B3.')
        stem=scene.replace('/','__')+'.npz'
        with (root/stem).open('xb') as f:
            np.savez_compressed(f,names=np.asarray(names),prob=prob,clip_prob=np.ones(n,np.float32),
                frame_prob=prob.copy(),iou=iou,uv=uv,area=masks.mean((-1,-2)),
                masks=np.packbits(masks,axis=-1,bitorder='little'),mask_shape=np.asarray(masks.shape),
                audit=np.asarray(json.dumps(audit)))
        index[scene]=dict(scene=scene,scene_key=scene,npz=stem,frame_indices=indices)
    dump(root/'INDEX.json',index)
    return dict(scenes=len(index),objects=sum(map(len,by_scene.values())),arm=arm)


def main():
    p=argparse.ArgumentParser(__doc__);p.add_argument('--candidates',required=True);p.add_argument('--selections',required=True)
    p.add_argument('--out',required=True);p.add_argument('--arm',default='fusion');p.add_argument('--accept',choices=['calibrated','all'],default='calibrated')
    a=p.parse_args();print(json.dumps(export(a.candidates,a.selections,a.out,a.arm,a.accept)))

if __name__=='__main__':main()
