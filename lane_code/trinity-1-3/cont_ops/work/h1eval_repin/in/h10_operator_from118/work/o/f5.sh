W=/project/community/jjyeung/okh7/e6fc152498
cat > $W/callcount.py <<'P'
import tarfile,gzip,json,collections,sys
t=tarfile.open('/home/jjyeung/okit/i/eb3429c5/eb3429c5.tar')
def calls(row):
    raw=row.get('routing',row)
    if 'ground_record' in raw: return [e['call'] for e in raw['ground_record']['events']]
    return [e['token'].strip() for e in raw.get('events',[]) if e.get('kind') in ('tool_call','ground_call')]
out={}
for m in t.getmembers():
    if not m.name.endswith('.jsonl.gz'): continue
    dist=collections.Counter(); types=collections.Counter(); ns=collections.Counter(); keys=None; mx=collections.defaultdict(int); ex={}
    for l in gzip.open(t.extractfile(m),'rt'):
        r=json.loads(l); keys=keys or sorted(r)[:60]
        q=r.get('question_type') or r.get('type') or r.get('task') or '?'
        c=calls(r); g=sum(1 for x in c if x.startswith('<ground') or x.startswith('<gap'))
        types[q]+=1; dist[(q,len(c),g)]+=1; mx[q]=max(mx[q],g); ns[(q,bool(r.get('not_seen')))]+=1
        if g>=mx[q] and q not in ex or g>3 and q not in ex: ex[q]=c[:8]
    out[m.name]=dict(types=dict(types),max_ground_gap=dict(mx),dist={'|'.join(map(str,k)):v for k,v in dist.most_common(12)},not_seen={'|'.join(map(str,k)):v for k,v in ns.items()},keys=keys,example=ex)
    print(m.name, dict(types), dict(mx), flush=True)
json.dump(out,open(sys.argv[1],'w'),indent=1)
print('DONE')
P
cd $W && nohup nice -n 19 ionice -c3 python3 callcount.py $W/callcount.json > $W/callcount.out 2>&1 &
sleep 5; cat $W/callcount.out
