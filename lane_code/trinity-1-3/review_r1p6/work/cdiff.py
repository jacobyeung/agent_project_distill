import json,sys
def flat(o,p=''):
    if isinstance(o,dict):
        r={}
        for k,v in o.items(): r.update(flat(v,f'{p}.{k}' if p else k))
        return r
    return {p:o}
for new,old in (('snap_fac07052','snap_8246a4dd'),('snap_0647a0df','snap_2c67f1f2')):
    a=json.load(open(f'{old}/out/config.json')); b=json.load(open(f'{new}/out/config.json'))
    fa,fb=flat(a),flat(b)
    print('==',new,'vs',old)
    for k in sorted(set(fa)|set(fb)):
        if fa.get(k,'<absent>')!=fb.get(k,'<absent>'):
            va,vb=fa.get(k,'<absent>'),fb.get(k,'<absent>')
            if k=='remove_files': print(k, 'old n',len(va),'new n',len(vb),'prefix equal',vb[:len(va)]==va,'appended',vb[len(va):])
            else: print(k, str(va)[:110],'->',str(vb)[:110])
    for k in sorted(fb):
        if any(s in k.lower() for s in ('s1_enabled','s2','max_own','own')) : print('  ',k,fb[k])
