"""Join a capture to reviewed per-instance GT in a common metric frame."""
import argparse
import gzip
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from funnel import stage, outside_obb
from capture import unrle


def hash_file(path):
    import hashlib
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def iou(mask, target):
    a,b=unrle(mask),unrle(target)
    if a.shape != b.shape:
        raise ValueError('GT raster resolution differs; no implicit resizing')
    union=np.logical_or(a,b).sum()
    return float(np.logical_and(a,b).sum()/union) if union else 0.


def join(row, gt):
    if gt.get('capture') != row['capture'] or gt.get('source_indices') != row['source_indices']:
        raise ValueError('GT capture/anchor binding differs')
    out=[]
    for obj in row['objects']:
        key=f"{row['item_id']}:{obj['name']}"
        target=gt.get('targets',{}).get(key)
        if not target or not target.get('binding_reviewed') or not target.get('annotation_complete'):
            out.append(dict(key=key,stage='U',reason='missing reviewed complete instance annotation'))
            continue
        masks=target['masks']
        if set(masks) != {str(x) for x in row['source_indices']}:
            raise ValueError('GT must describe every input frame, including zero masks')
        def target_at(frame, mask):
            h,w=mask['size']; source=str(row['source_indices'][int(frame)-1])
            return masks[source][f'{h}x{w}']
        visible=any(unrle(v).any() for frames in masks.values() for v in frames.values())
        proposed=any(iou(p['mask'],target_at(p['frame'],p['mask'])) > .5 for p in obj['proposals'])
        chosen=obj['selected_masks']
        active=[(f,m) for f,m in chosen.items() if unrle(m).any()]
        matched=[f for f,m in active if iou(m,target_at(f,m)) > .5]
        correct=bool(active) and 2*len(matched)>=len(active)
        outside=None
        box=obj.get('fitted_box')
        if box and target.get('world_alignment_reviewed'):
            T=np.asarray(target['reader_world_to_gt_world'],float)
            if T.shape!=(4,4) or not np.isfinite(T).all() or not np.allclose(T[3],[0,0,0,1]):
                raise ValueError('invalid rigid transform')
            R=T[:3,:3]
            if not np.allclose(R.T@R,np.eye(3),atol=1e-6) or abs(np.linalg.det(R)-1)>1e-6:
                raise ValueError('GT alignment must not fit or change metric scale')
            p=(T @ np.r_[box['world']['centroid'],1])[:3].tolist()
            outside=outside_obb(p,**target['full_obb'])
        evidence=dict(visible=bool(visible),proposed=bool(proposed),selected_correct=bool(correct),
                      selected_correct_frames=len(set(matched)),outside_box_m=outside)
        label,why=stage(evidence)
        out.append(dict(key=key,stage=label,reason=why,evidence=evidence))
    return out


def main():
    # Both entry points use the authenticated, trailer-less capture reader.
    sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
    from gpkg.join_capture import main as current_main
    current_main()


if __name__=='__main__':main()
