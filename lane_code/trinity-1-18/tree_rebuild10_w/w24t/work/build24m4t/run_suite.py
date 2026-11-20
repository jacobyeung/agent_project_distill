import sys,runpy,os,resource,tempfile
from pathlib import Path
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4t'
local_tmp=D/'tmp';local_tmp.mkdir(exist_ok=True);tempfile.tempdir=str(local_tmp)
for key in ('TMPDIR','XDG_CACHE_HOME','HF_HOME','TORCH_HOME','TORCHINDUCTOR_CACHE_DIR','TRITON_CACHE_DIR','MPLCONFIGDIR'):
 os.environ[key]=str(local_tmp/key.lower())
 Path(os.environ[key]).mkdir(exist_ok=True)
sys.path[:0]=[str(D),str(L/'work/tree_r1c'),str(L/'out/kit_qd/b')]
resource.setrlimit(resource.RLIMIT_AS,(14*1024**3,14*1024**3))
def audit(event,args):
 if event in ('os.remove','os.rmdir'):raise RuntimeError('NO_DELETION:'+str(args))
sys.addaudithook(audit)
sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')
