"""Round-three additions; previous package source members remain unchanged."""
from pathlib import Path
import hashlib
import json

SOURCES=('tree/student_pilot/scene_state.py','tree/student_pilot/geometry_profiles.py',
         'tree/student_pilot/routed_candidates.py','tree/student_pilot/routed_features.py',
         'tree/student_pilot/tower_read.py','tree/student_pilot/_tower_native.py',
         'tree/student_pilot/sam3_tower.py','tree/student_pilot/camera_targets.py',
         'tree/student_pilot/g3t_vendor/vggt/heads/dpt_head.py',
         'b/e2e_reader/geometry.py','b/e2e_reader/generate.py','b/e2e_reader/real.py',
         'b/e2e_reader/stage1.py','b/e2e_reader/grounding.py','b/e2e_reader/parity.py',
         'b/heads/selector/sl118/selector_inputs.py','tree/trace_format/box_v313.py')


def overlay(pf,source,once,jd):
    for path in sorted((source/'dense_runtime').glob('*.py')):pf['g/'+path.name]=path.read_bytes()
    pf['g/8.json']=jd({n:hashlib.sha256(pf[n]).hexdigest() for n in SOURCES})
    c=pf['g/c.py'].decode()
    c=once(c,'identity=g.identity)',"identity=g.identity, anchor_geometry_deltas=getattr(g,'anchor_geometry_deltas',None),\n                anchor_geometry_unchanged=getattr(g,'anchor_geometry_unchanged',True),\n                anchor_slots=getattr(g,'anchor_slots',list(range(32))))")
    c=once(c,"    for o in row['objects']:","""    ground=row.get('ground_source_indices',row['source_indices'])
    if len(ground) not in (32,64) or len(set(ground))!=len(ground):raise ValueError('ground frame map')
    if row.get('ground_frame_count',len(ground))!=len(ground):raise ValueError('ground frame count')
    slots=row.get('anchor_slots',list(range(32)))
    if [ground[s] for s in slots]!=row['source_indices']:raise ValueError('ground anchors')
    if row.get('geometry') and row['geometry']['source_indices']!=ground:raise ValueError('geometry binding')
    for o in row['objects']:""")
    c=once(c,"not 1 <= p['frame'] <= 32 or p['source_index'] != row['source_indices'][p['frame']-1]",
           "not 1 <= p['frame'] <= len(ground) or p['source_index'] != ground[p['frame']-1]")
    pf['g/c.py']=c.encode()


def operator(raw,once):
    text=raw.decode()
    text=once(text,'g3t = (64*9+64+32+32*51*51*5+51+2)*8',
              'g3t = (64*9+64+32+96*51*51*5+51+2)*8')
    text=once(text,"    cfg = prepare(config)[0]; root = control(cfg)",
              "    cfg = prepare(config)[0]; root = control(cfg)\n    from g.d import installed, rehearsal\n    with installed(): rehearsal()")
    return text.encode()


def rebuild_legacy(destination,root):
    """Repack the frozen round-one members, authenticating the historical input."""
    from gpkg.build import read_tar,write_tar,sha,jd
    raw=(root/'out/delivery.tgz').read_bytes()
    expected='f4509a4ad19b8e2bd2f9f5fd3fe7c32130ab13c10db5aa00407a84582fdb8d00'
    if sha(raw)!=expected:raise ValueError('frozen round-one delivery differs')
    rebuilt=write_tar(read_tar(raw))
    if sha(rebuilt)!=expected:raise ValueError('round-one rebuild differs')
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    (destination/'delivery.tgz').write_bytes(rebuilt)
    report=dict(token='a5d6f41359166',delivery_sha256=sha(rebuilt),
                method='deterministic rebuild from authenticated frozen member inventory')
    (destination/'BUILD.json').write_bytes(jd(report))
    return report
