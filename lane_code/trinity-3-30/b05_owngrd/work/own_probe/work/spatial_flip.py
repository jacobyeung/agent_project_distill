"""Real-frame correspondence gate with spatial fault controls."""
import torch
from torch.nn import functional as F
from own_feats import pool
from own_feats.core import readout_maps


def corrupt(maps,kind):
    if kind=='transpose':return [m.transpose(1,2).reshape_as(m) for m in maps]
    axis,shift={'left':(2,-1),'right':(2,1),'up':(1,-1),'down':(1,1)}[kind]
    return [torch.roll(m,shift,axis) for m in maps]


def correspondence(original,flipped,masks):
    """The grid must have a strict local correspondence maximum at zero displacement.

    In addition to the real-instance mirror contrast, ±one-patch shifts and a
    transposed grid must score below the correct correspondence. Masks are chosen
    from GT before encoding; no feature-dependent mask or threshold selection.
    """
    if len(original)!=4 or len(flipped)!=4:raise ValueError('Four taps required')
    a=readout_maps(original,'unstandardized');b=readout_maps(flipped,'unstandardized')
    mask=torch.as_tensor(masks,dtype=torch.float32)
    anchor=pool(a,mask)
    def similarity(maps,where):return F.cosine_similarity(anchor,pool(maps,where),dim=-1)
    same=similarity(b,mask.flip(-1));wrong=similarity(b,mask)
    alternatives={k:similarity(corrupt(b,k),mask.flip(-1)) for k in ('left','right','up','down','transpose')}
    margin=float((same-wrong).mean())
    controls={k:dict(cosine=float(v.mean()),gap=float((same-v).mean()),
                    rejected=bool((same-v).mean()>1e-6)) for k,v in alternatives.items()}
    passed=margin>1e-6 and all(c['rejected'] for c in controls.values())
    return dict(status='PASS' if passed else 'FAIL',instances=len(mask),same_mask_cosine=float(same.mean()),
        unflipped_position_cosine=float(wrong.mean()),mirror_margin=margin,negative_controls=controls,
        criterion='Positive mean mirror margin; zero displacement strictly beats every shifted/transposed control by >1e-6')


def validate_correspondence(original,flipped,masks):
    result=correspondence(original,flipped,masks)
    faults={kind:correspondence(corrupt(original,kind),corrupt(flipped,kind),masks)
            for kind in ('left','right','transpose')}
    result['mutant_grid_tests']={kind:value['status'] for kind,value in faults.items()}
    if any(value['status']!='FAIL' for value in faults.values()):result['status']='FAIL'
    return result
