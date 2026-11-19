import sys,re,json; sys.path.insert(0,'/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
def mra(p,g):
    if p is None: return 0.0
    g=float(g); 
    if g==0: return float(p==0)
    e=abs(p-g)/abs(g); return sum(e<=1-t+1e-12 for t in [x/100 for x in range(50,100,5)])/10
def num(s):
    try: return float(re.findall(r'[-+]?\d+(?:\.\d+)?',str(s))[-1])
    except Exception: return None
out={}
for step in (544,200):
    rows=K.routed(step)
    for t in ('camera_displacement','camera_rotation','camera_movement_direction'):
        rs=[r for r in rows if r['type']==t]; n=len(rs); c=dict(n=n,called=0,args_ok=0,faithful=0,head=0.0,score=0.0,unfaithful_ids=[],extra_calls=0)
        for r in rs:
            c['score']+=r['score']
            if not r['calls']: continue
            c['called']+=1; c['extra_calls']+=len(r['calls'])>1
            qf=re.search(r'frame (\d+) and frame (\d+)',r['question']); cf=re.search(r'from=(\d+) to=(\d+)',r['calls'][-1]['call'])
            c['args_ok']+= bool(qf and cf and qf.groups()==cf.groups())
            resp=r['calls'][-1]['response'] or ''
            if t=='camera_displacement':
                p=num(re.search(r'distance = ([-\d.]+)',resp).group(1)) if 'distance' in resp else None
                a=num(r['answer']); f=(p is not None and a is not None and abs(a-p)<0.006); c['head']+=mra(p,r['gt'])
            elif t=='camera_rotation':
                p=num(re.search(r'turn = ([-+\d.]+)',resp).group(1)) if 'turn' in resp else None
                a=num(r['answer']); f=(p is not None and a is not None and abs(a-p)<0.51)
                c['head']+= r['score'] if f else float('nan')
            else:
                m=re.search(r'dx = ([-+\d.]+) m, dy = ([-+\d.]+) m, dz = ([-+\d.]+)',resp)
                if m:
                    dx,dz=float(m.group(1)),float(m.group(3)); comp={'backward':-dz,'right':dx,'left':-dx,'forward':dz}; best=max(comp,key=comp.get)
                    opt={o.split('. ',1)[1].lower():o[0] for o in r['options']}; f=(str(r['answer']).strip()[:1]==opt.get(best)); c['head']+= float(opt.get(best)==r['gt'])
                else: f=False
            c['faithful']+=f
            if not f: c['unfaithful_ids'].append(r['id'])
        c['score']=round(100*c['score']/n,2); c['head']=round(100*c['head']/n,2) if c['head']==c['head'] else None
        out['%s@%d'%(t,step)]=c
        print(step,t,{k:(v if k!='unfaithful_ids' else v[:4]) for k,v in c.items()})
json.dump(out,open('ROUTED_TABLE_camera.json','w'),indent=1)
