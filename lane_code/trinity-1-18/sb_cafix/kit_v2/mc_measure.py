"""Mask measurements with sb_maskfail's unchanged functions (metrics, classify, dist, stats), loaded by declaration only."""
import ast, collections
from types import SimpleNamespace as NS
import numpy as np
import mc_common as C

ANALYZE = C.MASKFAIL/'analyze.py'
_MF = None


def maskfail():
    """sb_maskfail/analyze.py's declarations without executing its module body (which imports and mkdirs)."""
    global _MF
    if _MF is None:
        source = C.read(ANALYZE).decode()
        tree = ast.parse(source)
        keep = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name in ('metrics', 'classify', 'dist', 'stats'))
                or (isinstance(n, ast.Assign) and any(getattr(t, 'id', None) in ('THRESH', 'KINDS') for t in n.targets))]
        scope = dict(np=np, collections=collections)
        exec(compile(ast.Module(keep, []), str(ANALYZE), 'exec'), scope)
        _MF = NS(**{k: scope[k] for k in ('metrics', 'classify', 'dist', 'stats', 'THRESH', 'KINDS')})
    return _MF


def frame_record(base, mask, inst_f, raster_f, iid, classes, valid):
    """One sb_maskfail-format record for a mask on one anchor; pool fields (deployed_best_iou, teacher) come from base."""
    mf = maskfail()
    target = inst_f == iid
    value, inter, area = mf.metrics(mask, target)
    allids, counts = np.unique(inst_f[mask], return_counts=True)
    annotated = [(int(k), int(n)) for k, n in zip(allids, counts) if int(k) in classes]
    dominant = max(annotated, key=lambda v: (v[1], -v[0])) if annotated else (None, 0)
    covered = [k for k, n in annotated if area and n/area >= .1 and n/int(np.count_nonzero(inst_f == k)) >= .1]
    r = dict(base, iou=value if valid else None, valid=bool(valid), visible=bool(target.any()), served_area=area,
             share=float(np.mean(raster_f == iid)), precision=inter/area if area else 0., merged=len(covered) >= 2, merged_ids=covered,
             dominant_id=dominant[0], dominant_class=classes.get(dominant[0]), dominant_fraction=dominant[1]/area if area else 0.)
    r['failure_kinds'] = {str(t): mf.classify(r, t) for t in mf.THRESH}
    r['failure_kind'] = r['failure_kinds']['0.5']
    return r


def frame_recall(records, share=.01, t=.5):
    """Visible operand-frames with the instance above `share` of the frame where the mask has IoU >= t."""
    rows = [r for r in records if r['valid'] and r['visible'] and r['share'] > share]
    hit = sum((r['iou'] or 0) >= t for r in rows)
    return dict(frames=len(rows), hits=hit, rate=hit/len(rows) if rows else None)


def false_presence(records):
    rows = [r for r in records if r['valid'] and not r['visible']]
    return dict(absent_frames=len(rows), with_mask=sum(r['served_area'] > 0 for r in rows))


def unique(records):
    seen = {}
    for r in records:
        seen[(r['capture'], r['instance'], r['frame'])] = r
    return list(seen.values())
