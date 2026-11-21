import json, sqlite3, collections, sys
W=sys.argv[1]
out=json.load(open(W+'/out601.json'))
nei=[o for o in out if o['cls']=='NEITHER']
ROWS='/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite'
c=sqlite3.connect('file:'+ROWS+'?mode=ro',uri=True)
seen=set(); allq=[]
for o in nei:
    r=json.loads(c.execute('SELECT row FROM rows WHERE i=?',(o['i'],)).fetchone()[0])
    s=o['scene']; allq.append((o['i'],r['dataset'],s,r['qid'],o['question_type'],r.get('answer')))
    if s in seen: continue
    seen.add(s)
    fr=r['student_input']['frames']
    print('SCENE',r['dataset']+'/'+s,'frame0',fr[0]['path'],'nframes',len(fr))
    small={k:(v if len(json.dumps(v))<300 else '<%d>'%len(json.dumps(v))) for k,v in r.items() if k not in('student_input','target')}
    print('  row',json.dumps(small)[:1200])
    if isinstance(r.get('provenance'),dict): print('  prov',json.dumps(r['provenance'])[:800])
print('QIDS'); [print('Q',*a) for a in allq]
json.dump([a[3] for a in allq],open(W+'/qid127.json','w'))
