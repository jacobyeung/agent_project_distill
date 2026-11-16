"""Score video pointing on Trinity; never ship GT masks or visibility labels."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'evaluator'))
from common import pin,save,sha
from erosion_bind import TOOL,bounded_json,ground,programs,validate_pointing
from pointing_video import parse_output,VARIANTS
from score_pointing import read_records

PARSINGS=('xy_1000','yx_1000','processed_pixels','fractions')


def eroded_union(masks):
    import numpy as np
    from scipy.ndimage import binary_erosion
    if not masks:return None
    union=np.zeros_like(masks[0],dtype=bool)
    for mask in masks:
        eroded=binary_erosion(mask,iterations=2)
        union |= eroded if eroded.sum()>=8 else mask
    return union


def coordinates(point,parsing,processed_height_width):
    if point is None:return None
    a,b=point
    if parsing=='yx_1000':a,b=b,a
    if parsing in ('xy_1000','yx_1000'):x,y=a/1000,b/1000
    elif parsing=='fractions':x,y=a,b
    elif parsing=='processed_pixels':
        h,w=processed_height_width
        if not (0<=a<w and 0<=b<h):return None
        x,y=a/w,b/h
    else:raise ValueError('Unknown coordinate parsing')
    if not (0<=x<=1 and 0<=y<=1):return None
    return x,y


def hit(xy,mask):
    if xy is None or mask is None:return False
    h,w=mask.shape;x,y=xy
    return bool(mask[min(int(y*h),h-1),min(int(x*w),w-1)])


def score_mask(text,masks,processed_height_width,neighbors=None):
    """Keep malformed responses in denominators, and diagnose all four parsings."""
    p=parse_output(text);mask=eroded_union(masks)
    result=dict(visible=bool(masks),parse_failed=p['parse_failed'],explicit_none=p['none'],parsings={})
    h,w=processed_height_width
    if type(h) is not int or type(w) is not int or min(h,w)<=0:raise ValueError('Invalid processed frame size')
    for parsing in PARSINGS:
        xy=coordinates(p['point'],parsing,processed_height_width)
        invalid=p['point'] is not None and xy is None
        result['parsings'][parsing]=dict(inside=float(hit(xy,mask)),none_score=float(xy is None),
                                        malformed=bool(p['parse_failed'] or invalid))
    xy=coordinates(p['point'],'xy_1000',processed_height_width)
    result['neighbors']={}
    for name,neighbor_masks in (neighbors or {}).items():
        inside=hit(xy,eroded_union(neighbor_masks))
        result['neighbors'][name]=dict(inside=float(inside),exclusive_inside=float(inside and not hit(xy,mask)))
    return result


def summarize(items,expected):
    visible=[r for r in items if r['visible']];absent=[r for r in items if not r['visible']]
    def mean(values):return sum(values)/len(values) if values else None
    result=dict(expected=expected,completed=len(items),visible=len(visible),absent=len(absent),
        complete=len(items)==expected,malformed_rate=mean([float(r['parse_failed']) for r in items]),
        explicit_none_rate=mean([float(r['explicit_none']) for r in absent]),parsings={},neighbors={})
    for parsing in PARSINGS:
        result['parsings'][parsing]=dict(
            inside_rate=mean([r['parsings'][parsing]['inside'] for r in visible]),
            none_rate=mean([r['parsings'][parsing]['none_score'] for r in absent]),
            malformed_rate=mean([float(r['parsings'][parsing]['malformed']) for r in items]))
    for name in ('k-1','k+1'):
        eligible=[r['neighbors'][name] for r in items if name in r['neighbors']]
        result['neighbors'][name]=dict(eligible=len(eligible),inside_rate=mean([r['inside'] for r in eligible]),
                                     exclusive_inside_rate=mean([r['exclusive_inside'] for r in eligible]))
    result.update(result['parsings']['xy_1000'])
    return result


def score_rows(rows,membership,gt_root=TOOL/'gt/scannet',programs_path=TOOL/'tp/programs.py'):
    validate_pointing(membership)
    expected={it['id']:it for it in membership['items']}
    records={}
    for row in rows:
        if row.get('benchmark')!='pointing_video':continue
        identity=(row.get('membership_id'),row.get('variant'))
        if identity[0] not in expected or identity[1] not in VARIANTS:raise ValueError('Unexpected video pointing identity')
        if identity in records:raise ValueError('Duplicate video pointing result')
        it=expected[identity[0]]
        if (row.get('example_id')!=identity[0]+':'+identity[1]
                or (row.get('scene'),row.get('obj'),row.get('frame'),row.get('source_index'))
                   !=(it['scene'],it['obj'],it['frame'],it['source_index'])):
            raise ValueError('Video pointing scene/object/frame differs')
        records[identity]=row
    by_scene=defaultdict(list)
    for it in expected.values():by_scene[it['scene']].append(it)
    module=programs(programs_path);scored=[];visibility={}
    for scene,items in sorted(by_scene.items()):
        if not any(records.get((it['id'],v),{}).get('status')=='complete' for it in items for v in VARIANTS):continue
        gg=ground(scene,gt_root,module)
        for it in items:
            if not any(records.get((it['id'],v),{}).get('status')=='complete' for v in VARIANTS):continue
            k=it['frame']
            if not gg.gt.valid[k-1]:raise ValueError('Selected GT frame became invalid')
            masks=[m for _,m in gg.masks(it['obj'],k)]
            visibility[it['id']]=bool(masks)
            neighbors={name:[m for _,m in gg.masks(it['obj'],j)]
                       for name,j in (('k-1',k-1),('k+1',k+1)) if 1<=j<=32 and gg.gt.valid[j-1]}
            for variant in VARIANTS:
                row=records.get((it['id'],variant))
                if row is None or row.get('status')!='complete':continue
                value=score_mask(row['raw_generation'],masks,row['processed_height_width'],neighbors)
                scored.append(dict(membership_id=it['id'],example_id=row['example_id'],variant=variant,
                                   scene=scene,**value))
        del gg
    if len(visibility)==1000 and sum(visibility.values())!=650:raise ValueError('GT visibility differs from 650/350 membership')
    variants={v:summarize([r for r in scored if r['variant']==v],len(expected)) for v in VARIANTS}
    for v in VARIANTS:
        have={r['membership_id'] for r in scored if r['variant']==v}
        variants[v]['missing_or_failed']=sorted(set(expected)-have)
    return dict(benchmark='pointing_video',variants=variants,items=scored,
        definitions=dict(inside_rate='Visible completed items; 2-pixel GTGround erosion with <8-pixel fallback.',
            none_rate='Absent completed items with no valid point under the given coordinate parsing, including malformed replies.',
            explicit_none_rate='Absent completed items with an explicit JSON null.',
            malformed_rate='Completed items with invalid JSON/schema or coordinates outside the parsing domain.',
            neighbors='Convention parsing; excludes out-of-range or invalid neighbor frames. Exclusive hits miss the target mask.'))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--items',required=True,type=Path,help='Merged items_ATTEMPT.jsonl')
    p.add_argument('--membership',required=True,help='absolute-path@sha256')
    p.add_argument('--gt-root',type=Path,default=TOOL/'gt/scannet')
    p.add_argument('--programs',type=Path,default=TOOL/'tp/programs.py')
    p.add_argument('--summary',type=Path,help='Matching merged summary_ATTEMPT.json for parity gate')
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();m=pin(a.membership)
    if sha(m['path'])!=m['sha256']:raise ValueError('Pointing membership pin differs')
    membership=bounded_json(m['path'])
    if membership['sources']['programs']!=sha(a.programs):raise ValueError('GTGround source differs from bind')
    rows=read_records(a.items)
    result=score_rows(rows,membership,a.gt_root,a.programs)
    parity=False
    if a.summary:
        summary=bounded_json(a.summary)
        if any(r.get('binding')!=summary['binding'] for r in rows):raise ValueError('Summary binding differs')
        parity=bool(summary.get('parity_pass')) and not summary.get('smoke_items')
    result.update(parity_pass=parity,numbers_status='eligible' if parity and all(v['complete'] for v in result['variants'].values()) else 'do not count')
    save(a.output,result)
    print(json.dumps({k:v for k,v in result.items() if k!='items'},allow_nan=False))


if __name__=='__main__':main()
