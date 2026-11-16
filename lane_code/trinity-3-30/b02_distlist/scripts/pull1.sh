cd /scratch/jjyeung/orch_n30/native_r2/work || exit 1
/scratch/jjyeung/orch_n30/native_r2/env312/bin/python3.12 -I -s -B - <<'PY'
import json, sys, tarfile, io, hashlib
def h(b): return hashlib.sha256(b).hexdigest()
files={'TASKS.jsonl':'meta/sj/orch_cd/legs1_reads/work/vendor/r3/TASKS.jsonl','EXIT.json':'full_c8r/EXIT.json','COMPLETE.json':'full_c8r/x/COMPLETE.json','R1.json.pin.json':'full_c8r/x/native/R1.json.pin.json','SIDE_BY_SIDE.md':'full_c8r/SIDE_BY_SIDE.md','TABLE.txt':'full_c8r/TABLE.txt'}
raw=open('full_c8r/x/native/R1.json','rb').read()
R=json.loads(raw)
def shrink(o):
    if isinstance(o,str) and len(o)>3000:
        b=o.encode(); return {'_shrunk':True,'len':len(o),'sha256':h(b),'head':o[:600],'tail':o[-1500:]}
    if isinstance(o,dict): return {k:shrink(v) for k,v in o.items()}
    if isinstance(o,list): return [shrink(v) for v in o]
    return o
ext={'source':'full_c8r/x/native/R1.json','source_sha256':h(raw),'note':'rows of both arms with question_type object_abs_distance or room_size_estimation; strings >3000 chars replaced by len/sha256/head/tail','top':{k:R[k] for k in ('artifact_sha256','binding','schema','geometry_refusal_policy','geometry_scores','unit_scores','receipts','report_scope') if k in R},'arms':{}}
for arm,rows in R['arms'].items():
    ext['arms'][arm]=[shrink(r) for r in rows if r.get('question_type') in ('object_abs_distance','room_size_estimation')]
buf=io.BytesIO()
with tarfile.open(fileobj=sys.stdout.buffer, mode='w|') as tf:
    for n,p in files.items():
        b=open(p,'rb').read(); ti=tarfile.TarInfo(n); ti.size=len(b); ti.mtime=0; tf.addfile(ti,io.BytesIO(b))
    b=json.dumps(ext,sort_keys=True,indent=1).encode(); ti=tarfile.TarInfo('R1_EXTRACT_DIST_ROOM.json'); ti.size=len(b); ti.mtime=0; tf.addfile(ti,io.BytesIO(b))
PY
