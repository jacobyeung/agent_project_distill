import torch,tarfile,glob,time,io,re,json
NL='/tmp/jjyeung/a_6ed2c7aa'; R=NL+'/runs/6ed2c7aa'
def norm(sd):
    if isinstance(sd,dict):
        for k in ('state_dict','model','heads','replicated','tensors'):
            if k in sd and isinstance(sd[k],dict) and len(sd[k])>50: return norm(sd[k])
    out={}
    for k,v in sd.items():
        if not torch.is_tensor(v): continue
        k2=k.replace('_fsdp_wrapped_module.','').replace('module.','')
        for pre in ('auxiliary_heads.pose.','auxiliary_heads.depth.'):
            i=k2.find(pre)
            if i>=0: k2=k2[i+len('auxiliary_heads.'):]; break
        out[k2]=v
    return out
t=time.time()
S={}
import os
cand=sorted(glob.glob('/project/community/jjyeung/okh7/x_07ca49df/runs/469ddece/*/heads.pt')+glob.glob('/project/community/jjyeung/okh7/x_07ca49df/runs/469ddece/*heads*')+glob.glob('/project/community/jjyeung/okh7/*/runs/469ddece/m544/heads.pt'))
print('544 cand',cand,glob.glob('/project/community/jjyeung/okh7/x_07ca49df/runs/469ddece/*')[:30],flush=True)
if cand:
    S['544']=norm(torch.load(cand[0],map_location='cpu',mmap=True,weights_only=False)); print('544',len(S['544']),round(time.time()-t),flush=True)
with tarfile.open('/project/community/jjyeung/okh7/r/673bc60f/A.tar') as tf:
    for m in tf:
        if m.name.endswith('/replicated.pt'):
            raw=torch.load(io.BytesIO(tf.extractfile(m).read()),map_location='cpu',weights_only=False); break
tt=raw.get('tensors'); print('200 raw',type(tt),(len(tt) if hasattr(tt,'__len__') else ''),(list(tt)[:5] if isinstance(tt,dict) else (type(tt[0]),tt[0] if not torch.is_tensor(tt[0]) else tt[0].shape) if isinstance(tt,list) else ''),flush=True)
S['200']=norm(raw); print('200',len(S['200']),round(time.time()-t),flush=True)
S['400']=norm(torch.load(R+'/m400/heads.pt',map_location='cpu',mmap=True,weights_only=False))
ck=sorted(glob.glob(R+'/checkpoint_000524_*/replicated.pt'))
if ck:
    S['524']=norm(torch.load(ck[0],map_location='cpu',mmap=True,weights_only=False)); print('524',len(S['524']),flush=True)
for s,d in S.items(): print('keys',s,len(d),[k for k in d if 'scale' in k][:5],[k for k in d][:3])
def grp(k):
    p=k.split('.')
    if p[0]=='depth': return '.'.join(p[:3]) if p[1]!='auxiliary_heads' else '.'.join(p[:4])
    return '.'.join(p[:3])
pairs=[p for p in [('544','200'),('200','400'),('544','400'),('400','524')] if p[0] in S and p[1] in S]
res={}
for a,b in pairs:
    A,B=S[a],S[b]; g={}
    common=[k for k in A if k in B and A[k].shape==B[k].shape]
    for k in common:
        x=A[k].float(); y=B[k].float(); e=g.setdefault(grp(k),[0.,0.,0,0])
        e[0]+=(y-x).norm().item()**2; e[1]+=x.norm().item()**2; e[2]+=1; e[3]+=int(torch.equal(A[k],B[k]))
    print('PAIR',a,b,'common',len(common),'onlyA',len(set(A)-set(B)),'onlyB',len(set(B)-set(A)))
    for k,(dd,nn,c,eq) in sorted(g.items()):
        r=(dd**.5)/max(nn**.5,1e-12); res.setdefault(k,{})[a+'->'+b]=dict(rel=r,n=c,identical=eq)
        print(' G %-40s n=%3d identical=%3d rel_change=%.5f'%(k,c,eq,r))
for k in ['pose.head.scale_token','pose.head.scale_branch.fc2.weight','pose.head.scale_branch.fc2.bias','depth.fov.weight','depth.auxiliary_heads.frame_queries']:
    print('T',k,{s:(round(d[k].float().norm().item(),6) if k in d else None) for s,d in S.items()}, {s:([round(float(v),6) for v in d[k].float().reshape(-1)[:3]] if k in d else None) for s,d in S.items()})
json.dump(res,open('/tmp/jjyeung/r10_a5.json','w'))
print(json.dumps(res))
