"""Export T1 choices through ofs and replay only the 31 tuning scans."""
import argparse
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import numpy as np
from scipy import ndimage
from probe_common import *
from extract import load_payload,candidate_mask


def run(a):
    sys.path[:0]=[str(O/'verify_kit/work/x2_vendor'),str(O/'verify_kit/work/x2_vendor/work/vendor')]
    from ofs import core
    from rk import programs,report,sets
    result=json.loads(Path(a.t1).read_text())
    if result['rules_sha256']!=sha256(RULES_PATH):raise ValueError('T1 rule pin differs')
    groups,_,_,pins=candidate_inputs();selected={r['object_id']:r for r in result['predictions']}
    if set(selected)!={g['object_id'] for g in groups}:raise ValueError('Selections do not cover tuning cohort')
    for r in selected.values():gate.check_row(r,'tuning')
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True);export=out/'exports';export.mkdir(exist_ok=True)
    for scene in sorted({g['scene'] for g in groups}):
        gate.check_row(dict(scene=scene),'tuning')
        gs=sorted([g for g in groups if g['scene']==scene],key=lambda g:g['name'])
        names=[g['name'] for g in gs];chosen={};values=core.empty_values(len(names));payloads={}
        for q,g in enumerate(gs):
            pred=selected[g['object_id']]
            cid=pred['fused_candidate_id'] if a.fused else pred['candidate_id']
            if cid is None:raise ValueError('Requested fusion is unmeasured')
            c=next(c for c in g['candidates'] if c['candidate_id']==cid);chosen[g['name']]=NS(id=cid)
            for member in c['members']:
                ref=member['mask_ref'];path=ref['path'];gate.guard_path(path)
                if path not in payloads:payloads[path]=load_payload(path)
                mask=candidate_mask(member,payloads[path]);k=member['slot']
                small=ndimage.zoom(mask,(80/mask.shape[0],112/mask.shape[1]),order=0,prefilter=False)
                if not small.any():continue
                values['mask'][q,k]=small;values['prob'][q,k]=1;values['iou'][q,k]=c['peak']
                row,col=np.unravel_index(np.argmax(ndimage.distance_transform_edt(small)),core.SHAPE)
                values['uv'][q,k]=np.rint([(col+.5)/112*1000,(row+.5)/80*1000])
        values['frame_prob']=values['prob'].copy();values['area']=values['mask'].mean(axis=(-1,-2))
        core.export(export,scene,names,chosen,gs[0]['frame_indices'],values=values,
                    audit=dict(arm=result['arm'],selection='Frozen training-room probe; tuning diagnostic only',t1_sha256=sha256(a.t1)))
    scenes=sorted({g['scene'] for g in groups})
    routed=programs.run(NS(mdg_export=str(export),set='dev',scenes=','.join(scenes),limit_per_type=None,out=str(out/'routed'),
                           heads=a.heads,allow_gt_substitution=False,gates=False))
    # Use a direct export explicitly supplied by the orchestrator; never infer a read cohort.
    keys={str(r['qid']) for r in routed};direct=[]
    for r in routed:gate.check_row(r,'tuning')
    with Path(a.direct).open() as f:
        for line in f:
            row=json.loads(line)
            if str(row.get('qid',row.get('example_id'))) in keys:
                if 'scene' in row:gate.check_row(row,'tuning')
                direct.append(row)
    truths={k:v for k,v in sets.answers('dev').items() if str(k) in keys}
    summary=report.make_report(routed,direct,truths,'dev',4000,17)
    if summary['unpaired_routed']!=0:raise ValueError('Routed/direct/GT cohort differs')
    output_metrics(out/'ROUTED.json',dict(arm=result['arm'],split='tuning',diagnostic=True,gains=summary,
                    note='Unmodified X2 scorer and scene bootstrap; decision intervals remain object-paired'),
                    [a.t1,a.direct,RULES_PATH],vars(a))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--t1',required=True);p.add_argument('--out',required=True)
    p.add_argument('--fused',action='store_true');p.add_argument('--direct',required=True)
    p.add_argument('--heads',default=str(O/'ttower/work/geo/heads_g3s64_vcd'));run(p.parse_args())
