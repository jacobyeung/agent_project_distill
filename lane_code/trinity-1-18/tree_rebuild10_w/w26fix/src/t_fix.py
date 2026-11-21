# Fail-before / pass-after on the real tree's admit(): the soft RLIMIT_AS after admit() returns or raises.
import os,sys,resource,importlib,json
tree=sys.argv[1]; mode=sys.argv[2]; sys.path.insert(0,tree)
os.environ['CUDA_VISIBLE_DEVICES']=''
before=resource.getrlimit(resource.RLIMIT_AS)
import student_pilot.s1_admission as admission_module
if mode=='after':
    native_admit=admission_module.admit
    def restoring_admit(*args,**kwargs):
        limit=resource.getrlimit(resource.RLIMIT_AS)
        try:return native_admit(*args,**kwargs)
        finally:resource.setrlimit(resource.RLIMIT_AS,limit)
    admission_module.admit=restoring_admit
from student_pilot.s1_admission import admit   # as production_proof._run imports it, at call time
try:admit('/nonexistent/config.json','/nonexistent/out',[],threads=8,memory_gib=180,prepare_only=True);err=None
except BaseException as e:err=type(e).__name__+': '+str(e)[:200]
after=resource.getrlimit(resource.RLIMIT_AS)
print(json.dumps(dict(mode=mode,before=before,after=after,restored=after==before,lowered_to_180GiB=after[0]==180*(1<<30),admit_error=err)))
