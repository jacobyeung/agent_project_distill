import json,sys
S=json.load(open('/scratch/jjyeung/orch_n30/k1_ops3/work/K1_MANIFEST.staged.json'))
F=json.load(open('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_finalize_v2/K1_MANIFEST.finalized.json'))
diffs=[]
def walk(a,b,p):
    if isinstance(a,dict) and isinstance(b,dict):
        for k in sorted(set(a)|set(b)):
            if k not in a: diffs.append((p+'/'+k,'ADDED',None)); continue
            if k not in b: diffs.append((p+'/'+k,'REMOVED',None)); continue
            walk(a[k],b[k],p+'/'+k)
    elif isinstance(a,list) and isinstance(b,list) and len(a)==len(b) and not (p.endswith('timestamps')):
        for i,(x,y) in enumerate(zip(a,b)): walk(x,y,p+'[%d]'%i)
    elif a!=b or type(a)!=type(b): diffs.append((p,'CHANGED',(str(a)[:60],str(b)[:60])))
walk(S,F,'')
import re,collections
norm=collections.Counter(re.sub(r'\[\d+\]','[*]',d[0])+' '+d[1] for d in diffs)
for k,v in sorted(norm.items()): print(v,k)
print('top-level keys S',sorted(S)); print('F',sorted(F))
print('unresolved',S.get('unresolved_dense_sources'),S.get('unresolved_gt_names'))
print('flags S',S.get('production_ready'),S.get('frame_staging_authorized'),'F',F.get('production_ready'),F.get('frame_staging_authorized'))
# timing changes per dataset
cnt=collections.Counter()
for c0,c1 in zip(S['captures'],F['captures']):
    assert c0['canonical']==c1['canonical']
    ds=c0['canonical'].split('/')[0]
    ch=tuple(k for k in ('fps','timestamps','total_num_frames') if c0['model_row']['student_input'].get(k)!=c1['model_row']['student_input'].get(k))
    nulls=tuple(c1['model_row']['student_input'].get(k) is None for k in ('fps','timestamps','total_num_frames'))
    cnt[(ds,ch,nulls,c1.get('timing_source'))]+=1
for k,v in cnt.items(): print(v,k)
print('staged timing sample',{k:S['captures'][0]['model_row']['student_input'].get(k) for k in ('fps','total_num_frames')})
print('k1a_frame_parity S==F',S.get('k1a_frame_parity')==F.get('k1a_frame_parity'))
