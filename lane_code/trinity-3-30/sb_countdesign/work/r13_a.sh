set -u
O=/scratch/jjyeung/orch_n30/b08_headrows/out
hostname -s
ls -la $O | head -40
echo ---SCHEMA
head -c 3000 $O/CHOICE.per_item.jsonl
echo
echo ---COUNTROWS
python3 - <<'PY'
import json
n=0
for l in open('/scratch/jjyeung/orch_n30/b08_headrows/out/CHOICE.per_item.jsonl'):
    r=json.loads(l)
    t=r.get('type') or r.get('question_type') or r.get('qtype')
    if t and 'count' in t:
        n+=1
        print(json.dumps(r, separators=(',',':'))[:1500])
print('NCOUNT', n)
PY
