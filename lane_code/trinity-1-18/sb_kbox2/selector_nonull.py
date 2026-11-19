"""Five room-grouped train folds, positive-object candidate CE, and final train fit.

The run_iso architecture/optimizer config is fixed before training. Multiple
positive candidates receive equal target mass. No null module is instantiated
in saved models. This module never opens tables outside the supplied train list.
"""
import json
import random
from collections import defaultdict
from pathlib import Path
import sys
from adapters import ROOT


def build_class():
    import torch
    sys.path.insert(0,str(ROOT/'vendor'))
    from selector_head import SelectorHead
    class NonNullHead(SelectorHead):
        def __init__(self,**kwargs):
            super().__init__(**kwargs)
            del self.null
        def forward(self,x,name_emb=None,name=None,mask_tokens=None,vit_feats=None):
            z=((x.double()-self.feat_mean)/self.feat_std).float()
            h=self.phi(z)
            if mask_tokens is not None:h=h+self.mask_proj(mask_tokens.float())
            if vit_feats is not None:h=h+self.vit_proj(vit_feats.float())
            ctx=torch.cat([h.mean(0),h.max(0).values,self.name_vector(name_emb,name)])
            return self.out(torch.cat([h,ctx.expand(len(x),-1)],1))[:,0]
    return NonNullHead


def fit(groups,config,seed=20261116):
    import torch
    torch.set_num_threads(8);torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    groups=[g for g in groups if any(g['y'])]
    if not groups:raise ValueError('no_positive_train_objects')
    cls=build_class()
    head=cls(hidden=config['hidden'],name_mode=config['name_mode'],n_hash=config.get('n_hash',4096))
    X=torch.cat([torch.tensor(g['x'],dtype=torch.float64) for g in groups])
    head.feat_mean.copy_(X.mean(0))
    std=X.std(0);head.feat_std.copy_(torch.where(std>1e-12,std,torch.ones_like(std)))
    opt=torch.optim.AdamW(head.parameters(),lr=config['lr'],weight_decay=config['wd'])
    rng=random.Random(seed);order=list(range(len(groups)))
    for epoch in range(config['epochs']):
        rng.shuffle(order)
        for start in range(0,len(order),16):
            losses=[]
            for i in order[start:start+16]:
                g=groups[i];x=torch.tensor(g['x'],dtype=torch.float64)
                y=torch.tensor(g['y'],dtype=torch.float32);y=y/y.sum()
                logits=head(x,None,g['name'])
                losses.append(-(y*torch.log_softmax(logits,0)).sum())
            opt.zero_grad();torch.stack(losses).mean().backward();opt.step()
    return head.eval()


def train_oof(groups,config,out,input_sha256,seed=20261116):
    import torch
    from safetensors.torch import save_file
    assert all(g['split']=='train' for g in groups)
    if config['name_mode']!='none':
        raise ValueError('This kit binds the run_iso name_mode=none configuration only')
    rooms=sorted({g['room'] for g in groups});random.Random(seed).shuffle(rooms)
    folds={room:i%5 for i,room in enumerate(rooms)}
    choices={};out=Path(out);out.mkdir(parents=True,exist_ok=True)
    for fold in range(5):
        head=fit([g for g in groups if folds[g['room']]!=fold],config,seed)
        with torch.no_grad():
            for g in groups:
                if folds[g['room']]==fold:
                    k=int(torch.argmax(head(torch.tensor(g['x'],dtype=torch.float64),None,g['name'])))
                    choices[g['object_id']]=g['candidate_ids'][k]
        save_file({k:v.contiguous() for k,v in head.state_dict().items()},str(out/f'fold_{fold}.safetensors'))
    final=fit(groups,config,seed)
    save_file({k:v.contiguous() for k,v in final.state_dict().items()},str(out/'final.safetensors'))
    meta=dict(input_sha256=input_sha256,config=config,seed=seed,folds=folds,oof_choices=choices,
              target='uniform positive-candidate cross entropy; exclude zero-positive objects from fitting')
    (out/'TRAIN_OOF.json').write_text(json.dumps(meta,indent=2)+'\n')
    return choices,final
