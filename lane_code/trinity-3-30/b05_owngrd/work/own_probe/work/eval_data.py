"""Tuning-only GT and teacher adapters. No fitting caller may use this module."""
import importlib.util
from pathlib import Path
import numpy as np
from PIL import Image
from probe_common import O,gate
from provenance import sha256


def tuning_gt(scene):
    gate.check_row(dict(scene=scene,split='tuning'),'tuning')
    path=O/'toolprog/work/gt/scannet'/(scene.split('/')[1]+'.npz')
    gate.guard_path(path)
    with np.load(path,allow_pickle=False) as z:
        value={k:z[k] for k in ('inst','ids','labels','valid','frame_indices')}
    value['path']=str(path);value['sha256']=sha256(path)
    return value


def matched_ids(gt,name):
    if not hasattr(matched_ids,'fn'):
        p=O/'toolprog/work/tp/tplib.py'
        spec=importlib.util.spec_from_file_location('own_eval_tplib',p)
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        matched_ids.fn=mod.match_labels
    names=gt['labels'].tolist();matches=matched_ids.fn(name,names)
    return [int(i) for i,n in zip(gt['ids'],names) if n in matches]


def gt_mask(gt,name,slot):
    out=np.zeros(gt['inst'].shape[-2:],bool)
    if not gt['valid'][slot]:return out
    for i in matched_ids(gt,name):
        mask=gt['inst'][slot]==i
        if mask.sum()>=154:out|=mask
    return out


def identity_for(mask,gt,slot):
    if not gt['valid'][slot]:return None
    small=np.asarray(Image.fromarray(mask).resize((gt['inst'].shape[2],gt['inst'].shape[1]),Image.Resampling.NEAREST),bool)
    best=None;score=0.
    for i in gt['ids']:
        other=gt['inst'][slot]==i
        inter=(small&other).sum();union=(small|other).sum()
        v=float(inter/union) if union else 0.
        if v>score:score=v;best=int(i)
    return best if score>=.5 else None
