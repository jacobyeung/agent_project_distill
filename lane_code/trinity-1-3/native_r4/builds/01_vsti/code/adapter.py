"""Prepare opaque prompt records and verified local frame assets."""
import hashlib
import json
import re
from pathlib import Path

CAMERA = ('camera_displacement', 'camera_movement_direction')
COUNTS = dict(camera_displacement=2, camera_movement_direction=2, camera_obj_abs_dist=1,
              camera_obj_rel_dist_v1=1, camera_obj_rel_dist_v2=1, camera_obj_rel_dist_v3=1,
              obj_obj_relative_pos_lr=1, obj_obj_relative_pos_nf=1)

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def load(p):
    return json.loads(Path(p).read_text())

def dump(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    pending=p.with_name(p.name+'.next')
    pending.write_text(json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n')
    pending.replace(p)

def rows(p):
    return [json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]

def pin(p):
    return dict(path=str(Path(p).resolve()),sha256=sha(p))

def checked(p):
    if sha(p['path']) != p['sha256']:
        raise ValueError('pin mismatch')
    return Path(p['path'])

def frame_pair(question):
    match=re.search(r'\bframe\s+(\d+)(?:\s+of\s+32)?\s+(?:and|to)\s+(?:frame\s+)?(\d+)\s+of\s+32\b',question,re.I)
    if match is None:
        raise ValueError('camera question lacks a frame pair')
    pair=tuple(map(int,match.groups()))
    if any(not 1 <= k <= 32 for k in pair) or pair[0]==pair[1]:
        raise ValueError('invalid camera frame pair')
    return pair

def order(items):
    ordered=sorted(items,key=lambda x:int(x['id'].removeprefix('q')))
    canary=[]
    for typ,n in COUNTS.items():
        group=[t['id'] for t in ordered if t['question_type']==typ]
        if len(group)<n:
            raise ValueError('canary lacks required type: '+typ)
        canary.extend(group[:n])
    rest=[t for t in ordered if t['id'] not in canary]
    rest.sort(key=lambda t:(t['question_type'] not in CAMERA,int(t['id'][1:])))
    return canary,[t['id'] for t in rest]

def shard_keys(bound,shard,canary_only=False):
    k,n=map(int,shard.split('/'))
    if n<1 or not 0<=k<n:
        raise ValueError('invalid shard')
    if canary_only:
        if k!=0:raise ValueError('canary belongs to shard zero')
        return list(bound['canary'])
    return (list(bound['canary']) if k==0 else [])+bound['post_canary'][k::n]

def prepare(items_path,media_path,frames_root,dest,sample=False):
    items=load(items_path);media=load(media_path);dest=Path(dest);root=Path(frames_root)
    if dest.exists():raise ValueError('adapter destination exists')
    if len(items)!=450 or len({str(x['id']) for x in items})!=450:
        raise ValueError('item membership differs')
    from collections import Counter
    if sorted(Counter(x['question_type'] for x in items).values())!=[50]*9:
        raise ValueError('type membership differs')
    prompts=[];scores={};captures=[];dense={};missing=[]
    for scene in sorted({x['scene_name'] for x in items}):
        receipt=media['scannet:'+scene]['frame_receipt'];cache=Path(receipt['path']).parent.name
        selection=root/cache/'selection.json'
        if not selection.is_file():
            missing.append(scene)
            continue
        if sha(selection)!=receipt['sha256']:raise ValueError('selection pin differs: '+cache)
        sel=load(selection);indices=sel['frame_indices']
        if (sel['schema']!='rgb32-selection-v1' or sel['cache_id']!=cache or len(sel['frames'])!=32
            or indices!=[k*(sel['total_num_frames']-1)//31 for k in range(32)] or sel['fps']!=24):
            raise ValueError('selection contract differs')
        native='c'+digest(scene)[:24];ff=[];dd=[]
        for f in sel['frames']:
            h=f['png']['sha256'];source=root/cache/Path(f['png']['path']).name
            if source.stat().st_size!=f['png']['size_bytes'] or sha(source)!=h:
                raise ValueError('frame pin differs: '+h)
            rel=h[:2]+'/'+h+'.png';target=dest/'store'/rel;target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():target.write_bytes(source.read_bytes())
            ff.append(dict(path=rel,sha256=h));dd.append(dict(path=str(target.resolve()),sha256=h,index=f['index']))
        c=dict(native=native,group='rgb32',anchor_indices=indices,frames=ff,fps=sel['fps'],
               total_num_frames=sel['total_num_frames'],timestamps=[i/sel['fps'] for i in indices])
        captures.append(c);dense[native]=dict(frames=dd,anchor_slots=list(range(32)))
        for item in items:
            if item['scene_name']!=scene:continue
            key='q'+str(item['id']);task=dict(id=key,native=native,dataset='d0',scene=native,
                    room='r'+digest(scene.split('_')[0])[:24],question_type=item['question_type'],
                    question=item['question'],options=item['options'],stratum='s0')
            if task['question_type'] in CAMERA:task['pair']=list(frame_pair(task['question']))
            prompts.append(task)
            scores[key]=dict(id=str(item['id']),scene=scene,room=scene.split('_')[0],
                            question_type=item['question_type'],ground_truth=item['ground_truth'],options=item['options'])
    if missing and not sample:raise ValueError('missing local captures: '+str(len(missing)))
    full_prompts=[dict(id='q'+str(i['id']),question_type=i['question_type']) for i in items]
    canary,post=order(full_prompts)
    if sample:
        present={p['id'] for p in prompts}
        # Rehearsal exercises a local canary; it cannot certify the global canary.
        local_order=[k for k in canary+post if k in present]
        canary=local_order[:min(10,len(local_order))];post=local_order[len(canary):]
    dest.mkdir(parents=True,exist_ok=True)
    (dest/'TASKS.jsonl').write_text(''.join(json.dumps(t,sort_keys=True)+'\n' for t in prompts))
    dump(dest/'FRAMES.json',dict(captures=captures))
    dump(dest/'DENSE.json',dict(schema='legs1-dense-frames-v1',captures=dense))
    dump(dest/'SCORES.json',scores)
    bound=dict(schema='read-list-v1',synthetic=sample,canary=canary,post_canary=post,
               keys=canary+post,source_sha256=sha(items_path),media_sha256=sha(media_path),
               inputs={n:pin(dest/n) for n in ('TASKS.jsonl','FRAMES.json','DENSE.json','SCORES.json')},
               frames_root=str((dest/'store').resolve()),missing_scenes=missing)
    bound['binding']=digest(bound);dump(dest/'BOUND.json',bound)
    return bound

def validate_bound(path):
    b=load(path)
    if digest({k:v for k,v in b.items() if k!='binding'})!=b['binding']:raise ValueError('list binding differs')
    for p in b['inputs'].values():checked(p)
    if len(set(b['keys']))!=len(b['keys']) or b['keys']!=b['canary']+b['post_canary']:
        raise ValueError('list contains duplicates or wrong order')
    tasks=rows(checked(b['inputs']['TASKS.jsonl']))
    if {t['id'] for t in tasks}!=set(b['keys']):raise ValueError('prompt membership differs')
    if not b['synthetic']:
        canary,post=order(tasks)
        if (b['canary'],b['post_canary'])!=(canary,post) or len(tasks)!=450:
            raise ValueError('production canary/order differs')
    return b


def relocate_input(dest,logical):
    """Seal host-prepared files for a fixed read-only namespace mount."""
    dest=Path(dest);logical=Path(logical)
    if not logical.is_absolute():raise ValueError('logical root must be absolute')
    dense=load(dest/'DENSE.json')
    for entry in dense['captures'].values():
        for frame in entry['frames']:
            frame['path']=str(logical/'store'/frame['sha256'][:2]/(frame['sha256']+'.png'))
    dump(dest/'DENSE.json',dense)
    bound=load(dest/'BOUND.json')
    for name in bound['inputs']:
        bound['inputs'][name]=dict(path=str(logical/name),sha256=sha(dest/name))
    bound['frames_root']=str(logical/'store')
    bound['binding']=digest({k:v for k,v in bound.items() if k!='binding'})
    dump(dest/'BOUND.json',bound);return bound
