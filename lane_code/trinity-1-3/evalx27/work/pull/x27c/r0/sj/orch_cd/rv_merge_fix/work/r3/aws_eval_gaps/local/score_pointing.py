"""Score pinned pointing outputs on Trinity with toolprog's GTGround masks."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'evaluator'))
from pointing import parsed
from common import pin, save, sha
from erosion_bind import TOOL, bounded_json, ground, programs


def read_records(path):
    path = Path(path)
    if path.stat().st_size > 64*1024*1024:
        raise ValueError('Output journal exceeds 64 MB bound')
    rows = []
    with path.open() as f:
        for line in f:
            if line.strip():rows.append(json.loads(line))
    return rows


def indexed(rows, benchmark):
    result = {}
    for row in rows:
        if row.get('benchmark') != benchmark:continue
        key = str(row['example_id'])
        if key in result:raise ValueError('Duplicate result ID: '+key)
        result[key] = row
    return result


def score_mask(text, masks):
    """Return per-item credit; malformed replies remain in the denominator."""
    import numpy as np
    from scipy.ndimage import binary_erosion
    p = parsed(text)
    inside = 0.0
    if masks and p['points']:
        union = np.zeros_like(masks[0],dtype=bool)
        for mask in masks:
            eroded = binary_erosion(mask,iterations=2)
            # SPEC v3.4 / GTGround.eroded retains small masks with <8 interior pixels.
            union |= eroded if eroded.sum() >= 8 else mask
        h,w = union.shape
        xy = np.asarray(p['points'])
        xs = np.clip((xy[:,0]/1000*w).astype(int),0,w-1)
        ys = np.clip((xy[:,1]/1000*h).astype(int),0,h-1)
        inside = float(union[ys,xs].mean())
    return dict(**p,visible=bool(masks),inside=inside,none_score=float(p['none']))


def score_rows(rows, membership, gt_root=TOOL/'gt/scannet', programs_path=TOOL/'tp/programs.py'):
    records = indexed(rows,'pointing')
    expected = {r['id']:r for r in membership['items']}
    extra = sorted(set(records)-set(expected))
    if extra:raise ValueError('Unexpected pointing IDs: '+str(extra))
    if membership.get('review_only'):raise ValueError('Synthetic membership cannot produce real scores')
    module = programs(programs_path)
    by_scene = defaultdict(list)
    for item in expected.values():by_scene[item['scene']].append(item)
    scored = []
    for scene, items in sorted(by_scene.items()):
        gg = ground(scene,gt_root,module)
        for it in items:
            if not gg.gt.valid[it['frame']-1]:raise ValueError('Selected GT frame became invalid: '+it['id'])
            masks = [m for _,m in gg.masks(it['obj'],it['frame'])]
            row = records.get(it['id'])
            if row is None or row.get('status')!='complete':continue
            if (row.get('scene'),row.get('frame')) != (scene,it['frame']):
                raise ValueError('Pointing result scene/frame differs: '+it['id'])
            value = score_mask(row['raw_generation'],masks)
            scored.append(dict(example_id=it['id'],scene=scene,**value,
                hit_token_cap=bool(row.get('hit_token_cap')),output_tokens=row.get('output_tokens')))
        del gg
    counts = {v:sum(r['visible']==v for r in scored) for v in (True,False)}
    complete = len(scored)==len(expected)
    if complete and (counts[True],counts[False]) != (650,350):
        raise ValueError('GT visibility differs from the 650/350 binding')
    return dict(expected=len(expected),completed=len(scored),missing_or_failed=sorted(set(expected)-{r['example_id'] for r in scored}),
                visible=counts[True],absent=counts[False],cap_hits=sum(r['hit_token_cap'] for r in scored),
                parse_failures=sum(r['parse_failed'] for r in scored),
                inside_rate=sum(r['inside'] for r in scored if r['visible'])/counts[True] if counts[True] else None,
                none_rate=sum(r['none_score'] for r in scored if not r['visible'])/counts[False] if counts[False] else None,
                complete=complete,items=scored)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--items',required=True,type=Path)
    p.add_argument('--base',type=Path,help='Optional item-paired base journal')
    p.add_argument('--membership',required=True,help='absolute-path@sha256')
    p.add_argument('--gt-root',type=Path,default=TOOL/'gt/scannet')
    p.add_argument('--programs',type=Path,default=TOOL/'tp/programs.py')
    p.add_argument('--output',required=True,type=Path)
    a = p.parse_args()
    m = pin(a.membership)
    if sha(m['path'])!=m['sha256']:raise ValueError('Pointing membership pin differs')
    membership = bounded_json(m['path'])
    if membership['sources']['programs']!=sha(a.programs):raise ValueError('GTGround source differs from bind')
    result = score_rows(read_records(a.items),membership,a.gt_root,a.programs)
    if a.base:
        from erosion_report import pointing_pairs
        base = score_rows(read_records(a.base),membership,a.gt_root,a.programs)
        result['paired'] = pointing_pairs(base,result)
    save(a.output,result)
    print(json.dumps({k:v for k,v in result.items() if k!='items'},allow_nan=False))


if __name__=='__main__':main()
