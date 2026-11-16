<!-- recovered by seal_plan: transcript=71f94277 line=34538 utc=2026-11-15T01:28:46.523Z kind=commands original_path=(bash command)  -->
S=/tmp/claude-25409/-scratch-jjyeung-orch-home-distill/71f94277-362e-467c-a4bc-ccc9ae6b87c8/scratchpad; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<EOF
import os,difflib,hashlib
B='/scratch/jjyeung/orch_cd/evalx/work/milestone/'
A=B+'native_geometry_candidate_s24_03/'
N=B+'native_package_s24_03/sources/sj/orch_cd/evalx/work/milestone/'
pairs=[]
for sub_new,sub_old in (('native/out2','native'),('orchard_native','orchard_native')):
    d=N+sub_new
    for f in sorted(os.listdir(d)):
        if not f.endswith('.py'): continue
        newp=os.path.join(d,f)
        cands=[A+sub_old+'/'+f, A+sub_old+'/out2/'+f]
        oldp=next((c for c in cands if os.path.exists(c)),None)
        pairs.append((f,oldp,newp))
out=[]
for f,oldp,newp in pairs:
    nb=open(newp).read().splitlines()
    if oldp is None:
        print(f'{f}: no reviewed-candidate copy found (new={len(nb)} lines)'); continue
    ob=open(oldp).read().splitlines()
    d=list(difflib.unified_diff(ob,nb,'reviewed/'+f,'sealed/'+f,lineterm='',n=2))
    print(f'{f}: incremental diff {len(d)} lines')
    if d: out.append('\n'.join(d))
open('$S/p8_incremental.diff','w').write('\n'.join(out)+'\n')
print('archive sha',hashlib.sha256(open(B+'native_package_s24_03/packages/code.tar','rb').read()).hexdigest()[:16])
EOF
ls /scratch/jjyeung/orch_cd/evalx/work/milestone/native_geometry_candidate_s24_03/native /scratch/jjyeung/orch_cd/evalx/work/milestone/native_geometry_candidate_s24_03/orchard_native | head -n 30