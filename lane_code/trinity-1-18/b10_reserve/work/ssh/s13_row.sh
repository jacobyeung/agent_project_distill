nice -n 10 python3 - <<'PY'
import sqlite3,json,collections
db=sqlite3.connect('file:/scratch/jjyeung/orch_n30/rows_rebuild3/out/rows/d0_v5/vqa/rows.sqlite?mode=ro',uri=True)
seen=collections.Counter()
for (r,) in db.execute('select row from rows limit 4000'):
    r=json.loads(r); si=r.get('student_input',{})
    qt=r.get('question_type') or r.get('type')
    key=(qt, r.get('dataset') or si.get('dataset'))
    if seen[key]>=1: continue
    seen[key]+=1
    fi=si.get('frame_indices') or r.get('frame_indices')
    print(json.dumps({'qt':qt,'keys':sorted(r)[:40],'si_keys':sorted(si),'fi':fi,'tnf':r.get('total_num_frames') or si.get('total_num_frames'),'q':(si.get('question') or r.get('question'))[:200] if (si.get('question') or r.get('question')) else None,'opts':si.get('options') or r.get('options'),'ans':r.get('answer') or r.get('gt_answer'),'meta':{k:str(r[k])[:150] for k in r if k in ('scene','dataset','video','scene_name','video_path','source','unit')}}))
    if sum(seen.values())>14: break
PY
