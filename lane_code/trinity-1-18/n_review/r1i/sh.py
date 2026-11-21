import json,base64,hashlib
def load(p):
    v=json.load(open(p))
    if isinstance(v,dict) and v.get('encoding') in ('base64','base64-json') and 'payload' in v: v=json.loads(base64.b64decode(v['payload']))
    return v
def shape(x,d=0,maxd=3):
    if isinstance(x,dict):
        if d>=maxd: return '{%d keys}'%len(x)
        return {k:shape(v,d+1,maxd) for k,v in list(x.items())[:25]}
    if isinstance(x,list): return '[%d]%s'%(len(x), (' '+json.dumps(shape(x[0],d+1,maxd))[:200]) if x else '')
    if isinstance(x,str): return x[:70]
    return x
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w/work'
for p in (W+'/d173881/173881/receipt.json', W+'/d173912/173912/k_dr_p_q_pr_receipt.json', W+'/d173912/173912/RESULT.json'):
    try: print('==',p); print(json.dumps(shape(load(p)),indent=1)[:3500])
    except Exception as e: print('ERR',e)
