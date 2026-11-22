import json,sys,base64
sys.path.insert(0,'/scratch/jjyeung/orch_n30/n_review1l/work/taskA')
from taska_diff import walk
def dec(p):
    d=json.load(open(p))
    while isinstance(d,dict) and d.get('encoding') in ('base64-json','base64'):
        raw=base64.b64decode(d['payload']).decode()
        if d['encoding']=='base64':
            try: d=json.loads(raw)
            except Exception: return raw
        else: d=json.loads(raw)
    return d
for n in ['BUILD.json','k/7.json','k/a.json','k/c.json','k/c0.json','k/n.json','k/p.json']:
    a,b=dec('kq/old/'+n),dec('kq/new/'+n); out=[]; walk(a,b,'',out)
    print('==',n,len(out),'differences')
    for p,x,y in out[:12]: print('   ',p,str(x)[:70],'->',str(y)[:70])
