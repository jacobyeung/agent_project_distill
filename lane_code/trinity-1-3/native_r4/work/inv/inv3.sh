set +e
export TZ=UTC
python3 - <<'PY'
import os,json,hashlib
C='/project/community/jjyeung'
def ls(p,n=40):
    print('== ls',p)
    try:
        es=sorted(os.listdir(p)); print('  n=',len(es))
        for e in es[:n]:
            q=os.path.join(p,e)
            try: st=os.stat(q); print(('  d ' if os.path.isdir(q) else '  f ')+str(st.st_size)+' '+e)
            except Exception as x: print('  ? '+e,x)
    except Exception as x: print('ERR',x)
vv=C+'/cp4tk_eval/inputs/data2root/jjyeung/agent_project_data/'+'vsi'+'bench_videos'
ls(vv)
for s in sorted(os.listdir(vv)) if os.path.isdir(vv) else []:
    q=vv+'/'+s
    if os.path.isdir(q):
        es=sorted(os.listdir(q)); print('  sub',s,len(es),es[:3], sum(os.path.getsize(q+'/'+e) for e in es if os.path.isfile(q+'/'+e)))
# sha of two scannet videos vs release manifest
inp=C+'/okh7/x27tmp/x27env/sj/orch_cd/rv_merge_fix/work/r3/aws_eval_gaps/inputs'
man=json.load(open(inp+'/'+'vs'+'ti_videos.json'))['files']
ok=0;bad=0;miss=0
for i,(sc,e) in enumerate(sorted(man.items())[:4]):
    p=vv+'/scannet/'+sc+'.mp4'
    if not os.path.exists(p): miss+=1; print('  miss',sc); continue
    h=hashlib.sha256(open(p,'rb').read()).hexdigest()
    print('  sha',sc,h==e['sha256'],os.path.getsize(p))
for d in [C+'/distill/okit/in/cr', C+'/distill/okit/in/evalx', C+'/cp4tk_rt/kit', C+'/okh7/x_07ca49df/k', C+'/okh7/nr2tmp/direct544', C+'/okh7/nr2tmp/full_b07', C+'/okh7/x27tmp/x27env/sj/orch_cd/rv_merge_fix/work/r3/aws_eval_gaps/kit', C+'/distill']:
    ls(d,60)
PY
