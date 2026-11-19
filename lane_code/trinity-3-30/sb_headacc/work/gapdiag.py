"""CPU read of the routed distance returns on this node: what in the stage-1 record goes with a bad gap."""
import sys, json, re, statistics as st
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
S = K._scorer(); O = S.O
fac={'m':1.0,'cm':100.0,'ft':1/.3048,'in':1/.0254}
def unit(q):
    q=q.lower()
    if re.search(r'centimet|\bcm\b',q): return 'cm'
    if re.search(r'\bfeet\b|\bfoot\b|\bft\b',q): return 'ft'
    if re.search(r'\binch',q): return 'in'
    return 'm'
def mra(p,g):
    e=abs(p-g)/abs(g); return sum(e<=1-t/100+1e-12 for t in range(50,100,5))/10
def load(step):
    if step==200:
        rows, items, _, _ = S.load(O.parent/'out3/A4/ret', O/'A', 0, 200, 'candidates_argmax')
    else:
        rows, items, _, _ = S.load(S.BASE/'b1/work/ret', S.BASE/'b1', 1, 544, 'candidates_argmax')
    out=[]
    for k in sorted(rows):
        it=items[k]
        if it['question_type']!='object_abs_distance': continue
        o=rows[k]['output']; recs=o['calls']['records']
        g=[r for r in recs if r.get('family')=='ground' and r.get('stage1')]
        gp=[re.search(r'distance ([\d.]+) m', r.get('response') or '') for r in recs if r.get('family')=='gap']
        gp=[float(x.group(1)) for x in gp if x]
        if not gp: continue
        truth_m=float(it['answer'])/fac[unit(it['question'])]
        objs={}
        for r in g:
            s=r['stage1']; resp=r.get('response') or ''
            m=re.search(r'frames ([\d,]+) \(best (\d+)\)', resp); z=re.search(r'size ([\d.]+) x ([\d.]+) x ([\d.]+) m', resp)
            if not m or not z: continue
            c=s['candidates']; lg=sorted([x['logit'] for x in c if x.get('logit') is not None], reverse=True)
            ch=s.get('chosen_index',-1)
            allfr=set(f for x in c for f in x['frames'])
            objs[s['name_key']]=dict(nfr=len(m.group(1).split(',')), size=sorted(map(float,z.groups()),reverse=True),
                ncand=s['linked_candidates'], margin=(lg[0]-lg[1]) if len(lg)>1 else None, top_is_chosen=(c[ch]['logit']==lg[0]) if 0<=ch<len(c) and lg else None,
                sam_frames=sum(1 for n in s['sam3']['kept_per_frame'] if n>0), union_frames=len(allfr), peak=c[ch]['peak'] if 0<=ch<len(c) else None,
                null_wins=s.get('null_would_win'))
        if len(objs)<2: continue
        out.append(dict(id=k, ds=it['dataset'], truth=truth_m, gap=gp[-1], s=mra(gp[-1],truth_m), ratio=gp[-1]/truth_m, objs=objs))
    return out
def tab(rows, key, label):
    b={}
    for r in rows: b.setdefault(key(r),[]).append(r)
    print('--', label)
    for k in sorted(b, key=str):
        v=b[k]; print('  %-28s n=%3d gapMRA=%5.1f medratio=%.2f over=%d' % (k, len(v), 100*sum(x['s'] for x in v)/len(v), st.median(x['ratio'] for x in v), sum(x['ratio']>1 for x in v)))
for step in (544,200):
    R=load(step); print('==== step',step,'gaps with two boxed objects',len(R),'gapMRA %.1f'%(100*sum(r['s'] for r in R)/len(R)))
    mn=lambda r,f: min(o[f] for o in r['objs'].values())
    mx=lambda r,f: max(o[f] for o in r['objs'].values())
    tab(R, lambda r: ('1' if mn(r,'nfr')==1 else '2' if mn(r,'nfr')==2 else '3-4' if mn(r,'nfr')<=4 else '5+'), 'min grounded frames of the two objects')
    tab(R, lambda r: ('single cand both' if mx(r,'ncand')==1 else '2-3 cands' if mx(r,'ncand')<=3 else '4+ cands'), 'max linked candidates over the two objects')
    def amb(r):
        ms=[o['margin'] for o in r['objs'].values() if o['margin'] is not None]
        return 'no rival' if not ms else ('margin<1' if min(ms)<1 else 'margin>=1')
    tab(R, amb, 'selector logit margin (top - second), min over objects')
    tab(R, lambda r: ('lowcov' if mn(r,'nfr')<3 else 'cov3+')+' / '+('rival' if mx(r,'ncand')>1 else 'single'), 'coverage x rival')
    tab(R, lambda r: r['ds'], 'dataset')
    tab(R, lambda r: ('<1m' if r['truth']<1 else '1-2m' if r['truth']<2 else '2-4m' if r['truth']<4 else '4m+'), 'truth band')
    tab(R, lambda r: 'null would win on an object' if any(o['null_wins'] for o in r['objs'].values()) else 'null loses both', 'null slot')
    tab(R, lambda r: ('min peak<0.5' if mn(r,'peak')<0.5 else 'min peak 0.5-0.8' if mn(r,'peak')<0.8 else 'min peak>=0.8'), 'SAM3 peak of the chosen candidate, min over objects')
    # linking fragmentation: frames SAM 3 proposed the name in vs frames of the chosen candidate
    O2=[o for r in R for o in r['objs'].values()]
    print('  objects',len(O2),'median frames chosen',st.median(o['nfr'] for o in O2),'median frames with any SAM3 proposal',st.median(o['sam_frames'] for o in O2),'median union frames over candidates',st.median(o['union_frames'] for o in O2))
    print('  frames hist chosen:', {k: sum(1 for o in O2 if (o['nfr'] if o['nfr']<6 else 6)==k) for k in range(1,7)}, '(6 = 6+)')
    print('  objects with 1 cand: %d; 2-3: %d; 4+: %d' % (sum(o['ncand']==1 for o in O2), sum(1<o['ncand']<=3 for o in O2), sum(o['ncand']>3 for o in O2)))
    print('  box longest edge median %.2f m; share of boxes with longest edge < 0.3 m: %.2f; second edge < 0.1 m: %.2f' % (st.median(o['size'][0] for o in O2), sum(o['size'][0]<.3 for o in O2)/len(O2), sum(o['size'][1]<.1 for o in O2)/len(O2)))
    json.dump(R, open('gapdiag_%d.json'%step,'w'))
