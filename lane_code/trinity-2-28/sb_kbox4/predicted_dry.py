"""Price deployed and gathered dry-run arms, preserving the reader socket."""
import gzip,json,sys
import numpy as np
from adapters import ROOT,READER
from dryrun import read
from predicted import replay,gathered_masks
from box_math import FUSIONS
from pricing import lift_frames,session_distance,object_diagnostics

def seed_instance(seed,gt,allowed_ids):
    """Match seed members by IoU; keep that instance fixed after gathering."""
    from scipy.ndimage import zoom
    counts={};sums={}
    for p in seed:
        truth=gt['inst'][p.frame-1]
        truth=zoom(truth,(p.mask.shape[0]/truth.shape[0],p.mask.shape[1]/truth.shape[1]),order=0,prefilter=False)
        hits=[]
        for iid in np.unique(truth):
            if int(iid) not in allowed_ids:continue
            m=truth==iid;union=np.count_nonzero(p.mask|m)
            iou=np.count_nonzero(p.mask&m)/union if union else 0.
            if iou>.5:hits.append((iou,int(iid)))
        if hits:
            iou,iid=max(hits,key=lambda q:(q[0],-q[1]));counts[iid]=counts.get(iid,0)+1;sums[iid]=sums.get(iid,0.)+iou
    return min(counts,key=lambda i:(-counts[i],-sums[i],i)) if counts else None

def run(c,rows,gt,geo,G,labels,boxes):
    import torch
    torch.set_num_threads(8)
    from selector_head import load_head
    from predicted import member_precision
    from replay_check import run as replay_run
    directory=READER/'heads/selector/work/run_iso'
    for ext in ('json','safetensors'):read(directory/f'selector_head.{ext}')
    head,_=load_head(directory)
    checks,states,tables=replay_run(c,geo,head)
    items=[];parity=[];objects={};gather_stats={}
    for name,result in states.items():
        k=result['A0'];m=np.zeros((32,240,320),bool)
        if k>=0:
            for frame,mask in result['accepted'][k]['masks'].items():m[int(frame)-1]=mask
        objects[name]=lift_frames(name,m,geo,G)
        gm,seed,members=gathered_masks(result,k)
        objects[(name,'gather')]=lift_frames(name,gm,geo,G)
        iid=seed_instance(seed,gt,c["gt_name_ids"].get(name,[]))
        precision=member_precision(members,gt['inst']==iid) if iid is not None else dict(members=len(members),correct=None,precision=None)
        gather_stats[name]=dict(seed_instance=iid,frames_before=[p.frame for p in seed],frames_after=[p.frame for p in members],**precision)
    for row in rows:
        for arm,rule,is_gather in [('A0_deployed','best1',False)]+[('DRY_A4_gathered_'+r,r,True) for r in FUSIONS]:
            objs={n:objects[(n,'gather') if is_gather else n] for n in row['operands']}
            pred,refusal,raw,printed=session_distance(row,geo,objs,G,rule)
            diagnostics={n:object_diagnostics(gt['inst']==row['gt_instances'][n],objs[n],printed.get(n),boxes.get((c['canonical'],row['gt_instances'][n]))) for n in objs}
            items.append(dict(stage='dry_run',arm=arm,row_id=row['id'],room=c['room'],capture=c['canonical'],split='train',dataset=c['canonical'].split('/')[0],prediction=pred,label=labels[row['id']]['corrected'],refusal_code=refusal,member_frames={n:objs[n]['frames'] for n in objs},box=printed,diagnostics=diagnostics,gather={n:gather_stats[n] for n in objs} if is_gather else None))
            if arm=='A0_deployed':
                # The reference uses the copied reader's socket and its own lifting.
                def propose(name):
                    r=states[name]
                    return [dict(candidate_id=a['candidate_id'],masks=a['masks']) for a in r['accepted']],name
                sock=G.StageOneSocket(propose,lambda name:states[name]['A0'],(240,320),32)
                s=G.ground_session(geo,sock)
                for name in row['operands']:s.execute(f'<ground obj="{name}" mode="box">')
                a,b=row['operands'];response=s.execute(f'<gap a="{a}" b="{b}" rule="box_grid_5cm">')
                expected=f'distance {pred:.2f} m' if pred is not None else refusal
                parity.append(dict(row_id=row['id'],passed=response==expected,got=expected,reader=response))
    return items,checks,parity
