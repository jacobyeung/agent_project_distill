cd /scratch/jjyeung/orch_n30/fb_pack/relcnt/out; wc -c READ40.md READ40_TEXT.md
/scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
import json,random
rows=[json.loads(l) for l in open('relative_count.jsonl')]
print(len(rows), sorted(rows[0].keys()))
random.seed(7); S=random.sample(rows,40)
for r in S:
    q=r.get('question') or r.get('prompt'); t=r.get('target') or r.get('response') or r.get('answer_text')
    print('---', r['qid'], '| ans', r.get('answer'), '| prov', json.dumps(r.get('provenance',{}).get('relative_count',{}))[:160])
    print('Q:', str(q)[-330:].replace('\n',' / '))
    print('T:', str(t).replace('\n',' / ')[:600])
PY
