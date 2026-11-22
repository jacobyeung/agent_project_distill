# Writes lists/{arkit,scannet,scannetpp}.txt (absolute paths, tar -T) and lists/SUMMARY.json.
# Video datasets: the whole VSI mp4 per capture. ARKit: /data3 3dod lowres_wide PNGs at stride 2 over traj rows plus anchors
# (readdir one capture directory at a time, stat only the selected files).
import json, os, gzip, time
L='/scratch/jjyeung/orch_n30/lever7/gtcd/lists'
G=json.load(open('/scratch/jjyeung/orch_n30/lever6/gtc/out/FRAMES_GTC.json'))
P=json.load(gzip.open('/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/fb_pack/in/pk/frame_plan.json.gz'))
F=json.load(open('/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/b/work/meta/x/sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json'))
al={c['native']:c['plan_alias'] for c in F['captures']}
R='/data2/jjyeung/agent_project_data/vsi_distill_training_20260917'
ROOTS={'d1':[R+'/runtime_control/gt_teacher_r1313/poolext_wave2_scannet/media',R+'/media'],
       'd2':[R+'/runtime_control/gt_teacher_r1313/poolext_wave1_scannetpp/media',R+'/media']}
STRIDE={'d1':5,'d2':24,'d3':2}; FPS={'d1':24.0,'d2':60.0,'d3':10.0}
def dense(n,anchors,s):
    return sorted(set(range(anchors[0],anchors[-1]+1,s))|set(anchors))
out={'arkit':[],'scannet':[],'scannetpp':[]}; summ={'per_capture':[]}
for c in G['captures']:
    g=c['native'][:2]; a=c['anchor_indices']; e=(P['v'].get(al[c['native']]) or P['a'][al[c['native']]])
    d=dense(None,a,STRIDE[g]); rec=dict(capture=c['capture'],native=c['native'],stride=STRIDE[g],fps_src=FPS[g],dense_frames=len(d),anchors=len(a))
    if g in ('d1','d2'):
        p=next((os.path.join(r,e['n']) for r in ROOTS[g] if os.path.isfile(os.path.join(r,e['n']))),None)
        rec.update(source=p,files=1 if p else 0,bytes=os.stat(p).st_size if p else 0,raw_n=e['raw_n'])
        if p: out['scannet' if g=='d1' else 'scannetpp'].append(p)
    else:
        vid=c['native'][3:]; base=f'/data3/shared/datasets/arkitscenes/3dod/Training/{vid}/{vid}_frames/lowres_wide'
        names=sorted((float(n[:-4].rpartition('_')[2]),n) for n in os.listdir(base) if n.endswith('.png'))
        need={k:t for k,t,fl in e['need']}
        anchor_ts_ok=sum(abs(names[k][0]-need[k])<=0.002 for k in a)
        sel=[os.path.join(base,names[k][1]) for k in d]
        b=0
        for p in sel: b+=os.stat(p).st_size
        out['arkit']+=sel
        rec.update(source=base,png_in_dir=len(names),N=a[-1]+1,anchor_ts_within_2ms=anchor_ts_ok,files=len(sel),bytes=b,rot=e['rot'])
        time.sleep(1)
    summ['per_capture'].append(rec)
for k,v in out.items():
    open(f'{L}/{k}.txt','w').write(''.join(p+'\n' for p in v))
tot={}
for ds,g in (('arkit','d3'),('scannet','d1'),('scannetpp','d2')):
    rs=[r for r in summ['per_capture'] if r['native'].startswith(g)]
    tot[ds]=dict(captures=len(rs),files=sum(r['files'] for r in rs),bytes=sum(r['bytes'] for r in rs),dense_frames=sum(r['dense_frames'] for r in rs),
                 stride=STRIDE[g],fps_src=FPS[g],fps_dense=FPS[g]/STRIDE[g],missing=[r['capture'] for r in rs if not r['files']])
summ['totals']=tot; summ['total_bytes']=sum(t['bytes'] for t in tot.values())
json.dump(summ,open(f'{L}/SUMMARY.json','w'),indent=1)
print(json.dumps(tot,indent=1)); print('total_bytes',summ['total_bytes'])
for r in summ['per_capture']:
    if r['native'].startswith('d3'): print(r['capture'],r['png_in_dir'],r['N'],r['anchor_ts_within_2ms'],r['files'],r['bytes'],r['rot'])
