X=/project/community/jjyeung/okh7/x_22c714e1; TZ=UTC date +%TZ; cd $X/o/174198 < /dev/null && ls; cat tb.txt | tail -5
python3 - <<'PY'
import json
for f in ('a0r.json','a3r.json','q0.json'):
    try: d=json.load(open(f))
    except Exception as e: print(f,'ERR',e); continue
    s=json.dumps(d); print(f, 'q_ns', s.count('/tmp/q_22c714e1/'), 'q_nj', s.count('/tmp/jjyeung/q_22c714e1/'))
d=json.load(open('a0r.json')); print('a0r database',d.get('database')); print('a0r materialization',d.get('materialization'))
PY
