import sys, re, json, collections, statistics as st
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
items=[json.loads(l) for l in open('r0_appearance_items.jsonl')]
R=[r for r in K.direct('R1', 200, 'R0-dev') if r['type']=='obj_appearance_order']
byq={r['question']:r for r in R}
idm=json.load(open(K.IDMAP)) if True else {}
ex=w1=n=0; early=late=0; joined=0; order_ok=0; order_n=0; ties=0
for it in items:
    r=byq.get(it['question'])
    if r is None: continue
    joined+=1
    gt=it['gt']['first_pos_f32']
    m=re.search(r'first frame showing each object: (.+?)\.\s', r['text'].replace('\n',' ')+' ')
    if not m: continue
    st_={}
    for part in m.group(1).split(';'):
        q=re.match(r'\s*(.+?) frame ([\d.]+)\s*$', part)
        if q: st_[q.group(1).strip()]=float(q.group(2))
    if set(st_)!=set(gt): continue
    order_n+=1
    for k in gt:
        d=st_[k]-gt[k]; n+=1; ex+=(d==0); w1+=(abs(d)<=1); early+=(d<-1); late+=(d>1)
    go=sorted(gt, key=lambda k: gt[k]); so=sorted(st_, key=lambda k: st_[k])
    order_ok+=(go==so); ties+=(len(set(gt.values()))<len(gt))
print('items',len(items),'joined',joined,'parsed with all names',order_n)
print('model stated first-seen vs GT (f32 positions): objects %d exact %.3f within-one %.3f early(>1) %.3f late(>1) %.3f' % (n, ex/n, w1/n, early/n, late/n))
print('stated order equals GT order: %d of %d (%.1f%%); items with GT ties: %d' % (order_ok, order_n, 100*order_ok/order_n, ties))
print('GT first_pos range example', items[0]['gt'])
# scale check and pairwise order
pairs=ok=0; S=[]; G=[]
for it in items:
    r=byq[it['question']]; gt=it['gt']['first_pos_f32']
    m=re.search(r'first frame showing each object: (.+?)\.\s', r['text'].replace('\n',' ')+' ')
    st_={}
    for part in m.group(1).split(';'):
        q=re.match(r'\s*(.+?) frame ([\d.]+)\s*$', part)
        if q: st_[q.group(1).strip()]=float(q.group(2))
    ks=sorted(gt)
    for k in ks: S.append(st_[k]); G.append(gt[k])
    for a in range(len(ks)):
        for b in range(a):
            if gt[ks[a]]!=gt[ks[b]] and st_[ks[a]]!=st_[ks[b]]:
                pairs+=1; ok+=((gt[ks[a]]<gt[ks[b]])==(st_[ks[a]]<st_[ks[b]]))
print('pairwise order from stated frames: %.3f (%d pairs)' % (ok/pairs, pairs))
print('stated/gt median ratio %.2f; share stated>32: %.3f; max stated %.0f' % (st.median(s/g for s,g in zip(S,G)), sum(s>32 for s in S)/len(S), max(S)))
for f in (1.0, 0.5, 0.25):
    print('scale %.2f: exact %.3f within-one %.3f' % (f, sum(round(s*f)==g for s,g in zip(S,G))/len(S), sum(abs(s*f-g)<=1 for s,g in zip(S,G))/len(S)))
