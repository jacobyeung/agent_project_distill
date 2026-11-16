"""Fit feature-only listwise selection on training rooms; score tuning only."""
import argparse
import collections
import json
from pathlib import Path
import numpy as np
import torch
from torch.nn import functional as F
from own_feats import NameEmbedder
from feature_data import load_features,frame_groups,candidate_groups
from probe_heads import Selector,ScoreFusion,listwise_loss,parameter_gate
from probe_common import *


def tasks(records):
    result=[]
    for ids in frame_groups(records):
        for name in sorted({records[i]['name'] for i in ids}):
            result.append((ids,name,torch.tensor([records[i]['name']==name for i in ids])))
    return result


def fit(features,records,names,steps,device):
    for row in records: gate.check_row(row,'training')
    model=Selector(features.shape[-1]).to(device);parameter_gate(model)
    optim=torch.optim.AdamW(model.parameters(),lr=rules()['fit']['learning_rate'],weight_decay=.01)
    train=[t for t in tasks(records) if records[t[0][0]]['split']=='train']
    val=[t for t in tasks(records) if records[t[0][0]]['split']=='val']
    if not train or not val:raise ValueError('Training and room-disjoint validation groups required')
    fitcfg=json.loads((ROOT/'work/FIT_CONFIG.json').read_text())
    raw=json.loads(Path(fitcfg['confusers_path']).read_text())
    confusers={normalize_name(k):{normalize_name(v) for v in vs} for k,vs in raw.items()}
    rng=np.random.default_rng(17)
    for step in range(steps):
        optim.zero_grad();losses=[]
        for j in rng.integers(0,len(train),size=rules()['fit']['batch_objects']):
            ids,name,positive=train[j]
            logits=model(features[ids].to(device),names[name].to(device).expand(len(ids),-1))
            negative_weights=torch.tensor([fitcfg['confuser_negative_weight'] if records[i]['name'] in confusers.get(name,set()) else 1.
                                           for i in ids],device=device)
            losses.append(listwise_loss(logits,positive.to(device),negative_weights))
        loss=torch.stack(losses).mean();loss.backward();optim.step()
    model.eval();correct=collections.defaultdict(list)
    with torch.inference_mode():
        for ids,name,positive in val:
            choice=model(features[ids].to(device),names[name].to(device).expand(len(ids),-1)).argmax().item()
            correct[(records[ids[0]]['scene'],name)].append(float(positive[choice]))
    return model,mean_ci([np.mean(x) for x in correct.values()],rooms=[gate.room(*s.split('/')) for s,n in correct])


def fit_fusion(path,model,device,admitted_scenes):
    """Each O5-derived row supplies candidate features, score and on-target truth.

    Schema: dataset,scan,split=train, features[K,D], name_embedding[4096],
    sam_scores[K], positive[K]. Never generate artificial teacher scores for GT regions.
    """
    rows=gate.read_manifest(path,'training')
    if any(r.get('split')!='train' for r in rows):raise ValueError('Fusion fits train rooms only')
    if any(r.get('scene') not in admitted_scenes for r in rows):raise ValueError('Fusion scene is outside this training split')
    examples=[]
    with torch.inference_mode():
        for r in rows:
            x=torch.tensor(r['features'],dtype=torch.float32,device=device)
            name=torch.tensor(r['name_embedding'],dtype=torch.float32,device=device).expand(len(x),-1)
            score=torch.tensor(r['sam_scores'],dtype=torch.float32,device=device)
            positive=torch.tensor(r['positive'],dtype=torch.bool,device=device)
            if score.shape!=(len(x),) or positive.shape!=(len(x),) or not positive.any():raise ValueError('Invalid fusion candidate group')
            if not torch.isfinite(x).all() or not torch.isfinite(name).all() or not torch.isfinite(score).all():raise ValueError('Nonfinite fusion input')
            if (score<0).any() or (score>1).any():raise ValueError('SAM scores must lie in [0,1]')
            hard=torch.tensor([s=='HARDNEG' for s in r.get('statuses',['POS' if y else 'NEG' for y in r['positive']])],device=device)
            confuser=torch.tensor(r.get('confuser',[False]*len(x)),dtype=torch.bool,device=device)
            if hard.shape!=positive.shape or confuser.shape!=positive.shape:raise ValueError('Invalid HARDNEG metadata')
            negative_weights=torch.where(hard&confuser,torch.tensor(.25,device=device),torch.tensor(1.,device=device))
            examples.append((model(x,name).detach().clone(),torch.tensor(r['sam_scores'],device=device),
                             positive,negative_weights))
    if not examples:raise ValueError('No fusion examples')
    fusion=ScoreFusion().to(device);optim=torch.optim.AdamW(fusion.parameters(),lr=.01)
    rng=np.random.default_rng(17)
    for step in range(rules()['fit']['fusion_steps']):
        optim.zero_grad();losses=[]
        for j in rng.integers(0,len(examples),size=min(16,len(examples))):
            a,b,y,negative_weights=examples[j];losses.append(listwise_loss(fusion(a,b),y,negative_weights))
        torch.stack(losses).mean().backward();optim.step()
    return fusion.eval()


