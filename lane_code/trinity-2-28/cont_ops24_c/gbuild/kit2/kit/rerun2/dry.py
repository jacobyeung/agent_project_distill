"""Fabricated full-schema capture; no model or image files are opened."""
import copy
import gzip
import json
from pathlib import Path
import numpy as np
from capture import Writer,rle,validate
from parity import check


def fixture(ref):
    m=np.zeros((480,640),bool);m[100:180,200:300]=True
    small=m[::2,::2]
    proposals=[dict(id=f'{f}:0',frame=f,source_index=ref['source_indices'][f-1],
                    prompt='object',score=.9,presence=.8,mask=rle(m)) for f in (1,2,3)]
    masks={str(f):rle(small) for f in (1,2,3)}
    obj=dict(name='object',proposals=proposals,
             linked_tracks=[dict(id='object:000',members=[p['id'] for p in proposals],features={})],
             early_lifts=[],early_rejections=[],
             candidates=[dict(id='object:000',masks=masks,features={})],
             selector=dict(inputs=[[.5]*58],slots=[1.,2.],null_index=1,choice=0,
                           rule='candidates_argmax',invoked=True),selected_masks=masks,
             lift=dict(centroid=[0.,0.,0.],extent=[1.,1.,1.],frames=[1,2,3],frame_count=3),
             fitted_box=dict(world=dict(centroid=[0.,0.,0.],axesLengths=[1.,1.,1.],normalizedAxes=np.eye(3).tolist()),f1={}))
    geometry=dict(K=np.tile(np.eye(3),(32,1,1)).tolist(),canvas_to_source=np.tile(np.eye(3),(32,1,1)).tolist(),
                  camera_to_world_metric=np.tile(np.eye(4),(32,1,1)).tolist(),
                  camera_to_world_unscaled=np.tile(np.eye(4),(32,1,1)).tolist(),scale=1.,
                  source_indices=ref['source_indices'],reference_source_frame=ref['source_indices'][0],
                  camera_axes='x_right_y_down_z_forward',world_axes='x_right_y_heading_z_up',
                  depth_kind='optical_axis',pixel_centres='edge_origin_half',gravity_up=[0,0,1],
                  depth_scale_count=1,pose_scale_count=1,identity='synthetic',depth_grid_sha256='synthetic')
    row=dict(schema='ground-capture-v1',item_id=ref['item_id'],capture=ref['capture'],
             source_indices=ref['source_indices'],dense_indices=list(range(64)),
             geometry=geometry,objects=[obj],calls=copy.deepcopy(ref['calls']),answer_pass=False,synthetic=True)
    gt_masks={str(f):{'480x640':rle(m if i<3 else np.zeros_like(m)),
                      '240x320':rle(small if i<3 else np.zeros_like(small))}
              for i,f in enumerate(ref['source_indices'])}
    target=dict(binding_reviewed=True,annotation_complete=True,world_alignment_reviewed=True,
                instance_id='synthetic:0',masks=gt_masks,reader_world_to_gt_world=np.eye(4).tolist(),
                full_obb=dict(center=[0,0,0],axes=np.eye(3).tolist(),full_lengths=[1,1,1]))
    gt=dict(capture=ref['capture'],source_indices=ref['source_indices'],targets={ref['item_id']+':object':target})
    return row,gt


def dry_run(out, rows, frames, step):
    from join import join
    out.mkdir(parents=True,exist_ok=False)
    row,gt=fixture(rows[0]); validate(row)
    # Every stored item is checked, with fabricated identity returns only.
    for ref in rows:check(ref['calls'],copy.deepcopy(ref['calls']),0.)
    changed=copy.deepcopy(row['calls'])
    gap=next(c for c in changed if c['call'].startswith('<gap'))
    gap['response']='distance 9999.00 m'
    rejected=False
    try:check(rows[0]['calls'],changed,0.)
    except ValueError:rejected=True
    assert rejected and join(row,gt)[0]['stage']=='S5'
    path=out/'synthetic.jsonl.gz';w=Writer(path);w.append(row);w.close()
    with gzip.open(path,'rt') as f:validate(json.loads(next(f)))
    report=dict(cpu_only=True,step=step,requested_frames=frames,items=len(rows),
                calling_items=sum(bool(r['calls']) for r in rows),
                ground_calls=sum(c['call'].startswith('<ground') for r in rows for c in r['calls']),
                synthetic_compressed_bytes_per_item=w.bytes,
                synthetic_extrapolation_150_bytes=w.bytes*150,output_cap_bytes=1_900_000_000,
                real_bytes_per_item=None,synthetic_parity_items=len(rows),negative_parity_rejected=rejected,
                join_stage='S5',reached='argument parsing, pinned item list, synthetic schema/RLE write/read, fabricated all-item parity and synthetic GT join',
                not_reached=['reader runtime imports','RGB decode','checkpoint/tower/SAM loading','prefill','real masks','GPU parity'],
                optional_arm_status='requires variable-frame adapter' if frames!=32 else 'baseline',trusted=False)
    (out/'DRY.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
