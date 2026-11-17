import sqlite3, json, collections, re, hashlib, os, glob, numpy as np
ROOT='/scratch/jjyeung/orch_n30/rows_a2/work/inputs/assets/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313'
dirs={}
IN='/scratch/jjyeung/orch_n30/rows_a2/work/inputs/assets'
meta=json.load(open('/scratch/jjyeung/orch_n30/rows_a2/work/META_PINCHECK.json'))
for k,r in meta.items():
    if r['status']!='ok': continue
    c=[x for x in r['cands'] if x['fi_match']][0]
    ds,sid=k.split('/'); pre='scannet' if ds=='scannet' else 'scannetppv2'
    dirs[pre+'__'+sid]=IN+os.path.dirname(c['assets']['instances']['path'])
print('asset scenes with instances.json',len(dirs), collections.Counter(k.split('__')[0] for k in dirs))
amap=json.load(open('/scratch/jjyeung/orch_n30/rows_a2/work/alias_map.json'))
c=sqlite3.connect('file:/scratch/jjyeung/orch_n30/rows_a2/out/a2_vqa_v6/vqa/rows.sqlite?immutable=1',uri=True)
rows=[]
for (row,) in c.execute("select row from rows"):
    d=json.loads(row)
    if d['question_type']!='object_size_estimation': continue
    alias=d['dataset']+'/'+d['scene']; can=amap.get(alias)
    key=can.replace('scannetpp/','scannetppv2__').replace('/','__') if can else None
    m=re.search(r'Step 1: find the (.+?)(?:, first seen in frame \d+)?\.\n',d['target'])
    rows.append(dict(qid=d['qid'],alias=alias,key=key,label=m.group(1) if m else None,answer=float(d['answer']),q=d['student_input']['question'],retraced=bool(d.get('retrace_a2'))))
print('size rows',len(rows),'with canonical',sum(1 for r in rows if r['key']),'with assets',sum(1 for r in rows if r['key'] in dirs))
def norm(s): return re.sub(r'\s+',' ',s.strip().lower())
cache={}
def scene(key):
    if key not in cache:
        m=json.load(open(dirs[key]+'/instances.json'))
        cache[key]=m
    return cache[key]
elig=[]
for r in rows:
    if r['key'] not in dirs or not r['label']: continue
    m=scene(r['key']); ids=[g for g in m['segGroups'] if norm(g['label'])==norm(r['label'])]
    if len(ids)!=1: continue
    r['g']=ids[0]; elig.append(r)
print('eligible (unique label, assets present)',len(elig))
elig.sort(key=lambda r: hashlib.sha256(('size_diag30|'+r['qid']).encode()).hexdigest())
pick=elig[:30]
out=[]
for r in pick:
    g=r['g']; ob=g['obb']; L=np.array(ob['axesLengths'],float); A=np.array(ob['normalizedAxes'],float).reshape(3,3); c=np.array(ob['centroid'],float)
    aabb=np.array(ob['max'])-np.array(ob['min'])
    sig_half=2*np.abs(A.T)@L      # world AABB width if L are half extents (axes as rows)
    sig_full=np.abs(A.T)@L        # world AABB width if L are full extents
    z=np.load(dirs[r['key']]+'/instance_mesh.npz')
    if 'face_instance_ids' in z.files:
        fidx=np.nonzero(z['face_instance_ids']==g['id'])[0]
    else:
        ids=list(z['membership_instance_ids']); i=ids.index(g['id']); off=z['membership_face_offsets']
        fidx=z['membership_face_indices'][off[i]:off[i+1]]
    vidx=np.unique(z['faces'][fidx].reshape(-1)); V=z['vertices_world'][vidx].astype(float)
    proj=(V-c)@A.T; ext=proj.max(0)-proj.min(0); halfmax=np.abs(proj).max(0)
    out.append(dict(qid=r['qid'],scene=r['key'],label=r['label'],q=r['q'],answer_cm=r['answer'],half_max_cm=100*L.max(),two_half_cm=200*L.max(),mesh_ext_cm=100*ext.max(),
        ratio_ans_half=r['answer']/(100*L.max()),ratio_ans_mesh=r['answer']/(100*ext.max()),
        sig_half_err=float(np.abs(aabb-sig_half).max()),sig_full_err=float(np.abs(aabb-sig_full).max()),mesh_halfmax_over_L=[round(float(x),3) for x in halfmax/L],nverts=len(V),retraced=r['retraced']))
json.dump(out,open('Q1_30ROWS.json','w'),indent=1)
print('%-26s %-30s %-16s %7s %7s %7s %6s %6s %8s %8s'%('qid','scene','label','ans','2L','mesh','a/L','a/mesh','sigHalf','sigFull'))
for o in out:
    print('%-26s %-30s %-16s %7.1f %7.1f %7.1f %6.2f %6.2f %8.4f %8.4f %s'%(o['qid'],o['scene'][:30],o['label'][:16],o['answer_cm'],o['two_half_cm'],o['mesh_ext_cm'],o['ratio_ans_half'],o['ratio_ans_mesh'],o['sig_half_err'],o['sig_full_err'],o['mesh_halfmax_over_L']))
import statistics as st
print('median answer/(100 max L) %.3f; median answer/mesh extent %.3f; half-extent signature max err %.4f m; full-extent signature min err %.3f m'%(st.median(o['ratio_ans_half'] for o in out),st.median(o['ratio_ans_mesh'] for o in out),max(o['sig_half_err'] for o in out),min(o['sig_full_err'] for o in out)))
print('rounding: answer == round(200*maxL) on', sum(1 for o in out if abs(o['answer_cm']-round(o['two_half_cm']))<=0.5+1e-9),'of',len(out))