def run(args):
    seed_all();out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    x,records,inputs=load_features(args.feature_root,args.arm,'training',getattr(args,'readout','four'))
    tx,trecords,tinputs=load_features(args.feature_root,args.arm,'tuning',getattr(args,'readout','four'));inputs+=tinputs
    groups,labels,fits,pins=candidate_inputs()
    all_names=sorted({r['name'] for r in records}|{candidate_phrase(g) for g in groups})
    embed=NameEmbedder();nb=embed(all_names);names=dict(zip(all_names,nb.mean))
    model,val=fit(x,records,names,rules()['fit']['T1_steps'],args.device)
    fusion=fit_fusion(args.fusion_rows,model,args.device,{r['scene'] for r in records if r['split']=='train'}) if args.fusion_rows else None
    candidates=candidate_groups(tx,trecords);predictions=[];success=[];consistent=[];fused=[];fused_consistent=[];baseline=[]
    with torch.inference_mode():
        for g in groups:
            ids=[c['candidate_id'] for c in g['candidates']]
            feat=torch.stack([candidates[(g['object_id'],k)] for k in ids]).to(args.device)
            logits=model(feat,names[candidate_phrase(g)].to(args.device).expand(len(ids),-1))
            good,consistent_labels,_=candidate_truth(g,labels[g['object_id']],fits[g['object_id']])
            j=logits.argmax().item();success.append(float(good[j]));consistent.append(float(consistent_labels[j]));baseline.append(float(good[0]))
            scores=torch.tensor([c['peak'] for c in g['candidates']],device=args.device)
            k=fusion(logits,scores).argmax().item() if fusion else None
            if k is not None:fused.append(float(good[k]));fused_consistent.append(float(consistent_labels[k]))
            predictions.append(dict(scene=g['scene'],object_id=g['object_id'],candidate_id=ids[j],accepted=True,
                                    fused_candidate_id=ids[k] if k is not None else None,
                                    logits=logits.cpu().tolist(),on_target=bool(good[j]),name_consistent=bool(consistent_labels[j]),baseline_on_target=bool(good[0]),fused_on_target=bool(good[k]) if k is not None else None))
    checkpoint=dict(state_dict={k:v.cpu() for k,v in model.state_dict().items()},feature_dim=x.shape[-1],
                    arm=args.arm,rules_sha256=sha256(RULES_PATH),name_rows_sha256=nb.rows_sha256,
                    tokenizer_sha256=nb.tokenizer_sha256,input_pins={str(p):sha256(p) for p in inputs},
                    fusion_state={k:v.cpu() for k,v in fusion.state_dict().items()} if fusion else None)
    torch.save(checkpoint,out/f't1_selector_{args.arm}_features.pt')
    if fusion:torch.save(checkpoint,out/f't1_selector_{args.arm}_fused.pt')
    rooms=[gate.room(*g['scene'].split('/')) for g in groups]
    metrics=dict(arm=args.arm,readout=getattr(args,'readout','four'),task='T1',status='complete' if fusion else 'feature_complete_fusion_pending',
                 features=dict(on_target=mean_ci(success,rooms=rooms),name_consistent=mean_ci(consistent,rooms=rooms),training_val_top1=val),
                 fused=dict(on_target=mean_ci(fused,rooms=rooms),name_consistent=mean_ci(fused_consistent,rooms=rooms),gain=mean_ci(fused,baseline,rooms=rooms)) if fusion else None,
                 fusion_missing_reason=None if fusion else 'O5 training-room scored proposals have not been supplied',
                 candidate_pins=pins,name_rows_sha256=nb.rows_sha256,predictions=predictions,
                 fitting_steps=rules()['fit']['T1_steps'],parameters=parameter_gate(model),
                 routed_gains=None,routed_status='Run routed_tuning.py on these frozen selections')
    if args.fusion_rows:inputs.append(Path(args.fusion_rows))
    output_metrics(out/'T1.json',metrics,inputs+[Path(__file__),RULES_PATH,ROOT/'work/FIT_CONFIG.json',O/'mdg_build/work/cfg/confusers.json'],vars(args))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--arm',choices=ARMS,required=True)
    p.add_argument('--feature-root',required=True);p.add_argument('--out',required=True);p.add_argument('--device',default='cuda:0')
    p.add_argument('--readout',choices=['four','final','unstandardized'],default='four');p.add_argument('--fusion-rows');run(p.parse_args())


if __name__=='__main__':main()
