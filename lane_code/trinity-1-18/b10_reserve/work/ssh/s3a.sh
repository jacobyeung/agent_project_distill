hostname -s
DB=/scratch/jjyeung/orch_n30/rows_rebuild3/out/rows/d0_v5/vqa/rows.sqlite
ls -la $DB
nice -n 10 python3 - <<'PY'
import sqlite3,json,collections
db=sqlite3.connect('file:/scratch/jjyeung/orch_n30/rows_rebuild3/out/rows/d0_v5/vqa/rows.sqlite?mode=ro',uri=True)
cur=db.execute('select row from rows limit 1'); r=json.loads(cur.fetchone()[0])
print(sorted(r.keys())); print({k:str(v)[:120] for k,v in r.items() if k in ('scene','scene_id','dataset','video','provenance','source','meta','scene_key')})
keys=collections.Counter()
for (row,) in db.execute('select row from rows'):
    o=json.loads(row)
    k=o.get('scene') or o.get('scene_id')
    d=o.get('dataset')
    keys[f'{d}|{k}']+=1
open('/tmp/b10_d0v5_scenes.txt','w').write('\n'.join(sorted(keys))+'\n')
print('distinct',len(keys), list(keys.items())[:5])
PY
cat /tmp/b10_d0v5_scenes.txt | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-18.ib "cat > /scratch/jjyeung/orch_n30/b10_reserve/in/d0v5_vqa_scenes_raw.txt" && echo SENT
