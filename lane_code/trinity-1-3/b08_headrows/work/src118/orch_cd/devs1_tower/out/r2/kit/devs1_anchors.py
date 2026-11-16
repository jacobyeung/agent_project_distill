"""Build pinned E0 manifests with authoritative, ordered registry anchors."""
import argparse
import hashlib
import io
import json
import re
from pathlib import Path
import numpy as np
from PIL import Image

DATASETS={'d1':'scannet','d2':'scannetppv2','d3':'arkitscenes'}

def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    blob=json.dumps(value,sort_keys=True,indent=2)+'\n'
    if path.exists() and path.read_text()==blob:return
    tmp=path.with_suffix(path.suffix+'.part');tmp.write_text(blob);tmp.replace(path)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def uniform(n,k):
    if n<k or k<2:raise ValueError('Insufficient frames')
    return [j*(n-1)//(k-1) for j in range(k)]

def select_dense(pins,anchors):
    """Keep anchors; interleave temporal midpoints, then maximize the remaining spacing."""
    ids=[p['index'] for p in pins]
    if len(anchors)!=32 or anchors!=sorted(set(anchors)):
        raise ValueError('Require 32 unique ordered registry anchors')
    if ids!=sorted(set(ids)) or not set(anchors)<=set(ids):
        raise ValueError('Registry anchors missing from available frames')
    if len(pins)==32:return list(pins),list(range(32))
    if len(pins)<64:raise ValueError('Insufficient dense frames')
    selected=set(anchors)
    for left,right in zip(anchors,anchors[1:]):
        between=[i for i in ids if left<i<right]
        if not between:raise ValueError('Cannot interleave registry anchors')
        selected.add(min(between,key=lambda i:(abs(2*i-left-right),i)))
    # There are 31 anchor intervals. The last extra frame splits the largest
    # remaining gap; ties choose the earliest frame. No anchor is inferred.
    remaining=[i for i in ids if i not in selected]
    selected.add(min(remaining,key=lambda i:(-min(abs(i-j) for j in selected),i)))
    dense=[p for p in pins if p['index'] in selected]
    slots=[sorted(selected).index(i) for i in anchors]
    assert len(dense)==64 and [dense[i]['index'] for i in slots]==anchors
    return dense,slots

def validate_capture(capture):
    dense=capture['dense'];slots=capture['anchor_slots'];anchors=capture['anchor_indices']
    ids=[p['index'] for p in dense]
    if len(anchors)!=32 or anchors!=sorted(set(anchors)):
        raise ValueError('Invalid registry anchors')
    if len(ids) not in (32,64) or ids!=sorted(set(ids)):
        raise ValueError('Invalid dense frames')
    if not set(anchors)<=set(ids):raise ValueError('Anchor containment failed')
    if len(slots)!=32 or any(type(i)!=int or i<0 or i>=len(ids) for i in slots):
        raise ValueError('Invalid anchor slots')
    if [ids[i] for i in slots]!=anchors:raise ValueError('Registry anchor identity differs')
    if capture['group']!='g3s'+str(len(ids)):raise ValueError('Dense group differs')
    if len(ids)==32 and ids!=anchors:raise ValueError('g3s32 must equal anchors')
    if len(ids)==64 and any(b-a<2 for a,b in zip(slots,slots[1:])):
        raise ValueError('Anchors are not interleaved')

def path_for(root,pin):
    root=Path(root).resolve();path=(root/pin['path']).resolve()
    if not path.is_relative_to(root):raise ValueError('Frame escapes root')
    return path

def verify_frames(plan,root):
    for capture in plan['captures']:validate_capture(capture)
    total=0
    for pin in plan['files']:
        path=path_for(root,pin)
        if not path.is_file():raise ValueError('Missing frame: '+str(path))
        if sha(path)!=pin['sha256']:raise ValueError('Frame sha256 mismatch: '+str(path))
        total+=path.stat().st_size
    return total

def pixels(arr):
    f=io.BytesIO();np.save(f,arr,allow_pickle=False);return hashlib.sha256(f.getvalue()).hexdigest()

def build(plan,root,out):
    root=Path(root).resolve();out=Path(out)
    for capture in plan['captures']:
        validate_capture(capture)
        scene=capture['scene'];group=capture['group'];dense=capture['dense'];slots=capture['anchor_slots']
        arrays=[]
        for pin in dense:
            path=path_for(root,pin);raw=path.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=pin['sha256']:raise ValueError('Frame sha256 mismatch')
            with Image.open(io.BytesIO(raw)) as im:
                if im.format!='PNG' or im.mode!='RGB':raise ValueError('Require RGB PNG')
                if list(im.size)!=[capture['hw'][1],capture['hw'][0]]:raise ValueError('Frame dimensions differ')
                arrays.append(np.array(im))
        anchors=[dense[i] for i in slots];arr=np.stack([arrays[i] for i in slots])
        row=dict(scene=scene,video_rel=scene+'.mp4',fps=capture.get('fps',1),total_num_frames=capture['total_num_frames'],
                 frame_indices=[p['index'] for p in anchors],frames=anchors,anchor_pixel_sha256=pixels(arr),duplicate_pixel_sha256=pixels(np.repeat(arr,2,axis=0)))
        member=dict(id=hashlib.sha256((scene+'|floor').encode()).hexdigest()[:16],scene=scene,obj='floor',frame=1,kind='point',
                    **{k:row[k] for k in ['video_rel','fps','total_num_frames','frame_indices']})
        dest=out/group/scene.replace('/','__')
        save(dest/'A_MANIFEST.json',dict(selections=[row]));save(dest/'MEMBERSHIP.json',dict(items=[member]))
        save(dest/'DENSE.json',dict(dense=len(dense),render_root=str(root),clips={scene:dict(frame_indices=[p['index'] for p in dense],anchor_slots=slots,frames=dense,hw=capture['hw'])},refused={}))
    return len(plan['captures'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',default=str(Path(__file__).with_name('PLAN.json')));p.add_argument('--frame-root',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();plan=json.loads(Path(a.plan).read_text());print(json.dumps(dict(bytes=verify_frames(plan,a.frame_root),captures=build(plan,a.frame_root,a.out))))
