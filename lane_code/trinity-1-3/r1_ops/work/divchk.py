import json,sqlite3,collections,sys
D=json.load(open(sys.argv[1])); train=set(D['train_scenes']); held=set(D['heldout_scenes'])
c=sqlite3.connect('file:/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite?immutable=1',uri=True)
bad=collections.Counter(); ex=collections.defaultdict(list); seen=set(); dup=0
for i,row in c.execute('select i,row from rows order by i'):
    r=json.loads(row); s=r['dataset']+'/'+r['scene']
    if r['qid'] in seen: dup+=1
    seen.add(r['qid'])
    if s not in train or s in held:
        k=('heldout' if s in held else 'not_train',r.get('question_type'),'appended' if i>=195471 else 'base', r.get('pool'))
        bad[k]+=1
        if len(ex[k])<3: ex[k].append((i,r['qid'],s))
print('dup',dup); print('train',len(train),'held',len(held))
for k,v in bad.most_common(): print(v,k,ex[k])
