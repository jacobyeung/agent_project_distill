import sys, json, collections
import numpy as np
R='/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/work/n13/ret/native'
META='/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/work/meta/x/sj/orch_cd'
K5='/scratch/jjyeung/orch_n30/lever5/k5/kit'
d=json.load(open(R+'/R1.json'))
tasks={}
for p in (META+'/legs1_reads/work/vendor/r3/TASKS.jsonl', META+'/legs1_routed/out2/CAMERA_TASKS.jsonl'):
    for l in open(p):
        t=json.loads(l); tasks['devrows:'+t['id']]=t
U=d['arms']['unflagged']
print('tasks', len(tasks), 'missing', sum(x['key'] not in tasks for x in U))
scene_clips=collections.defaultdict(set); cam_scene=collections.Counter()
for x in U:
    t=tasks[x['key']]; scene_clips[t['scene']].add(x['perception']['clip'])
    if x['question_type'].startswith('camera'): cam_scene[t['scene']]+=1
print('scenes', len(scene_clips), 'multi-clip', [s for s,c in scene_clips.items() if len(c)>1][:5], 'cam scenes', len(cam_scene))
cfg=json.load(open(K5+'/1.json')); ref={c['k']:c for c in json.load(open(K5+'/REFERENCE_K5.json'))['captures']}
rows={r['k']:r for r in cfg['x3']}
k5scene={ref[k]['capture']:k for k in rows}
print('K5 captures', len(k5scene), 'cam scenes covered', sum(s in k5scene for s in cam_scene), 'all scenes covered', sum(s in k5scene for s in scene_clips))
print('cam scenes not in K5', [s for s in cam_scene if s not in k5scene])
eqc=eqK=eqs=anch=0; n=0
for s,k in k5scene.items():
    if s not in scene_clips: print('K5 scene not in banked', s); continue
    clip=list(scene_clips[s])[0]; z=np.load(R+'/geometry/'+clip+'.npz')
    a=list(z['anchor_frame_indices']); anch+= a==list(rows[k]['a'])
    dmp=ref[k].get('dump')
    if dmp:
        n+=1
        eqc+= np.array_equal(np.array(dmp['c2w_unscaled']), z['camera_to_world'])
        eqK+= np.array_equal(np.array(dmp['K']), z['K']); eqs+= float(dmp['scale'])==float(z['scale'])
        if n<4: print(s, np.abs(np.array(dmp['c2w_unscaled'])-z['camera_to_world']).max(), np.abs(np.array(dmp['K'])-z['K']).max(), dmp['scale'], float(z['scale']))
print('anchors equal', anch, '/', len(k5scene), '; vs dump (n=%d): c2w bit %d, K bit %d, scale bit %d'%(n,eqc,eqK,eqs))
print('room field sample', [tasks[x['key']]['room'] for x in U[:3]], [x['room'] for x in U[:3]])
print(collections.Counter(x['question_type'] for x in U))
