import sqlite3,json,hashlib,collections,sys
sys.path.insert(0,'/scratch/jjyeung/orch_n30/rows_rebuild3/work/validator')
import trace_grammar as g
def con(p): return sqlite3.connect('file:'+p+'?immutable=1',uri=True)
v7=con('/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite')
v6=con('/scratch/jjyeung/orch_n30/rows_a2/out/a2_vqa_v6/vqa/rows.sqlite')
h6=hashlib.sha256();h7=hashlib.sha256()
for i,r,t in v6.execute('select i,row,target from rows order by i'): h6.update((json.dumps([i,r,t],separators=(',',':'),ensure_ascii=True)+'\n').encode())
qids=collections.Counter();types=collections.Counter();tcol=collections.Counter();fails=[];n=0
for i,r,t in v7.execute('select i,row,target from rows order by i'):
  if i<195471: h7.update((json.dumps([i,r,t],separators=(',',':'),ensure_ascii=True)+'\n').encode())
  d=json.loads(r);qids[d['qid']]+=1;types[d['question_type']]+=1;tcol[t=='{}']+=1;n+=1
  if i>=195471:
    e=g.validate_row(d)
    if e: fails.append((i,[tuple(x)[:2] for x in e]))
print('v6',h6.hexdigest(),'v7prefix',h7.hexdigest(),'equal',h6.digest()==h7.digest())
print('rows',n,'dup qids',sum(1 for q,c in qids.items() if c>1),'target col == {} :',dict(tcol))
print('validator fails on new',len(fails),fails[:5])
c=json.load(open('/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/COUNTS_V7.json'))
json.dump(dict(types),open('my_type_counts.json','w'),indent=1,sort_keys=True)
print(sorted(types.items()))
print('COUNTS_V7 keys',list(c)[:10])
