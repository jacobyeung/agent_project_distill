import json,collections,math,numpy as np
res=json.load(open('rv_out2.json'))
rows=[o for x in res for o in x['rows']]
print('errors',collections.Counter(e.split()[0] for o in rows for e in o['errors']))
def score(fn,sub):
    s=0.
    for o in sub: s+=fn(o)
    return round(s/len(sub),3)
T=sorted(set(o['t'] for o in rows))
for t in T:
    sub=[o for o in rows if o['t']==t];out={}
    if t.startswith('camera'):
        def pick(key,sign=1):
            def f(o):
                F=o['feat'];vals=[sign*key(q,o) for q in F];m=max(vals);w=[q['label'] for q,v in zip(F,vals) if v==m]
                return (o['ans'] in w)/len(w)
            return f
        out['max_share_f']=score(pick(lambda q,o:q['sf']),sub)
        out['fs_closest_to_f']=score(pick(lambda q,o:-abs(q['fs']-o['f'])),sub)
        out['largest_box']=score(pick(lambda q,o:q['vol']),sub)
        out['fs_latest_le_f']=score(pick(lambda q,o:(q['fs'] if q['fs']<=o['f'] else -99)),sub)
    else:
        def bin_(fn):
            def f(o):
                a,b=o['feat'];v=fn(a,b,o)
                if v==0:return .5
                first=o['ans'] in ('Near','Up','Left')
                return float((v>0)==first)
            return f
        out['a_more_visible_in_f']=score(bin_(lambda a,b,o:np.sign(a['sf']-b['sf'])),sub)
        out['a_fs_closer_to_f']=score(bin_(lambda a,b,o:np.sign(abs(b['fs']-o['f'])-abs(a['fs']-o['f']))),sub)
        out['a_bigger']=score(bin_(lambda a,b,o:np.sign(a['vol']-b['vol'])),sub)
        out['a_fs_earlier']=score(bin_(lambda a,b,o:np.sign(b['fs']-a['fs'])),sub)
        if t.endswith('ud'):
            # leave-one-out label prior
            win=collections.defaultdict(lambda:[0,0])
            for o in sub:
                a,b=o['feat'];u=o['ans']=='Up';win[a['label']][0]+=u;win[a['label']][1]+=1;win[b['label']][0]+=(not u);win[b['label']][1]+=1
            def lp(o):
                a,b=o['feat'];u=o['ans']=='Up'
                wa=(win[a['label']][0]-u)/max(win[a['label']][1]-1,1) if win[a['label']][1]>1 else .5
                wb=(win[b['label']][0]-(not u))/max(win[b['label']][1]-1,1) if win[b['label']][1]>1 else .5
                if wa==wb:return .5
                return float((wa>wb)==u)
            out['label_prior_LOO']=score(lp,sub)
        if t.endswith('lr'):
            gaps=[abs(math.atan2(a['x'],a['zz'])-math.atan2(b['x'],b['zz'])) for a,b in (o['feat'] for o in sub)];out['bearing_gap_deg_q']=np.round(np.degrees(np.quantile(gaps,[0,.1,.5])),1).tolist()
            out['max_abs_bearing_deg_median']=round(float(np.degrees(np.median([max(abs(math.atan2(q['x'],q['zz'])) for q in o['feat']) for o in sub]))),1)
            out['both_outside_hfov']=sum(all(abs(math.atan2(q['x'],q['zz']))>math.radians(31) for q in o['feat']) for o in sub)
        if t.endswith('ud'):
            out['gap_q']=np.round(np.quantile([abs(a['zc']-b['zc']) for a,b in (o['feat'] for o in sub)],[0,.1,.5]),2).tolist()
        if t.endswith('nf'):
            out['gap_q']=np.round(np.quantile([abs(a['d']-b['d']) for a,b in (o['feat'] for o in sub)],[0,.1,.5]),2).tolist()
            out['near_obj_dist_lt_0.05']=sum(min(a['d'],b['d'])<.05 for a,b in (o['feat'] for o in sub))
    if t.startswith('camera'):
        out['closest_d<0.05 (camera inside/at box)']=sum(min(q['d'] for q in o['feat'])<.05 for o in sub)
        out['gap_q']=np.round(np.quantile([sorted(q['d'] for q in o['feat'])[1]-sorted(q['d'] for q in o['feat'])[0] for o in sub],[0,.1,.5]),2).tolist()
    print(t,out)
