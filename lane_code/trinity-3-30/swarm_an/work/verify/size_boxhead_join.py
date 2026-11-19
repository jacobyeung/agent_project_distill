"""Would routing object size through the deployed box head help? Join dev-S1 size items with the boxes the routed distance
read grounded for the same object name in the same room; compare the printed box's longest edge with the size truth."""
import sys,re,json,statistics as st; sys.path.insert(0,'/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
from collections import Counter
def mra(p,g):
    e=abs(p-g)/abs(g); return sum(e<=1-t/100+1e-12 for t in range(50,100,5))/10
def tocm(q):
    q=q.lower()
    if re.search(r'centimet|\bcm\b',q): return 1.0
    if re.search(r'\binch',q): return 2.54
    if re.search(r'\bfeet\b|\bfoot\b|\bft\b',q): return 30.48
    if re.search(r'\bmeters?\b|\bmetres?\b',q): return 100.0
    return None
size=K.direct('R1',200,'dev-S1',types=['object_size_estimation'])
print('units asked:',Counter({1.0:'cm',2.54:'in',30.48:'ft',100.0:'m',None:'?'}[tocm(r['question'])] for r in size))
key=lambda room: room.split('/')[-1]
out={}
for step in (200,544):
    boxes={}
    for r in K.routed(step,types=['object_abs_distance']):
        for c in r['calls']:
            if c['family']!='ground' or not c['response']: continue
            m=re.search(r'obj="([^"]+)"',c['call']); s=re.search(r'size ([\d.]+) x ([\d.]+) x ([\d.]+) m',c['response'])
            if m and s: boxes.setdefault((key(r['room']),m.group(1).lower()),[]).append(max(float(x) for x in s.groups())*100)
    n=0;hs=0.0;ds=0.0;ratios=[]
    for r in size:
        f=tocm(r['question'])
        if f is None: continue
        cands=[o for (rm,o) in boxes if rm==key(r['room']) and re.search(r'\b'+re.escape(o)+r'\b',r['question'].lower())]
        if not cands: continue
        o=max(cands,key=len); p=st.median(boxes[(key(r['room']),o)]); gcm=float(r['gt'])*f
        n+=1; hs+=mra(p,gcm); ds+=r['score']; ratios.append(p/gcm)
    out[step]=dict(joined=n,box_head_mra=round(100*hs/n,1),direct_mra_same_items=round(100*ds/n,1),median_ratio=round(st.median(ratios),2),share_within_25pct=round(sum(abs(x-1)<=.25 for x in ratios)/n,2))
    print(step,out[step])
json.dump(out,open('SIZE_BOXHEAD_JOIN.json','w'),indent=1)
