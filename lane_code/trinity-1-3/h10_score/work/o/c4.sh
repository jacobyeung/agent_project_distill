PN=/project/community/jjyeung/okh7/e6fc152498/p446
grep -n "M3\|follow\|stick\|eligible" $PN/h1eval/runner.py | head -40
python3 - <<'X'
import json,collections
F='/project/community/jjyeung/okh7/e6fc152498/r2/sj/h10sub3_b01ec87a6f29b00029ad2/items.jsonl'
c=collections.Counter(); ex={}
for l in open(F):
    r=json.loads(l)
    for x in r['output']['calls']['records']:
        resp=(x.get('response') or '')
        first=resp.split('\n')[0]
        key=(x['family'],x['served'], first.split(':',1)[-1].strip()[:40] if 'frames' not in first else 'frames...')
        c[key]+=1; ex.setdefault(key,(r['id'],r['mode'],x['call'][:80],resp[:200]))
for k,v in c.most_common(40): print(v,k,'|',ex[k])
X
