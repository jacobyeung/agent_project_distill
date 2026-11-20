"""Inspect staged annotations and refuse an unsupported lossless join conversion."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import zipfile
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
STAGED=Path('/scratch/jjyeung/orch_n30/cont_ops24_c/gt')


def header(archive,name):
    with archive.open(name+'.npy') as f:
        version=np.lib.format.read_magic(f)
        shape,fortran,dtype=np.lib.format._read_array_header(f,version)
    return dict(shape=list(shape),fortran_order=fortran,dtype=str(dtype))


def inspect_file(path):
    # Read each ZIP directory, array headers, and small metadata arrays only.
    # Pixel arrays are not decompressed after the resolution check has failed.
    with zipfile.ZipFile(path) as archive:
        headers={n[:-4]:header(archive,n[:-4]) for n in archive.namelist() if n.endswith('.npy')}
    with np.load(path,allow_pickle=False) as z:
        arrays={k:z[k] for k in ('ids','labels','frame_indices','valid','c2w','K_frames',
                                 'obb_centroid','obb_lengths','obb_axes') if k in z.files}
    ids=arrays.get('ids',np.array([]));labels=arrays.get('labels',np.array([]))
    if ids.ndim!=1 or labels.ndim!=1 or len(ids)!=len(labels) or len(set(ids.tolist()))!=len(ids):
        raise ValueError('instance inventory differs')
    missing=[]
    shape=headers.get('inst',{}).get('shape')
    if shape!=[32,480,640]:
        missing.append('No 480x640 per-instance raster; inst has shape '+str(shape)+'. Upsampling cannot recover lost boundary/occlusion labels.')
    if shape!=[32,240,320]:
        missing.append('No 240x320 selected-mask raster; portrait pixels require a documented anchor-image mapping, not an assumed transpose.')
    for k in ('camera_axes','world_axes','pixel_centres','metric_units','obb_axes_layout','obb_lengths_kind'):
        if k not in headers:missing.append('No explicit '+k+' metadata.')
    if 'valid' in arrays and not arrays['valid'].all():missing.append('Some GT frames are invalid.')
    return dict(path=str(path),bytes=path.stat().st_size,headers=headers,
                ids=ids.tolist(),labels=labels.tolist(),frame_indices=arrays.get('frame_indices',np.array([])).tolist(),
                valid_frames=int(arrays.get('valid',np.array([],bool)).sum()),
                cameras=arrays.get('c2w',np.array([])).tolist(),
                intrinsics=arrays.get('K_frames',np.array([])).tolist(),
                boxes={k:arrays[k].tolist() for k in ('obb_centroid','obb_lengths','obb_axes') if k in arrays},
                missing=missing,annotation_complete=False)


def names(ref):
    found=[]
    for call in ref['calls']:
        m=re.fullmatch(r'<ground obj="([^"]+)" mode="box">',call['call'])
        if m:found.append(m[1])
    if found:
        if len(found)!=2:raise ValueError('expected exactly two recorded object calls')
        return found,'recorded ground calls'
    # The sole routing omission has an explicit, unambiguous noun pair in its question.
    m=re.fullmatch(r"In inches, what's the smallest distance between the (.+) and the (.+) using their closest points\?",ref['task']['question'])
    if not m:raise ValueError('non-caller object names require explicit annotation')
    return list(m.groups()),'literal question noun phrases; no recorded calls'


def bind(name,record):
    if record is None:return dict(status='U',reason='missing GT file',instance_id=None)
    # Exact text only: no synonyms, stemming, singularization, or fuzzy matching.
    matches=[i for i,label in zip(record['ids'],record['labels']) if label==name]
    if len(matches)!=1:
        return dict(status='U',reason='ambiguous exact label' if matches else 'missing exact label',
                    instance_id=None,candidates=matches)
    return dict(status='bound',instance_id=matches[0],label=name)


def audit(staged=STAGED):
    refs=json.loads((ROOT/'kit2/kit/rerun2/items544.json').read_text())['items']
    manifest=json.loads((ROOT/'kit2/kit/rerun2/gt_staging.json').read_text())['files']
    records={};missing=[]
    for row in manifest:
        path=Path(staged)/row['relative_path']
        if path.is_file():records[row['capture']]=inspect_file(path)
        else:missing.append(row['capture'])
    occurrences=[];frame_matches=0;per_item=[]
    for ref in refs:
        rec=records.get(ref['capture']);objects,source=names(ref)
        if rec:
            shared=sorted(set(ref['source_indices'])&set(rec['frame_indices']))
            exact=rec['frame_indices']==ref['source_indices'];frame_matches+=exact
        else:shared=[];exact=False
        per_item.append(dict(item_id=ref['item_id'],capture=ref['capture'],anchor_indices_match=exact,
                             shared_source_indices=shared,missing_source_indices=sorted(set(ref['source_indices'])-set(shared))))
        for name in objects:
            occurrences.append(dict(item_id=ref['item_id'],capture=ref['capture'],name=name,name_source=source,
                                    binding=bind(name,rec),join_stage='U',annotation_complete=False))
    counts=Counter(x['binding'].get('reason','unique exact label') for x in occurrences)
    return dict(status='BLOCKED',converted_items=0,total_captures=len(manifest),available_captures=len(records),
                missing_captures=len(missing),missing_capture_names=missing,total_object_occurrences=len(occurrences),
                unique_label_bindings=sum(x['binding']['status']=='bound' for x in occurrences),
                binding_counts=dict(counts),items_with_gt=sum(r['capture'] in records for r in refs),
                raster_shapes=dict(Counter('x'.join(map(str,r['headers']['inst']['shape'])) for r in records.values())),
                items_without_gt=sum(r['capture'] not in records for r in refs),items_with_exact_anchor_indices=frame_matches,
                files=records,items=per_item,occurrences=occurrences,
                refusal='Full join requires independently rasterized 480x640 instance masks at every exact anchor, '
                        'valid annotation flags, and documented camera/pixel/metric/OBB conventions. '
                        'The existing 240x320 raster cannot establish the missing finer-grid truth. '
                        'No reader capture exists locally, so no metric alignment residual was measured.',
                alignment=dict(performed=False,fit_scale=False,
                               required='Documented common camera axes and source indices; use one rigid SE(3) fit to shared camera poses, '
                                        'then report per-frame translation and rotation residuals. Never use object boxes to fit the transform.'))


def convert(path,ref):
    info=inspect_file(path)
    missing=list(info['missing'])
    if info['frame_indices']!=ref['source_indices']:missing.append('GT source indices differ from reader anchors.')
    raise ValueError('GT conversion refused: '+' '.join(missing or ['Annotation conventions have no reviewed adapter.']))


def main():
    p=argparse.ArgumentParser();p.add_argument('--staged',type=Path,default=STAGED)
    p.add_argument('--out',type=Path,default=ROOT/'gt/INSPECTION.json');p.add_argument('--inspect-only',action='store_true')
    args=p.parse_args();value=audit(args.staged)
    args.out.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in value.items() if k not in ('files','items','occurrences','missing_capture_names')},indent=2))
    if not args.inspect_only:raise SystemExit('GT conversion refused; see inspection evidence')


if __name__=='__main__':
    import sys
    if len(sys.argv)>1 and sys.argv[1]=='convert':
        sys.path.insert(0,str(ROOT))
        from gt.v2 import main as convert_main
        convert_main(sys.argv[2:])
    else:
        main()
