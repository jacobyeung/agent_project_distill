W=/project/community/jjyeung/okh7/e6fc152498
cat > $W/callcount.py <<'P'
import tarfile,gzip,json,collections,sys
t=tarfile.open('/home/jjyeung/okit/i/eb3429c5/eb3429c5.tar')
def calls(r):
    ev=r.get('events') or []
    return [e['call'] for e in ev if isinstance(e,dict) and 'call' in e]
out={}
for m in t.getmembers():
    if not m.name.endswith('.jsonl.gz'): continue
    dist=collections.Counter(); types=collections.Counter(); ns=collections.Counter(); mx=collections.defaultdict(int); ex={}; nsex={}
    for l in gzip.open(t.extractfile(m),'rt'):
        r=json.loads(l)
        q=r.get('question_type') or r.get('type') or r.get('task') or '?'
        c=calls(r); g=sum(1 for x in c if x.startswith('<ground') or x.startswith('<gap'))
        types[q]+=1; dist['%s|%d|%d'%(q,len(c),g)]+=1; ns['%s|%s'%(q,bool(r.get('not_seen')))]+=1
        if g>mx[q]: mx[q]=g; ex[q]=dict(qid=r.get('qid'),calls=c[:10],resp=[(e.get('response') or '')[:60] for e in r['events'][:10] if isinstance(e,dict)])
        if r.get('not_seen') and q not in nsex: nsex[q]=dict(qid=r.get('qid'),calls=c[:10],resp=[(e.get('response') or '')[:80] for e in r['events'][:10] if isinstance(e,dict)],answer=str(r.get('answer'))[:80],tail=str(r.get('suffix') or r.get('answer_content'))[-300:])
    out[m.name]=dict(types=dict(types),max_ground_gap=dict(mx),dist=dict(dist.most_common(15)),not_seen=dict(ns),max_example=ex,not_seen_example=nsex)
    print(m.name, dict(types), dict(mx), flush=True)
json.dump(out,open(sys.argv[1],'w'),indent=1)
print('DONE')
P
cd $W && nohup nice -n 19 ionice -c3 python3 callcount.py $W/callcount.json > $W/callcount.out 2>&1 &
sleep 20; cat $W/callcount.out
