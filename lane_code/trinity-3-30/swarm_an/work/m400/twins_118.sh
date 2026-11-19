cd /scratch/jjyeung/orch_n30/sb_rowD7f/out || exit 1
ls -la NEW_ROWS.jsonl | head -2
nice -n 10 python3 - <<'PY'
import json,re,random
from collections import Counter,defaultdict
rows=[json.loads(l) for l in open('NEW_ROWS.jsonl') if l.strip()]
print('rows',len(rows)); r0=rows[0]
print('keys',sorted(r0.keys())); print('prov',json.dumps(r0.get('provenance',{}).get('sb_rowD7'))[:600])
def think(t): return t.split('</think>')[0].replace('<think>','').strip()
T=defaultdict(Counter)
for d in rows:
    si=d['student_input']; q=si['question']; ty=d['category'].split('_')[-1]
    opts={o[0]:o[3:].strip() for o in si['options']}; a=opts.get(d['answer'])
    th=think(d['target']); L=[l for l in th.split('\n') if l.strip()]
    s2=[l for l in L if l.startswith('Step 2')]; s2=s2[0] if s2 else ''
    fb='back' if 'behind' in s2 else ('front' if 'in front' in s2 else 'none')
    m=re.search(r'(facing away from|facing in the opposite direction of|with my back to|turned away from|back toward)',q)
    k=ty; T[k]['n']+=1; T[k]['ans '+str(a)]+=1; T[k]['s2fb '+fb]+=1; T[k]['open '+L[0][:14]]+=1; T[k]['wording '+(m.group(1) if m else 'other')]+=1
    T[k]['pool '+str(d.get('pool'))]+=1
    s3=[l for l in L if l.startswith('Step 3') or l.startswith('The question')]; T[k]['s3 '+re.sub(r'the [a-z ]+','the X',s3[0])[:110] if s3 else 's3 none']+=1
for k,v in T.items(): print('TALLY',k,json.dumps(dict(v.most_common(40))))
random.seed(20261119)
E=[d for d in rows if d['category'].endswith('easy')]; H=[d for d in rows if d['category'].endswith('hard')]
S=random.sample(E,min(30,len(E)))+random.sample(H,min(30,len(H)))
out=[]
for d in S:
    si=d['student_input']
    out.append(dict(qid=d['qid'],cat=d['category'],pool=d.get('pool'),q=si['question'].split('\n')[0],opts=si['options'],ans=d['answer'],trace=think(d['target']),src=d.get('provenance',{}).get('sb_rowD7')))
print('SAMPLE_JSON '+json.dumps(out))
PY
