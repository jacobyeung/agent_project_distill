"""Pinned normalized points, exact name binding, and anchor RGB admission."""
import hashlib
import json
from pathlib import Path
import re
from .q import validate as validate_map


def load(path,expected,refs):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('points SHA256 differs')
    value=json.loads(raw)
    required={'model','route','frames','prompt_template_sha256','prompt_sha256_by_scene','frame_sha256_by_scene','format','points'}
    if not required<=set(value):raise ValueError('points envelope is incomplete')
    validate_map(value['points'])
    if set(value['points'])!={r['item_id'] for r in refs}:raise ValueError('points item membership differs')
    for ref in refs:
        for name,frames in value['points'][ref['item_id']].items():
            if set(frames)!={str(i) for i in ref['source_indices']}:raise ValueError('points anchors differ')
    return value


def resolve(name,names,name_key):
    if name in names:return name,'exact'
    matches=[n for n in names if name_key(n)==name_key(name)]
    return (matches[0],'normalized') if len(matches)==1 else (None,'ambiguous' if matches else 'unmapped')


def binding(value,ref,anchor_hashes,name_key):
    expected=value['frame_sha256_by_scene'].get(ref['capture'])
    matched=isinstance(expected,list) and len(expected)==32 and expected==anchor_hashes
    calls=[]
    for i,c in enumerate(ref['calls']):
        m=re.fullmatch(r'<ground obj="([^"]+)" mode="box">',c['call'])
        if not m:continue
        name,rule=resolve(m[1],value['points'][ref['item_id']],name_key)
        calls.append(dict(call_index=i,call=c['call'],recorded_name=m[1],points_name=name,rule=rule,served=c['served']))
    return dict(item_id=ref['item_id'],capture=ref['capture'],frame_hashes_match=matched,
                expected_anchor_sha256=expected,bound_anchor_sha256=anchor_hashes,
                excluded=not matched,calls=calls,unmapped_calls=[c for c in calls if c['points_name'] is None])
