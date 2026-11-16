set +e
export TZ=UTC
C=/project/community/jjyeung
python3 - <<'PY'
import os,json
C='/project/community/jjyeung'
W='vs'+'ti'
def ls(p,n=60):
    print('== ls',p)
    try:
        es=sorted(os.listdir(p)); print('  n=',len(es))
        for e in es[:n]:
            q=os.path.join(p,e)
            try: st=os.stat(q); print(('  d ' if os.path.isdir(q) else '  f ')+str(st.st_size)+' '+e)
            except Exception as x: print('  ? '+e,x)
    except Exception as x: print('ERR',x)
d2=C+'/cp4tk_eval/inputs/data2root'; ls(d2)
for root in [d2+'/jjyeung', d2+'/jjyeung/agent_project_data']:
    ls(root)
pr=C+'/official_reads/runs/o_p1w4m200_'+W
print('== protocol'); print(open(pr+'/protocol.json').read()[:3400])
print('== DONE'); print(open(pr+'/DONE.json').read())
print('== worker log'); print(open(pr+'/worker_00.log').read()[:2500])
print('== score stdout'); print(open(C+'/official_reads/scores/o_p1w4m200_'+W+'/score_stdout.json').read())
inp=C+'/okh7/x27tmp/x27env/sj/orch_cd/rv_merge_fix/work/r3/aws_eval_gaps/inputs'
v=json.load(open(inp+'/'+W+'_videos.json')); print('== videos manifest',v.get('schema'),v.get('source'),v.get('source_sha256'),type(v['files']).__name__,len(v['files']))
fl=v['files']; it=list(fl.items())[:3] if isinstance(fl,dict) else fl[:3]; print(json.dumps(it)[:800])
s=json.load(open(inp+'/'+W.upper()+'_FULL_SCENES.json'))
for k in s:
    print('  FS',k,json.dumps(s[k])[:500])
ls(C+'/cp4tk_fr/k6tk',20); ls(C+'/cp4tk_fr/media',20); ls(C+'/cp4tk_fr/stage_in',20)
ls(C+'/okh7/x27tmp/x27env/sj/orch_cd/rv_merge_fix/work/r3/aws_eval_gaps',80)
PY
export CLOUDSDK_CONFIG=$C/gcloud
for p in 69cb3a6a 7c31288e d36acca73f x27r; do echo "== gcs $p"; timeout 60 gsutil ls gs://cmu-gpucloud-jjyeung/q8/$p/ 2>&1 | head -30; done
timeout 60 gsutil ls gs://cmu-gpucloud-jjyeung/ 2>&1 | head -40
