"""Bound local membership construction; never ship masks or visibility labels."""
import ast
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from types import SimpleNamespace

from common import ROOT, save, sha

TOOL = Path('/scratch/jjyeung/orch_cd/toolprog/work')


def bounded_json(path, limit=8*1024*1024):
    path = Path(path)
    if path.stat().st_size > limit:
        raise ValueError('Metadata exceeds read bound: '+str(path))
    return json.loads(path.read_text())


def stratified(rows, count=100, seed=17):
    groups = defaultdict(list)
    for row in rows:
        groups[row['question_type']].append(row)
    if not 0 < count <= len(rows) or count < len(groups):
        raise ValueError('Slice cannot cover all question types')
    sizes = {k: len(v)*count/len(rows) for k,v in groups.items()}
    quotas = {k: max(1, int(v)) for k,v in sizes.items()}
    while sum(quotas.values()) > count:
        k = min((k for k in quotas if quotas[k]>1), key=lambda k:(sizes[k]-quotas[k], k))
        quotas[k] -= 1
    while sum(quotas.values()) < count:
        k = max((k for k in quotas if quotas[k]<len(groups[k])), key=lambda k:(sizes[k]-quotas[k], k))
        quotas[k] += 1
    rng = random.Random(seed)
    result = []
    for key in sorted(groups):
        group = sorted(groups[key], key=lambda r:str(r['example_id']))
        result.extend(rng.sample(group, quotas[key]))
    return sorted(result, key=lambda r:str(r['example_id']))


def vsi_membership(rows_path, membership_path):
    from evalpath.items import load_items, MEMBERSHIP_SHA256
    if sha(membership_path) != MEMBERSHIP_SHA256:
        raise ValueError('VSI membership pin differs')
    for p in (rows_path, membership_path):
        bounded_json(p)
    spec = dict(benchmark='vsi500', rows=dict(path=str(rows_path),sha256=sha(rows_path)),
                membership=dict(path=str(membership_path),sha256=MEMBERSHIP_SHA256))
    rows = load_items(spec, dict(video_root='/unused'))
    selected = stratified(rows)
    value = dict(seed=17, count=100, parent_sha256=MEMBERSHIP_SHA256,
                 items=[dict(example_id=r['example_id'], question_type=r['question_type'],
                             scene=r['scene_name'], dataset=r['dataset']) for r in selected])
    path = ROOT/'inputs/vsi500_slice.json'
    save(path, value)
    return path


def source_contract(kit):
    path = Path(kit)
    if path.stat().st_size > 256*1024:
        raise ValueError('Pointing kit exceeds read bound')
    raw = path.read_bytes()
    values = {}
    for node in ast.parse(raw).body:
        if isinstance(node, ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in ('PROMPTS','MAX_NEW','SIZE'):
                values[node.targets[0].id] = ast.literal_eval(node.value)
    if values['MAX_NEW']['point'] != 48:
        raise ValueError('Pointing kit token contract changed')
    return dict(prompt=values['PROMPTS']['point'], thinking=False, max_tokens=48,
                image_processor_kwargs={}, kit_sha256=hashlib.sha256(raw).hexdigest(),
                video_readout_size=values['SIZE'])


def programs(path=TOOL/'tp/programs.py'):
    path = Path(path)
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location('_pointing_gt', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ground(scene, gt_root, module):
    import numpy as np
    import zipfile
    # GTGround needs only these arrays. Never decompress depth, poses, or OBBs.
    path = Path(gt_root)/(scene.split('/',1)[1]+'.npz')
    if path.stat().st_size > 128*1024*1024:
        raise ValueError('GT archive exceeds per-scene read bound')
    with zipfile.ZipFile(path) as z:
        if any(z.getinfo(k+'.npy').file_size > 64*1024*1024 for k in ('inst','ids','labels','valid')):
            raise ValueError('GT array exceeds expanded read bound')
    with np.load(path, allow_pickle=False) as z:
        inst, ids, labels, valid = (z[k] for k in ('inst','ids','labels','valid'))
    h,w = inst.shape[1:]
    if inst.ndim!=3 or inst.shape[0]!=32 or len(valid)!=32 or len(ids)!=len(labels):
        raise ValueError('GT raster shape differs from 32-frame contract')
    gt = SimpleNamespace(inst=inst, ids=ids, labels=[str(x) for x in labels], valid=valid, H=h, W=w)
    return module.GTGround(gt)


def pointing_membership(items_path, scenes_path, gt_root, kit, programs_path):
    scenes = bounded_json(scenes_path)
    items_path = Path(items_path)
    if items_path.stat().st_size > 8*1024*1024:
        raise ValueError('Pointing items exceed read bound')
    by_scene = defaultdict(list)
    seen = set()
    with items_path.open() as f:
        for line in f:
            it = json.loads(line)
            if it['kind'] != 'point' or not it['scene_key'].startswith('scannet/'):
                continue
            if it['id'] in seen:
                raise ValueError('Duplicate pointing ID')
            seen.add(it['id'])
            if not 1 <= it['frame'] <= 32:
                raise ValueError('Pointing frame outside 32 anchors')
            by_scene[it['scene_key']].append(it)
    module = programs(programs_path)
    groups = {True:[], False:[]}
    for scene, items in sorted(by_scene.items()):
        gg = ground(scene, gt_root, module)
        for it in sorted(items, key=lambda r:r['id']):
            if gg.gt.valid[it['frame']-1]:
                groups[bool(gg.masks(it['obj'],it['frame']))].append(it)
        # Drop GTGround's mask cache before opening the next scene.
        del gg
    rng = random.Random(17)
    chosen = []
    visibility = {}
    for visible, n in ((True,650),(False,350)):
        if len(groups[visible]) < n:
            raise ValueError('Too few pointing items for stratum '+str(visible))
        for it in rng.sample(sorted(groups[visible],key=lambda r:r['id']),n):
            row = scenes[it['scene_key']]
            indices = row['frame_indices']
            if len(indices) != 32 or indices != sorted(indices):
                raise ValueError('Pointing source selection differs')
            chosen.append(dict(id=it['id'], scene=it['scene_key'], frame=it['frame'], obj=it['obj'],
                video_rel=row['video_rel'], source_index=indices[it['frame']-1],
                frame_indices=indices, fps=row['fps'], total_num_frames=row['total_num_frames']))
            visibility[it['id']] = visible
    chosen.sort(key=lambda r:r['id'])
    contract = source_contract(kit)
    public = dict(seed=17, count=1000, items=chosen, contract=contract,
                  sources=dict(items=sha(items_path), scenes=sha(scenes_path), programs=sha(programs_path)))
    path = ROOT/'inputs/pointing_membership.json'
    save(path,public)
    save(ROOT/'inputs/pointing_private.json',dict(membership_sha256=sha(path), visibility=visibility,
         gt_root=str(gt_root), programs_path=str(programs_path)))
    return path


def validate_pointing(value, review=False):
    items = value['items']
    n = len(items) if value.get('grounding') is True else 1000
    if len(items) != n or len({r['id'] for r in items}) != n or value['seed'] != 17:
        raise ValueError('Pointing membership must contain 1000 unique seed-17 items')
    if value.get('review_only') and not review:
        raise ValueError('Synthetic pointing membership is review-only')
    if any('visible' in r or 'mask' in r for r in items):
        raise ValueError('Private GT cannot enter public membership')
    c = value['contract']
    if c['thinking'] is not False or c['max_tokens'] != 48 or c['image_processor_kwargs'] != {}:
        raise ValueError('Pointing generation contract differs')
