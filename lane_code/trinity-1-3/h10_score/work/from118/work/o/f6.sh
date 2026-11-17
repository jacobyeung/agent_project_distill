nice -n 19 python3 - <<'P'
import tarfile,gzip,json
t=tarfile.open('/home/jjyeung/okit/i/eb3429c5/eb3429c5.tar')
m=t.getmember('7e4e92918e312afd.jsonl.gz')
for l in gzip.open(t.extractfile(m),'rt'):
    r=json.loads(l)
    if 'object_abs_distance' in (r.get('question_type'),r.get('type'),r.get('task')):
        print(sorted(r)); print(json.dumps(r['events'])[:800])
        for k in r:
            v=r[k]
            if isinstance(v,str) and ('<ground' in v or '<gap' in v): print('FIELD',k, v[:1200])
            if isinstance(v,list) and v and isinstance(v[0],dict) and any('<ground' in json.dumps(x) for x in v[:3]): print('LISTFIELD',k,json.dumps(v)[:1200])
        break
P
