"""Admit the fixed development-only room set and bind pinned RGBs to the reader."""
import json
from pathlib import Path
from .items import K,digest,sha

def validate(m):
    if not m.get('development_only') or m.get('fitting_permitted') is not False:
        raise ValueError('Room set is development-only and forbids fitting')
    rows=m['items'];sets=m['sets'];byid={r['id']:r for r in rows}
    if len(rows)!=134 or len(byid)!=134 or len(sets['dev-S1'])!=36 or len(sets['R0-dev'])!=98:
        raise ValueError('Room membership counts differ')
    if set(sets['dev-S1']) & set(sets['R0-dev']) or set(byid)!=set(sets['dev-S1'])|set(sets['R0-dev']):
        raise ValueError('Room membership keys differ')
    if any(r['question_type']!='room_size_estimation' or r['scorer']!='official_vsi_mra' for r in rows):
        raise ValueError('Room type or scorer differs')
    dev=set((K/'auth/R0_DEV_ROOMS.txt').read_text().splitlines())
    qpath=K/'inputs/r0dev/R0_QUESTIONS_dev_f32.jsonl'
    if sha(qpath)!=m['source']['sha256']:raise ValueError('Qset digest differs')
    qrows=[json.loads(line) for line in qpath.read_text().splitlines()]
    expected={q['qid']:q for q in qrows if q['question_type']=='room_size_estimation'}
    if set(sets['R0-dev'])!=set(expected):raise ValueError('R0 room keys differ')
    if m['r0_check']['found']!=98:raise ValueError('Reserve membership differs')
    for key in sets['R0-dev']:
        r=byid[key];q=expected[key];p=r['label_provenance']
        if (r['room_key'] not in dev or r.get('development_only') is not True or r['r0_split']!='R0-dev'
            or qrows[p['line']-1]!=q or p['source_qid']!=q['qid'] or p['source_sha256']!=m['source']['sha256']
            or r['question']!=q['question'] or r['ground_truth']!=q['gt']['area_m2']
            or r['source_frame_indices']!=q['frame_indices'] or r['total_num_frames']!=q['total_num_frames']):
            raise ValueError('R0 source binding differs')
    if {byid[k]['room_key'] for k in sets['dev-S1']} & {byid[k]['room_key'] for k in sets['R0-dev']}:
        raise ValueError('Physical room collision')

def bind(items,settings):
    from e2e_reader import parity
    from h1eval.h10.parity_adapter import map_items
    from parity_kit.common import FRAMES,DENSE
    manifest=json.loads((K/'items/room134.json').read_text())
    reserve=set(manifest['sets']['R0-dev'])
    dev=[r for r in items if r['id'] not in reserve]
    r0=[r for r in items if r['id'] in reserve]
    mapped,receipt=map_items(dev,settings,name='devs1_routed')
    c=dict(parity._captures(settings.get('frames_json',FRAMES)))
    d=dict(parity._captures(settings.get('dense_manifest',DENSE)))
    extra=json.loads((K/'inputs/room_captures.json').read_text())['captures']
    if set(c)&set(extra) or set(d)&set(extra):raise ValueError('Capture collision')
    c.update(extra);d.update(extra)
    settings.update(frames_json={'captures':c},dense_manifest={'captures':d},require_dense64=False)
    mapping=receipt['items'][:]
    for r in r0:
        task=dict(r,answer=r['ground_truth'])
        b=parity.bind_item(task,settings,verify=False)
        mapped[r['id']]=task
        mapping.append(dict(id=r['id'],key=parity.key(task),native=r['native'],task_sha256=digest(task),layout_count=32,
            anchor_indices=b['frames']['anchor_indices'],dense_count=32,frame_binding_sha256=digest(extra[r['native']])))
    mapping.sort(key=lambda r:r['id'])
    if len({r['key'] for r in mapping})!=len(items):raise ValueError('Duplicate reader key')
    return mapped,dict(schema='h10-parity-mapping-v1',items=mapping,sha256=digest(mapping))
