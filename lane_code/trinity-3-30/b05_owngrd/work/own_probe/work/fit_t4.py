"""Cross-view identity probe; fits GT identities only on training rooms."""
import argparse
import collections
from pathlib import Path
import numpy as np
import torch
from torch.nn import functional as F
from feature_data import load_features
from probe_heads import IdentityProbe,contrastive_loss,parameter_gate
from probe_common import *


def retrieval(features,records,projector=None,device='cpu'):
    z=F.normalize(features,dim=-1)
    if projector is not None:
        with torch.inference_mode():z=projector(features.to(device)).cpu()
    by_object=collections.defaultdict(list)
    for i,r in enumerate(records):
        if r.get('gt_instance_id') is not None:by_object[r['object_id']].append(i)
    objects=[]
    for key,ids in sorted(by_object.items()):
        if len({records[i]['gt_instance_id'] for i in ids})<2:continue
        successes=[];centroid=[];pair_y=[];pair_scores=[];centroid_pair=[]
        for i in ids:
            eligible=[j for j in ids if abs(records[j]['slot']-records[i]['slot'])>=8]
            if not any(records[j]['gt_instance_id']==records[i]['gt_instance_id'] for j in eligible):continue
            scores=(z[eligible]@z[i]).numpy();j=eligible[int(scores.argmax())]
            successes.append(float(records[j]['gt_instance_id']==records[i]['gt_instance_id']))
            if records[i].get('centroid') is not None and all(records[k].get('centroid') is not None for k in eligible):
                distances=np.linalg.norm(np.array([records[k]['centroid'] for k in eligible])-records[i]['centroid'],axis=-1)
                k=eligible[int(distances.argmin())]
                centroid.append(float(records[k]['gt_instance_id']==records[i]['gt_instance_id']))
            else:centroid.append(None)
        for a,i in enumerate(ids):
            for j in ids[a+1:]:
                if records[i]['candidate_id']!=records[j]['candidate_id'] or records[i]['slot']==records[j]['slot']:continue
                pair_y.append(records[i]['gt_instance_id']==records[j]['gt_instance_id'])
                pair_scores.append(float(z[i]@z[j]))
                if records[i].get('centroid') is not None and records[j].get('centroid') is not None:
                    centroid_pair.append(-float(np.linalg.norm(np.array(records[i]['centroid'])-records[j]['centroid'])))
                else:centroid_pair.append(None)
        if successes or pair_y:
            objects.append(dict(object_id=key,retrieval=successes,centroid=centroid,member_labels=pair_y,
                                member_scores=pair_scores,centroid_pair=centroid_pair))
    return objects


def summarize(objects):
    eligible=[x for x in objects if x['retrieval']]
    def mean(records,key):
        vals=[np.mean(r[key]) for r in records if r[key]]
        return float(np.mean(vals)) if vals else None
    paired=[r for r in eligible if all(x is not None for x in r['centroid'])]
    member=[r for r in objects if r['member_labels']]
    def auc(rs):return auroc([v for r in rs for v in r['member_labels']], [v for r in rs for v in r['member_scores']])
    paired_member=[r for r in member if all(v is not None for v in r['centroid_pair'])]
    def auc_gain(rs):
        ours=auc(rs);base=auroc([v for r in rs for v in r['member_labels']],[v for r in rs for v in r['centroid_pair']])
        return ours-base if ours is not None and base is not None else None
    return dict(member_auroc_gain=object_bootstrap(paired_member,auc_gain) if paired_member else None,top1=object_bootstrap(eligible,lambda rs:mean(rs,'retrieval')) if eligible else None,
                centroid_top1=object_bootstrap(paired,lambda rs:mean(rs,'centroid')) if paired else None,
                retrieval_gain=object_bootstrap(paired,lambda rs:mean(rs,'retrieval')-mean(rs,'centroid')) if paired else None,
                member_auroc=object_bootstrap(member,auc) if member else None,
                objects=len(objects),retrieval_objects=len(eligible),centroid_paired_objects=len(paired))


def run(a):
    seed_all();x,records,inputs=load_features(a.feature_root,a.arm,'training',getattr(a,'readout','four'))
    tx,tr,tinputs=load_features(a.feature_root,a.arm,'tuning',getattr(a,'readout','four'));inputs+=tinputs
    model=IdentityProbe(x.shape[-1]).to(a.device);parameter_gate(model)
    clips=collections.defaultdict(list)
    for i,r in enumerate(records):
        if r['split']=='train':clips[r['scene']].append(i)
    clips=list(clips.values());rng=np.random.default_rng(17)
    optimizer=torch.optim.AdamW(model.parameters(),lr=rules()['fit']['learning_rate'])
    for step in range(rules()['fit']['T4_steps']):
        ids=clips[int(rng.integers(len(clips)))];optimizer.zero_grad()
        z=model(x[ids].to(a.device));iid=torch.tensor([records[i]['instance_id'] for i in ids],device=a.device)
        slots=torch.tensor([records[i]['slot'] for i in ids],device=a.device)
        loss=contrastive_loss(z,iid,slots);loss.backward();optimizer.step()
    model.eval();raw=retrieval(tx,tr);mapped=retrieval(tx,tr,model,a.device)
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    torch.save(dict(state_dict={k:v.cpu() for k,v in model.state_dict().items()},feature_dim=x.shape[-1],
                    rules_sha256=sha256(RULES_PATH),arm=a.arm),out/'t4_identity.pt')
    output_metrics(out/'T4.json',dict(arm=a.arm,readout=getattr(a,'readout','four'),task='T4',status='complete',cosine=summarize(raw),linear=summarize(mapped),
                    records=mapped,fit_steps=rules()['fit']['T4_steps'],identity_gate='proposal GT IoU >= 0.5'),
                    inputs+[Path(__file__),RULES_PATH],vars(a))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--arm',choices=ARMS,required=True)
    p.add_argument('--feature-root',required=True);p.add_argument('--out',required=True);p.add_argument('--device',default='cuda:0')
    p.add_argument('--readout',choices=['four','final','unstandardized'],default='four')
    run(p.parse_args())
