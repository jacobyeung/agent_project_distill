"""Positive-point SAM prompts, one track, and the unchanged reader lift/socket."""
from contextlib import contextmanager
from unittest.mock import patch
import numpy as np
from . import c,w
from .points import resolve


def choose(masks,scores,presence,point):
    if len(masks)!=len(scores):raise ValueError('mask/score count differs')
    if not np.isfinite(scores).all() or not np.isfinite(presence) or not 0<=presence<=1:
        raise ValueError('invalid SAM scores')
    if not len(masks):return None,False,[]
    x,y=point
    contains=[bool(m[min(int(y*m.shape[0]),m.shape[0]-1),min(int(x*m.shape[1]),m.shape[1]-1)]) for m in masks]
    eligible=[i for i,v in enumerate(contains) if v]
    fallback=not eligible
    if fallback:eligible=list(range(len(masks)))
    chosen=max(eligible,key=lambda i:float(scores[i])*presence)
    return chosen,fallback,contains


def detect(tower,features,name,frame_points,Prompt):
    import torch
    import torch.nn.functional as TF
    from student_pilot import routed_features as F
    from e2e_reader.stage1 import name_key,K1_CONTRACT
    from .geometric import make_prompt,check_detector
    tower._load()
    check_detector(tower)
    if len(features.frames)!=32 or len(features.sizes)!=32 or len(frame_points)!=32:
        raise ValueError('point frame count differs')
    with torch.inference_mode(),tower._autocast():
        text=tower._backend.model.backbone.forward_text([name_key(name)],device=str(tower.device))
    frames=[]
    for slot,(stored,size,point) in enumerate(zip(features.frames,features.sizes,frame_points)):
        if point is None:
            frames.append(dict(point=None,proposals=[],chosen=None,mask=None,fallback=False,reason='null point'))
            continue
        backbone={k:(v.to(tower.device) if hasattr(v,'to') else [x.to(tower.device) for x in v]) for k,v in stored.items()}
        backbone['vision_features']=backbone['backbone_fpn'][-1];backbone.update(text)
        with torch.inference_mode(),tower._autocast():
            raw=tower._backend.model.forward_grounding(backbone_out=backbone,find_input=tower._backend.find_stage,
                geometric_prompt=make_prompt(Prompt,point,tower.device),find_target=None)
        scores=raw['pred_logits'].sigmoid().reshape(-1).float()
        presence=float(raw['presence_logit_dec'].sigmoid().item())
        joint=scores*presence
        order=torch.argsort(scores,descending=True,stable=True)
        keep=order[joint[order]>=K1_CONTRACT['joint_floor']][:K1_CONTRACT['cap']]
        native=raw['pred_masks'].reshape(-1,*raw['pred_masks'].shape[-2:])
        masks=[]
        for i in keep.tolist():
            mask=TF.interpolate(native[i][None,None].float(),size,mode='bilinear',align_corners=False)[0,0]>0
            masks.append(F.resize(mask.cpu().numpy(),F.SHAPE))
        scores=scores[keep].cpu().numpy()
        chosen,fallback,contains=choose(masks,scores,presence,point)
        proposals=[dict(mask=c.rle(F.resize(mask,F.SHAPE)),score=float(scores[i]),presence=presence,
                        contains_point=contains[i],chosen=i==chosen) for i,mask in enumerate(masks)]
        selected=None if chosen is None else F.resize(masks[chosen],F.SHAPE)[::2,::2].copy()
        frames.append(dict(point=point,proposals=proposals,chosen=chosen,mask=selected,fallback=fallback,
                           reason='no SAM masks' if chosen is None else 'no containing mask' if fallback else 'contains point'))
    return frames


@contextmanager
def point_context(gen,ref,points,Prompt):
    """Scope the reader's global factory lookups to one serial point replay."""
    from e2e_reader import stage1
    current={}
    original_stage=stage1.StageOne
    class PointCapture(c.Capture):
        def __init__(self,stage_class,grounding):
            super().__init__(original_stage,grounding)
            self.codes={k:v for k,v in self.codes.items() if v in ('lift','box')}
        def __enter__(self):
            current['capture']=self
            return super().__enter__()
    def point_detect(tower,features,name):
        mapped,rule=resolve(name,points,stage1.name_key)
        frame_points=[points[mapped][str(s)] if mapped is not None else None for s in ref['source_indices']]
        # No text fallback even when name admission fails.
        return detect(tower,features,name,frame_points,Prompt)
    class PointStage:
        def __init__(self,detect,head,geometry,rule='null_argmax'):
            self.detect=detect;self.geometry=geometry;self.diagnostics={};self.cache={}
        def propose(self,name):
            if name in self.cache:return self.cache[name]
            capture=current['capture']
            if capture.geometry is None:capture.geometry=c.geometry_record(self.geometry)
            frames=self.detect(name);raw=[];selected={};members=[];decisions=[]
            mapped,rule=resolve(name,points,stage1.name_key)
            for f,entry in enumerate(frames,1):
                raw.extend(dict(p,id=f'{f}:{i}',frame=f,source_index=ref['source_indices'][f-1],prompt=name)
                           for i,p in enumerate(entry['proposals']))
                if entry['chosen'] is not None:
                    selected[str(f)]=c.rle(entry['mask']);members.append(f"{f}:{entry['chosen']}")
                decisions.append({k:entry[k] for k in ('point','chosen','fallback','reason')})
            candidates=[dict(id='0',masks=selected,features={})] if selected else []
            record=dict(name=name,points_name=mapped,name_binding=rule,proposals=raw,
                        linked_tracks=[dict(id='0',members=members,features={})] if selected else [],
                        candidates=candidates,early_lifts=[],early_rejections=[],
                        selector=dict(skipped='point prompts',invoked=False,slots=None,choice=0 if selected else -1,
                                      null_index=len(candidates),inputs=[],rule='points'),
                        selected_masks=selected,frame_decisions=decisions,lift=None,fitted_box=None)
            capture.objects.append(record);capture.by_name[name]=record
            self.diagnostics[name]=dict(selector_skipped=True,points_name=mapped,frames=list(selected))
            result=([dict(candidate_id='0',masks={int(f):c.unrle(m) for f,m in selected.items()})] if selected else [],{})
            self.cache[name]=result
            return result
        def select(self,inputs):return 0
    with patch.object(stage1,'StageOne',PointStage),patch.object(stage1,'sam3_detect',point_detect),patch.object(w,'Capture',PointCapture):
        yield
