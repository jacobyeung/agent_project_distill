nice -n 10 python3 - <<'PY'
import sqlite3,json,collections,random
db=sqlite3.connect('file:/scratch/jjyeung/orch_n30/rows_rebuild3/out/rows/d0_v5/vqa/rows.sqlite?mode=ro',uri=True)
cnt=collections.Counter(); keep=collections.defaultdict(list); ans=collections.defaultdict(collections.Counter)
rng=random.Random(1116)
for (r,) in db.execute('select row from rows'):
    r=json.loads(r); si=r.get('student_input',{}); qt=r.get('question_type')
    cnt[qt]+=1
    a=str(r.get('answer')); ans[qt][a]+=1
    o={'qt':qt,'cat':r.get('category'),'ds':r.get('dataset'),'q':si.get('question'),'opts':si.get('options'),'a':r.get('answer'),'tnf':si.get('total_num_frames'),'fps':si.get('fps'),'nfi':len(si.get('frame_indices') or []),'qid':r.get('qid'),'pool':r.get('pool'),'prov':str(r.get('provenance'))[:300]}
    if len(keep[qt])<300: keep[qt].append(o)
    elif rng.random()<300/cnt[qt]: keep[qt][rng.randrange(300)]=o
print(json.dumps({'counts':cnt,'answers':{k:dict(v.most_common(400)) for k,v in ans.items()}}))
for qt,l in keep.items():
    for o in l: print(json.dumps(o))
PY
