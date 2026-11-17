set -u
P=/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/d0/c180e77978df.p00
if [ ! -f "$P" ]; then echo "MISSING $P" >&2; ls -la /scratch/jjyeung/orch_n30/rows_rebuild/work/pull/d0/ >&2; exit 3; fi
sha256sum "$P" | cut -c1-16 >&2
/usr/bin/python3 - "$P" <<'PY'
import sys, json, sqlite3, collections, gzip
P=sys.argv[1]
con=sqlite3.connect("file:"+P+"?mode=ro&immutable=1",uri=True)
cols=[r[1] for r in con.execute("pragma table_info(rows)")]
C=collections.Counter(); out=[]
q="select row,target from rows" if 'target' in cols else "select row,'' from rows"
for row,tg in con.execute(q):
    d=json.loads(row); qt=d.get('question_type'); C[(qt,d.get('dataset'))]+=1
    if qt in ('object_size_estimation','relative_size_object','object_size','obj_size'):
        si=d.get('student_input') or {}
        out.append(dict(qid=d.get('qid'),qt=qt,ds=d.get('dataset'),scene=d.get('scene'),q=si.get('question'),answer=d.get('answer'),target=d.get('target') or tg,pool=d.get('pool'),src=(d.get('provenance') or {}).get('source')))
w=gzip.GzipFile(fileobj=sys.stdout.buffer,mode='wb')
w.write((json.dumps(dict(cols=cols,counts=[[k[0],k[1],v] for k,v in sorted(C.items(),key=str)]))+'\n').encode())
for o in out: w.write((json.dumps(o)+'\n').encode())
w.close()
PY
