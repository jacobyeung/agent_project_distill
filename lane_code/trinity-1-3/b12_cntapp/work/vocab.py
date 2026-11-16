import sqlite3,json,collections,re
S='/scratch/jjyeung/orch_n30/rows_rebuild3/out/rows/d0_v5/vqa/rows.sqlite'
con=sqlite3.connect(f'file:{S}?mode=ro&immutable=1',uri=True)
tmpl=collections.Counter(); vocab=collections.defaultdict(collections.Counter); ans=collections.Counter(); atmpl=collections.Counter(); aans=collections.Counter()
for i,row,t in con.execute('select i,row,target from rows'):
    d=json.loads(row); qt=d['question_type']; q=d['student_input']['question']; ds=d['dataset']
    if qt=='object_counting' and 'count_kind' not in d:
        m=re.search(r'(?:How many|number of|Count the) (.+?)\(s\)',q)
        if m: tmpl[q.replace(m.group(1),'X')]+=1; vocab[('count',ds)][m.group(1)]+=1
        ans[(ds,d['answer'])]+=1
    if qt=='obj_appearance_order':
        m=re.search(r'(?:categories in the video|first appearances|these categories|order of)[^:]*: (.+?)[?.]$',q) or re.search(r'lists (.+?) in the chronological',q)
        if m:
            objs=[x.strip() for x in m.group(1).split(',')]
            atmpl[q.replace(m.group(1),'LIST')]+=1
            for o in objs: vocab[('app',ds)][o]+=1
        else: atmpl[q]+=1
        aans[(ds,d['answer'])]+=1
print('COUNT templates'); [print(v,k) for k,v in tmpl.most_common(20)]
print('APP templates'); [print(v,k) for k,v in atmpl.most_common(20)]
print(sorted(ans.items(), key=lambda t:(t[0][0],int(t[0][1]))))
print(sorted(aans.items()))
for k,v in vocab.items(): print(k,len(v),v.most_common(25))
json.dump({f'{a}|{b}':dict(v) for (a,b),v in vocab.items()},open('d0_vocab.json','w'),indent=0)
