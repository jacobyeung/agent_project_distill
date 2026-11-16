set +e
export TZ=UTC
C=/project/community/jjyeung
echo "== squeue"; squeue -u jjyeung -o '%i %j %P %T %M %l %R' 2>&1 | head
echo "== which"; which gsutil gcloud python3 2>&1
python3 - <<'PY'
import os,json,collections
C='/project/community/jjyeung'
def ls(p,filt=None,n=200):
    print('== ls',p)
    try:
        for e in sorted(os.listdir(p))[:n]:
            if filt and not any(f in e.lower() for f in filt): continue
            q=os.path.join(p,e)
            try: st=os.stat(q); print(('d ' if os.path.isdir(q) else 'f ')+str(st.st_size)+' '+e)
            except Exception as x: print('? '+e,x)
    except Exception as x: print('ERR',x)
W='vs'+'ti'
inp=C+'/okh7/x27tmp/x27env/sj/orch_cd/rv_merge_fix/work/r3/aws_eval_gaps/inputs'
ls(inp,[W,'frames','scenes'])
for fn in sorted(os.listdir(inp)) if os.path.isdir(inp) else []:
    if W in fn.lower() and fn.endswith('.json'):
        p=os.path.join(inp,fn)
        try: d=json.load(open(p))
        except Exception as x: print('JSONERR',fn,x); continue
        t=type(d).__name__; print('## ',fn,t,len(d))
        items=d if isinstance(d,list) else (d.get('items') or d.get('data') or d.get('questions') if isinstance(d,dict) else None)
        if isinstance(d,dict) and not isinstance(items,list): print('   keys',list(d)[:15])
        if isinstance(items,list) and items and isinstance(items[0],dict):
            print('   fields',list(items[0])[:30]); print('   first',json.dumps(items[0])[:600])
            for k in ('question_type','type','category'):
                if k in items[0]: print('   counts',k,dict(collections.Counter(i.get(k) for i in items)))
            for k in ('dataset','scene_name','video_path','scene_id'):
                if k in items[0]: print('   distinct',k,len(set(str(i.get(k)) for i in items)), list(collections.Counter(str(i.get(k)) for i in items).items())[:5])
dr=C+'/distill/data2root/jjyeung/agent_project_data'
ls(dr,[W,'video','frame','g3t','geom'])
vv=dr+'/'+'vsi'+'bench_videos'
ls(vv)
for sub in (os.listdir(vv) if os.path.isdir(vv) else []):
    q=os.path.join(vv,sub)
    if os.path.isdir(q): print('  sub',sub,len(os.listdir(q)))
ls(C+'/official_reads/runs/o_p1w4m200_'+W); ls(C+'/official_reads/scores/o_p1w4m200_'+W); ls(C+'/official_reads/tree/official'); ls(C+'/official_reads/vview')
for s in ('arkitscenes','scannet','scannetpp'):
    q=C+'/official_reads/vview/'+s; print('  vview',s,len(os.listdir(q)) if os.path.isdir(q) else 'NA')
ls(C+'/cp4tk_fr'); ls(C+'/okh7'); ls(C+'/okh7/nr2tmp'); ls(C+'/okh7/n2r'); ls(C+'/distill/okit/in',None,80)
ls(C+'/cp4tk_eval/inputs',None,80)
PY
echo "== gcs"
export CLOUDSDK_CONFIG=$C/gcloud
G=$(which gsutil 2>/dev/null)
if [ -n "$G" ]; then timeout 120 $G ls -l gs://cmu-gpucloud-jjyeung/q8/8865619b/evalx_native/ 2>&1 | tail -60; timeout 60 $G ls gs://cmu-gpucloud-jjyeung/q8/ 2>&1 | head -60; fi
