import sys,json
sys.argv=['x'];sys.path.insert(0,'.')
import score_r5 as S
a,items,_,_=S.load(S.O.parent/'out3/A4/ret',S.O/'A',0,200,'candidates_argmax')
ks=[k for k,i in items.items() if i['question_type']==S.DISTANCE]
n=sum(1 for k in ks if S.scorers.records(a[k]['output'])); print('with records',n,len(ks))
k=next(k for k in ks if S.scorers.records(a[k]['output']))
out=a[k]['output']
for f in ('calls','scale','heads','entries','finish'): print(f, json.dumps(out.get(f),default=str)[:700])
rs=S.scorers.records(out);print('rec0',json.dumps(rs[0],default=str)[:900]);print('printed',S.scorers.printed(rs[0]))
print('item',json.dumps({x:items[k][x] for x in items[k] if x not in ('frames',)},default=str)[:500])
