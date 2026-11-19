cd /scratch/jjyeung/orch_n30/n_review
python3 - <<'P'
import sqlite3,json
c=sqlite3.connect('file:/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite?mode=ro&immutable=1',uri=True)
d=json.load(open('vqa_sample40.json'))
out=[]
for x in d['sample']:
    r=json.loads(c.execute('select row from rows where i=?',(x['i'],)).fetchone()[0])
    x['target']=r['target']; out.append(x)
    print(x['i'],x['qid'],x['type'],x['dataset'],'|Q:',(x['question'] or '')[:160].replace('\n',' '),'|T:',r['target'].replace('\n',' / ')[:700])
d['sample']=out; json.dump(d,open('vqa_sample40.json','w'),indent=1)
for t in ('room_size_estimation','object_size_estimation','box_3d','route_planning','object_counting'):
    i,row=c.execute("select i,row from rows where row like ? limit 1",('%"question_type":"'+t+'"%',)).fetchone(); r=json.loads(row)
    print('TYPE',t,i,r['qid'],r['target'].replace('\n',' / ')[:900])
P
sha256sum vqa_sample40.json vqa_scan.json vqa_counts.json
T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24/upload_minimal/u
for h in 7b3d696d580386f9e8af3240fa142e2ad50eebb277a8718c97e2db497dcc925e d8c3837019d29e9c8b7916a7e8b3c3d595890b6cad32c7dc72ba5f871a0a5108; do f=$(ls $T/$h /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build22/upload/u/$h 2>/dev/null|head -1); echo "== $h $f"; file $f; head -c 1500 $f | cut -c1-1500; echo; done
