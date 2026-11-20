import json,gzip,random,collections,sys
R='/scratch/jjyeung/orch_n30/corpus/stage2/reads/'
ROUTED={
 544:['469ddece_s544_devS1_routed_b1.r0','469ddece_s544_devS1_routed_b1.r1','469ddece_s544_R0dev_D580_seg0_172957','469ddece_s544_R0dev_D580_seg1_173053','469ddece_s544_R0dev_D580_seg2_173202','469ddece_s544_room134_routed_b2'],
 600:['6ed2c7aa_s600_devS1cam_c600_173348'],
 400:['6ed2c7aa_s400_devS1_routed_A10b','6ed2c7aa_s400_R0dev_D580_173241','6ed2c7aa_s400_room134_routed_B10'],
}
DIRECT={544:['469ddece_s544_devS1R0_direct_adff67f7ae9'],600:['6ed2c7aa_s600_devS1R0_direct_a136f924ab1'],400:['6ed2c7aa_s400_devS1R0_direct_a59a7bff4c4']}
def load(rid):
    for l in gzip.open(R+rid+'.jsonl.gz','rt'): yield json.loads(l)
def ds(rec):
    sc=rec.get('scene') or ''
    s=sc.split('/')[0] if '/' in sc else ((rec.get('room') or '').split('/')[0] if '/' in (rec.get('room') or '') and not (rec.get('room') or '').startswith('d') else ((rec.get('raw') or {}).get('input') or {}).get('dataset',''))
    return {'arkitscenes':'ARKit','scannet':'ScanNet','scannetppv2':'ScanNet++','scannetpp':'ScanNet++'}.get(s,s)
def setname(rid,rec):
    if 'R0dev' in rid: return 'R0-dev'
    if 'room134' in rid: return 'dev-S1' if (rec.get('item_id') or '').startswith(('vsi590k','devs1')) and 'R0' not in str(rec.get('set')) else 'room134'
    return 'dev-S1'
def boot_mean(rows,n=10000,seed=0):
    rooms=collections.defaultdict(list)
    for r in rows: rooms[r[0]].append(r[1])
    ks=list(rooms); rnd=random.Random(seed); m=[]
    for _ in range(n):
        s=[v for k in (rnd.choice(ks) for _ in ks) for v in rooms[k]]; m.append(sum(s)/len(s))
    return m
def ci(m):
    m=sorted(m); return [round(100*m[249],1), round(100*m[9749],1)]
out=[]
for step,rids in ROUTED.items():
    direct={}
    for rid in DIRECT.get(step,[]):
        for rec in load(rid):
            a=rec['arms'] or {}
            sc=(a.get('full') or {}).get('score')
            if sc is not None: direct[rec['item_id']]=sc
    cells=collections.defaultdict(list)
    for rid in rids:
        for rec in load(rid):
            sc=rec['arms']['tower']['score']
            if sc is None: continue
            st=('room134/R0-dev' if rec['item_id'].startswith('r0_') else 'room134/dev-S1') if 'room134' in rid else ('R0-dev' if 'R0dev' in rid else 'dev-S1')
            cells[(st+'|'+rid,rec['question_type'])].append((rec['room'] or rec['scene'], sc, ds(rec), direct.get(rec['item_id'])))
    for (st,qt),rows in sorted(cells.items()):
        byd=collections.defaultdict(list)
        for room,sc,d,dsc in rows: byd[d].append((room,sc,dsc))
        line=dict(step=step,set=st,type=qt,n=len(rows))
        for d,rr in sorted(byd.items()):
            m=boot_mean([(a,b) for a,b,_ in rr]); line[d]=dict(n=len(rr),score=round(100*sum(b for _,b,_ in rr)/len(rr),1),ci=ci(m))
            dd=[(a,c) for a,_,c in rr if c is not None]
            if dd: line[d]['direct_same_items']=dict(n=len(dd),score=round(100*sum(c for _,c in dd)/len(dd),1))
        ark=[(a,b) for a,b,_ in byd.get('ARKit',[])]; rest=[(a,b) for d,rr in byd.items() if d!='ARKit' for a,b,_ in rr]
        if ark and rest:
            ma=boot_mean(ark,seed=1); mr=boot_mean(rest,seed=2); diff=[x-y for x,y in zip(ma,mr)]
            line['ARKit_minus_rest']=dict(diff=round(100*(sum(b for _,b in ark)/len(ark)-sum(b for _,b in rest)/len(rest)),1),ci=ci(diff))
            da=[(a,c) for a,_,c in byd.get('ARKit',[]) if c is not None]; dr=[(a,c) for d,rr in byd.items() if d!='ARKit' for a,_,c in rr if c is not None]
            if da and dr:
                line['ARKit_minus_rest_direct_same_items']=round(100*(sum(c for _,c in da)/len(da)-sum(c for _,c in dr)/len(dr)),1)
        out.append(line); print(json.dumps(line))
json.dump(out,open('/dev/shm/c25/price/PRICE_ARKIT.json','w'),indent=1)
