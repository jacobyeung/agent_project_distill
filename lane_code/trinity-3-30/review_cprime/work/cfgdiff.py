import json,hashlib,sys
def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def identity(cfg):
    v={k:x for k,x in cfg.items() if k not in ('preparation','admission','authorization','milestone_gate')}
    if 'readout' in v: v['readout']={k:x for k,x in v['readout'].items() if k!='contiguous_clips'}
    if v.get('frame_layout')=='spread': v.pop('frame_layout')
    return digest(v)
def walk(a,b,p=''):
    out=[]
    if isinstance(a,dict) and isinstance(b,dict):
        for k in sorted(set(a)|set(b)):
            if k not in a: out.append(('ADD',p+'/'+k,None,b[k]))
            elif k not in b: out.append(('DEL',p+'/'+k,a[k],None))
            else: out+=walk(a[k],b[k],p+'/'+k)
    elif isinstance(a,list) and isinstance(b,list) and len(a)<=len(b) and a==b[:len(a)]:
        for j,x in enumerate(b[len(a):]): out.append(('APPEND',p+f'[{len(a)+j}]',None,x))
    elif a!=b: out.append(('CHG',p,a,b))
    return out
A=json.load(open(sys.argv[1])); B=json.load(open(sys.argv[2]))
print('base identity',identity(A)); print('new identity',identity(B))
for d in walk(A,B): print(json.dumps(d))
