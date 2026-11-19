"""Adapt pinned f32 frame metadata to the unchanged reviewed reader."""
import json
from pathlib import Path
from h1eval.items import K, R0_PINS, checked, digest


def captures(items, root):
    root=Path(root)
    inventory=json.loads(checked(K/'inputs/r0dev/FRAMES_MANIFEST.json',R0_PINS['FRAMES_MANIFEST.json']).read_text())['scenes']
    result={}
    for item in items:
        key=item['native']
        if key in result:continue
        # The archive must preserve the producer's per-scene manifest bytes.
        path=root/key/'manifest.json'
        raw=json.loads(checked(path,inventory[key]['manifest_sha256']).read_text())
        frames=raw['frames']
        by_index={f['index']:f for f in frames}
        chosen=[]
        for i in item['frame_indices']:
            f=by_index[i];p=Path(f['path'])
            if p.is_absolute() or '..' in p.parts:raise ValueError('Frame path escapes archive')
            chosen.append(dict(index=i,path=str(p),sha256=f['sha256']))
        result[key]=dict(native=key,frames=chosen,anchor_indices=item['frame_indices'],
                         anchor_slots=list(range(32)),fps=item['fps'],
                         total_num_frames=item['total_num_frames'],
                         timestamps=[i/item['fps'] for i in item['frame_indices']])
    return result


def bind(items, settings):
    from e2e_reader import parity
    c=captures(items,settings['frames_root'])
    settings.update(frames_json={'captures':c},dense_manifest={'captures':c},require_dense64=False)
    mapped={r['id']:r for r in items};mapping=[]
    for item in items:
        parity.bind_item(item,settings,verify=False)
        mapping.append(dict(id=item['id'],key=parity.key(item),native=item['native'],
                            task_sha256=digest(item),layout_count=32,anchor_indices=item['frame_indices'],
                            dense_count=32,frame_binding_sha256=digest(c[item['native']])))
    if len({r['key'] for r in mapping})!=len(items):raise ValueError('Duplicate reserve reader keys')
    return mapped,dict(schema='h10-parity-mapping-v1',items=mapping,sha256=digest(mapping))
