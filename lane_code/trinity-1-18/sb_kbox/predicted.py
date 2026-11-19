"""StageOne replay and gather adapters; requires CPU torch in the chosen environment."""
from collections import defaultdict
import sys
import numpy as np
from adapters import READER, TREE
from box_math import gather


def cache_detect(cache):
    """Apply raw-name identity, joint floor .05, and cap 30 before StageOne."""
    from student_pilot import routed_features as F
    def detect(name):
        frames = []
        for slot in range(32):
            record = cache['frames'][str(slot)]['phrases'].get(name)
            if record is None:
                frames.append([]); continue
            entries = [p for p in record.get('instances', []) if p.get('source_prompt',name)==name]
            pres = float(entries[0].get('source_presence',record['presence'])) if entries else float(record['presence'])
            if any(float(p.get('source_presence',pres))!=pres for p in entries):
                raise ValueError('raw_name_presence_mismatch')
            entries = [p for p in sorted(entries,key=lambda p:-float(p['score'])) if float(p['score'])*pres>=.05][:30]
            out=[]
            for p in entries:
                rle=p['mask'];h,w=rle['size']
                counts=np.asarray(rle['counts'],np.int64)
                if np.any(counts<0) or counts.sum()!=h*w:
                    raise ValueError('invalid_rle')
                mask=np.repeat(np.arange(len(counts))%2==1,counts).reshape((h,w),order='F')
                out.append(dict(mask=F.resize(mask,F.SHAPE),score=float(p['score']),presence=pres))
            frames.append(out)
        return frames
    return detect


def replay(cache, geometry, head, name, table_rows):
    """Return A0/A1 choices and proposals without consulting distance labels."""
    sys.path[:0]=[str(READER),str(TREE),str(READER/'heads/selector')]
    import torch
    from e2e_reader.stage1 import StageOne
    stage=StageOne(cache_detect(cache),head,geometry)
    accepted,x=stage.features(name)
    if not accepted:
        return dict(accepted=[],A0=-1,A1=-1,null_argmax=-1,tracks={},proposals=[],raw=stage.raw[name])
    with torch.no_grad():
        slots=head.with_null(torch.tensor(x,dtype=torch.float64),None,name)
    a0=int(torch.argmax(slots[:-1]));null=int(torch.argmax(slots))
    null=-1 if null==len(accepted) else null
    F=stage.F
    proposals,_=F.candidates.lift(F.cache_for(name,stage.raw[name]),name,geometry,floor=.3,grids=stage.grids,phrase=name)
    tracks={c.id:c for c in F.candidates.link(proposals,name)}
    labels={r['candidate_id']:r['y'] for r in table_rows if r['name']==name}
    positive=[i for i,a in enumerate(accepted) if labels.get(a['candidate_id'])==1]
    a1=min(positive,key=lambda i:(-len(tracks[accepted[i]['candidate_id']].proposals),i)) if positive else a0
    return dict(accepted=accepted,x=x,A0=a0,A1=a1,null_argmax=null,tracks=tracks,proposals=proposals,raw=stage.raw[name])


def gathered_masks(result,choice):
    from student_pilot import routed_features as F
    if choice<0:
        return np.zeros((32,)+tuple(F.SHAPE),bool),[],[]
    track=result['tracks'][result['accepted'][choice]['candidate_id']]
    members=gather(track.proposals,result['proposals'])
    masks=np.zeros((32,)+tuple(F.SHAPE),bool)
    # Proposal.index indexes the same score-sorted per-frame detector list.
    for p in members:
        masks[p.frame-1]=result['raw'][p.frame-1][p.index]['mask']
    return masks,track.proposals,members


def member_precision(members,gt_masks):
    """Precision against the seed's explicitly supplied GT instance; no guessed mapping."""
    from scipy.ndimage import zoom
    hits=[]
    for p in members:
        truth=gt_masks[p.frame-1]
        truth=zoom(truth,(p.mask.shape[0]/truth.shape[0],p.mask.shape[1]/truth.shape[1]),order=0,prefilter=False)
        union=np.count_nonzero(p.mask|truth)
        hits.append(bool(union and np.count_nonzero(p.mask&truth)/union>.5))
    return dict(members=len(hits),correct=sum(hits),precision=sum(hits)/len(hits) if hits else None)
