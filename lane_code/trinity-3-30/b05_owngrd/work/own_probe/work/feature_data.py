import collections
import json
from pathlib import Path
import torch
from probe_common import gate,admit_shard
from own_feats.core import channel_reduce


def load_features(root,arm,purpose,readout='four'):
    if arm=='A8':
        x,records,inputs=load_features(root,'A2',purpose,readout)
        y,other,pins=load_features(root,'A4',purpose,readout)
        keys={r['region_id']:i for i,r in enumerate(other)}
        if len(keys)!=len(records) or {r['region_id'] for r in records}!=set(keys):
            raise ValueError('A8 region sets differ between A2 and A4')
        return channel_reduce(torch.cat([x,y[[keys[r['region_id']] for r in records]]],-1)),records,inputs+pins
    path=Path(root)/arm
    if not (path/'COMPLETE.json').is_file():raise ValueError(f'Incomplete feature extraction: {arm}')
    complete=json.loads((path/'COMPLETE.json').read_text())
    records=[];features=[];inputs=[path/'COMPLETE.json'];binding=None
    for p in sorted(path.glob('*.pt')):
        gate.guard_path(p)
        meta=json.loads(Path(str(p)+'.json').read_text())
        if meta['purpose']!=purpose:continue
        obj,meta=admit_shard(p,purpose)
        if meta['binding']!=complete['binding']:raise ValueError('Feature shard and completion binding differ')
        if binding is None:binding=meta['binding']
        elif binding!=meta['binding']:raise ValueError('Mixed feature-extraction bindings')
        key={'four':'features','final':'final_features','unstandardized':'unstandardized_features'}[readout]
        features.append(obj[key]);records.extend(obj['records']);inputs.extend([p,Path(str(p)+'.json')])
    if not features:raise ValueError(f'No {purpose} features for {arm}')
    return torch.cat(features).float(),records,inputs


def frame_groups(records):
    groups=collections.defaultdict(list)
    for i,r in enumerate(records):groups[(r['scene'],r['slot'])].append(i)
    return list(groups.values())


def candidate_groups(features,records):
    groups=collections.defaultdict(list)
    for i,r in enumerate(records):groups[(r['object_id'],r['candidate_id'])].append(i)
    return {k:features[ids].mean(0) for k,ids in groups.items()}
