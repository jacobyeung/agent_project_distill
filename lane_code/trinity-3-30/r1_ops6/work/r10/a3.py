import json,sys,os,re,torch,time
NL='/tmp/jjyeung/a_6ed2c7aa'; R=NL+'/runs/6ed2c7aa'
AS='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung'; LU='/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung'
def m(p):
    for a in (AS,LU):
        if p.startswith(a+'/ap/8865619b/runs'): return p.replace(a+'/ap/8865619b/runs',NL+'/runs')
        if p.startswith(a+'/ap/8865619b/'): return p.replace(a+'/ap/8865619b',NL+'/x_172660')
        if p.startswith(a): return p.replace(a,NL+'/root/aws/u')
    return p
def paths(o,acc,pre=''):
    if isinstance(o,dict):
        for k,v in o.items(): paths(v,acc,pre+'.'+k)
    elif isinstance(o,list):
        for i,v in enumerate(o): paths(v,acc,pre+'.'+str(i))
    elif isinstance(o,str) and o.startswith('/'): acc.append((pre,o))
arts={'400':R+'/m400/artifact.json','544':NL+'/root/aws/u/ap/93ccadab/m544/artifact.json'}
heads={}
for s,a in arts.items():
    A=json.load(open(a)); acc=[]; paths(A,acc)
    print(s,'keys',list(A)[:20])
    for k,p in acc:
        if 'heads' in p or 'heads' in k: print(' ',s,k,p,'->',m(p),os.path.exists(m(p)))
    hp=[m(p) for k,p in acc if p.endswith('heads.pt')]
    heads[s]=hp[0] if hp else None
print('heads',heads)
PAT=re.compile(r'(scale|depth|pose\.head\.|pose\.tokens|pose\.projector|frame_queries|fov)')
sd={}
for s,h in heads.items():
    if h and os.path.exists(h):
        t=time.time(); o=torch.load(h,map_location='cpu',mmap=True,weights_only=False)
        if isinstance(o,dict) and 'state_dict' in o: o=o['state_dict']
        sd[s]=o; print(s,'loaded',type(o),len(o) if hasattr(o,'__len__') else '',round(time.time()-t,1),'s')
        ks=list(o.keys()) if isinstance(o,dict) else []
        print(' sample',[k for k in ks if PAT.search(k)][:40], len(ks))
if len(sd)==2:
    a,b=sd['544'],sd['400']
    groups={}
    for k in a:
        if k in b and torch.is_tensor(a[k]) and PAT.search(k):
            g=k.split('.')[:4]; g='.'.join(g)
            d=(b[k].float()-a[k].float()); n0=a[k].float().norm().item(); 
            e=groups.setdefault(g,[0.,0.,0,0]); e[0]+=d.norm().item()**2; e[1]+=n0**2; e[2]+=1; e[3]+=int(torch.equal(a[k],b[k]))
    for g,(dd,nn,c,eq) in sorted(groups.items()): print('G',g,'tensors',c,'identical',eq,'rel_change',round((dd**.5)/max(nn**.5,1e-12),5))
    for k in [k for k in a if 'scale_token' in k or 'scale_branch' in k][:6]+[k for k in a if 'point_depth' in k][:3]:
        if k in b: print('T',k,tuple(a[k].shape),'544 norm',round(a[k].float().norm().item(),5),'400 norm',round(b[k].float().norm().item(),5),'diff',round((b[k].float()-a[k].float()).norm().item(),6))
