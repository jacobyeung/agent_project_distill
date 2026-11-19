cd /scratch/jjyeung/orch_n30/sb_rowA/out; head -c 600 SOURCE_ADMISSION.jsonl; echo
/scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
import json,collections
c=collections.Counter(); n=0
for l in open('SOURCE_ADMISSION.jsonl'):
    r=json.loads(l); n+=1
    c[(r.get('question_type') or r.get('type') or r.get('kind') or str(sorted(r.keys()))[:80], r.get('admitted', r.get('status')))]+=1
print(n); print(c.most_common(20))
PY
grep -n -i "per step\|rows a step\|draws\|routing.*64\|camera" REPORT.md | head -12
