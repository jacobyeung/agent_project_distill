"""Audit every selected nonempty training mask on every encoder grid, CPU only."""
import collections,json,time
import numpy as np
import torch
from torch.nn import functional as F
from extract import raster_masks,chosen_instances
from probe_common import ROOT,gate,ARMS,rules
from provenance import write_json

def run():
    torch.set_num_threads(4);rows=gate.read_manifest(ROOT/'out/b2_manifest.jsonl');by_scene=collections.defaultdict(list)
    for row in rows:
        if row['slot']%rules()['sampling']['training_frame_stride']==0:by_scene[row['scene']].append(row)
    grids={a:tuple(s//(14 if a in ('A4','A7','D2') else 16) for s in size) for a,(_,size) in ARMS.items() if a!='A8'}
    counts={a:dict(regions=0,zero=0) for a in grids};start=time.monotonic()
    for scene,frames in by_scene.items():
        masks=raster_masks(frames[0])
        for row in frames:
            selected=[masks[x['instance_id']][row['slot']] for x in chosen_instances(row)]
            if not selected:continue
            source=torch.from_numpy(np.stack(selected)).float()[:,None]
            if not (source.sum((1,2,3))>0).all():raise AssertionError('Manifest selected an empty source region')
            for size in set(grids.values()):
                weights=F.interpolate(source,size=size,mode='area');zero=int((weights.sum((1,2,3))==0).sum())
                for arm,grid in grids.items():
                    if grid==size:counts[arm]['regions']+=len(source);counts[arm]['zero']+=zero
    write_json(ROOT/'out/AREA_POOL_AUDIT.json',dict(arms=counts,seconds=time.monotonic()-start,method='All selected training and validation masks; area-resampled weights. Extractor separately rejects zero-valued encoded region features.'))
    assert all(v['zero']==0 for v in counts.values()),counts
    print(json.dumps(counts))
if __name__=='__main__':run()
