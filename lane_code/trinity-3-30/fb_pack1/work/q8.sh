cd /scratch/jjyeung/orch_n30/fb_pack/relcnt/out
/scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
import json,random
rows=[json.loads(l) for l in open('relative_count.jsonl')]
random.seed(7); S=random.sample(rows,40)
print(type(S[0]['student_input']).__name__, str(S[0]['student_input'])[:200])
for r in S[:40]:
    si=r['student_input']; s=json.dumps(si) if not isinstance(si,str) else si
    i=s.find('frames'); txt=s[-420:]
    t=r['target'].split('So there are ')[1].split('\n')[0]
    print(r['answer'],'|',t,'|',txt.replace('\\n',' / ')[-300:])
PY
