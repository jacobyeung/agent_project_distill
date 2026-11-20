"""Compare predictions at the GT grid; preserve separate extent readings."""
import copy
import importlib.util
from pathlib import Path
import sys
from gpkg.grid import resize
from gpkg.runtime.c import rle, unrle

KIT = Path(__file__).resolve().parents[1]/'kit2/kit/rerun2'
sys.path.insert(0, str(KIT))
_spec = importlib.util.spec_from_file_location('kit_join_v2', KIT/'join.py')
legacy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(legacy)


def join(row, gt):
    if gt.get('schema') != 'gt-adapter-v2':
        return legacy.join(row, gt)
    normalized = dict(row, objects=[])
    for obj in row['objects']:
        value = dict(obj)
        value['proposals'] = [dict(p, mask=rle(resize(unrle(p['mask']), (240, 320))))
                              for p in obj['proposals']]
        value['selected_masks'] = {f:rle(resize(unrle(m), (240,320))) for f,m in obj['selected_masks'].items()}
        normalized['objects'].append(value)
    result = legacy.join(normalized, gt)
    for value in result:
        target = gt.get('targets', {}).get(value['key'], {})
        value.update(alignment=gt.get('alignment'), extent_rule=target.get('extent_rule'),
                     binding=target.get('binding'), orientation=gt.get('orientation'))
    if gt.get('dataset') == 'scannet':
        alt = copy.deepcopy(gt)
        for target in alt['targets'].values():
            if target.get('half_extent_obb'):
                target['full_obb'] = target['half_extent_obb']
        second = {r['key']:r for r in legacy.join(normalized, alt)}
        for value in result:
            other = second[value['key']]
            value['scannet_extent_ambiguous'] = True
            value['extent_readings'] = dict(as_full={k:value.get(k) for k in ('stage','reason','evidence')},
                                           as_half={k:other.get(k) for k in ('stage','reason','evidence')})
            if value['stage'] != other['stage']:
                value.update(stage='U', reason='ScanNet extent readings disagree')
    return result
