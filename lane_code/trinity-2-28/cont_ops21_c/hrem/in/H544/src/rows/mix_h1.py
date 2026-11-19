"""Render D0 plus H1 switches; config paths are data and are never followed."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
K=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(K/'tree'))
from student_pilot.carrier_c1_sweep import recipe_for
from student_pilot.h1 import CAMERA_TYPES, validate
BASE=K/'auth/d0_base.json'
OVER=K/'auth/d0_override.txt'
NEEDS_64=[
 'carrier_c1_data frame ingestion, layouts, frame ids and position maps must accept 64 frames',
 'CarrierC1 camera_settings max_groups and pose carrier/target masks must grow from 32 to 64',
 'PrivateDepth frame_queries and group_embed must grow from 32 to 64 with an explicit initialization policy',
 'OwnGeometry, HeadState, query_tensor and camera GT target shapes must accept [64,9]',
 'camera_rows frame grammar and generation, decode parse_head and v3.14 grounding sessions must accept slots 1..64',
 'reader geometry profiles, stage-1 masks and selector features must use 64 anchors',
 'new checkpoint compatibility, exact RGB/GT bindings, native position and cache parity tests are required']


def merge(a,b):
    out=copy.deepcopy(a)
    for k,v in b.items(): out[k]=merge(out[k],v) if isinstance(v,dict) and isinstance(out.get(k),dict) else copy.deepcopy(v)
    return out


def d0():
    text=OVER.read_text();start=text.index('"config":',text.index('=== over_b'))+len('"config":')
    overrides,_=json.JSONDecoder().raw_decode(text[start:].lstrip())
    return merge(json.loads(BASE.read_text()),overrides)


def build(frames=32):
    if frames!=32: raise ValueError('64 frames refused:\n- '+'\n- '.join(NEEDS_64))
    base=d0();outputs={}
    for name,s2 in [('h1_1',True),('h1_1a',False)]:
        c=copy.deepcopy(base)
        c['h1']=dict(faithful_own_camera_rows=True,routing_pose_targets=s2,camera_types=list(CAMERA_TYPES),
                     stop_after_step=200,metrics=True,
                     r0_rooms=dict(path='auth/R0_ROOMS.txt',
                         sha256='bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3'))
        c['scheduled_sampling'].update(max_own_probability=.5,force_from_step=1)
        c['milestones']=[100,200];c['recipe']=recipe_for(c);validate(c)
        assert c['steps']==c['recipe']['steps']==1000
        outputs[name]=c
    return base,outputs


def differences(a,b,prefix=''):
    changes=[]
    for k in sorted(set(a)|set(b)):
        path=prefix+'.'+k if prefix else k
        if isinstance(a.get(k),dict) and isinstance(b.get(k),dict): changes+=differences(a[k],b[k],path)
        elif a.get(k)!=b.get(k): changes.append(dict(field=path,d0=a.get(k),h1=b.get(k)))
    return changes

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--frames',type=int,choices=[32,64],default=32);a=p.parse_args()
    try: base,outputs=build(a.frames)
    except ValueError as e: p.exit(2,str(e)+'\n')
    (K/'configs/d0.json').write_text(json.dumps(base,indent=2)+'\n')
    for name,c in outputs.items(): (K/'configs'/f'{name}.json').write_text(json.dumps(c,indent=2)+'\n')
    report=dict(frames=32,inputs=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in (BASE,OVER)],
                configs={name:differences(base,c) for name,c in outputs.items()})
    (K/'configs/diff_against_d0.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({name:[d['field'] for d in differences(base,c)] for name,c in outputs.items()},indent=2))
