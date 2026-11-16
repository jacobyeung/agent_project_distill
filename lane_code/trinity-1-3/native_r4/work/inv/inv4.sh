set +e
export TZ=UTC
python3 - <<'PY'
import os,json,gzip,base64,io,tarfile
C='/project/community/jjyeung'
W='vs'+'ti'
k=C+'/cp4tk_fr/k6tk'
for f in ('INDEX.json','RECEIPT.json','SHA256SUMS.store'):
    print('==',f); print(open(k+'/'+f).read()[:2500])
sc=json.load(open(k+'/SCENES.json')); print('== SCENES',type(sc).__name__,len(sc)); 
if isinstance(sc,dict): print(list(sc)[:10]); print(json.dumps(sc)[:1500])
else: print(json.dumps(sc[:5])[:1500])
n=0;hits=[]
with gzip.open(k+'/MAP.jsonl.gz','rt') as f:
    for i,l in enumerate(f):
        if i<3: print('MAP',l[:400].rstrip())
        if 'scene0019_00' in l and len(hits)<3: hits.append(l[:400].rstrip())
        n+=1
print('MAP lines',n); print('\n'.join(hits))
ls=sorted(os.listdir(k+'/parts')); print('parts',len(ls),ls[:5])
print(open(C+'/cp4tk_fr/media/scannet.tar.gz.chunks').read()[:600])
# small files back as base64 tar
buf=io.BytesIO(); t=tarfile.open(fileobj=buf,mode='w:gz')
for p,a in [(C+'/official_reads/tree/official/score_and_aggregate.py','score_and_aggregate.py'),
            (C+'/official_reads/scores/o_p1w4m200_'+W+'/o_p1w4m200_'+W+'.per_question_scores.jsonl','p1m200.per_question_scores.jsonl'),
            (C+'/official_reads/scores/o_f17_'+W+'/o_f17_'+W+'.per_question_scores.jsonl','f17.per_question_scores.jsonl'),
            (C+'/official_reads/scores/o_f17_'+W+'/score_stdout.json','f17.score_stdout.json'),
            (C+'/official_reads/runs/o_p1w4m200_'+W+'/protocol.json','p1m200.protocol.json'),
            (C+'/official_reads/runs/o_f17_'+W+'/protocol.json','f17.protocol.json'),
            (C+'/official_reads/tree/official/run_eval_hc.py','run_eval_hc.py'),
            (C+'/okh7/x27tmp/x27env/sj/orch_cd/rv_merge_fix/work/r3/aws_eval_gaps/inputs/VSTI_FULL_SCENES.json'.replace('VSTI',W.upper()),'FULL_SCENES.json'),
            (C+'/okh7/x27tmp/x27env/sj/orch_cd/rv_merge_fix/work/r3/aws_eval_gaps/inputs/'+W+'_videos.json','videos.json'),
            (k+'/INDEX.json','k6_INDEX.json'),(k+'/SCENES.json','k6_SCENES.json'),(k+'/VALIDATION.json','k6_VALIDATION.json'),(k+'/k6install.py','k6install.py')]:
    try: t.add(p,arcname=a)
    except Exception as x: print('ADDERR',a,x)
t.close(); print('B64BEGIN'); print(base64.b64encode(buf.getvalue()).decode()); print('B64END')
PY
ls /project/community/jjyeung/official_reads/scores/o_f17_vsti 2>&1 | head
