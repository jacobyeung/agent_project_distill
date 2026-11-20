import sys,runpy,os,resource
from pathlib import Path
L=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent
os.environ.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',MKL_NUM_THREADS='4',NUMEXPR_NUM_THREADS='4',TMPDIR=str(D/'tmp'),XDG_CACHE_HOME=str(D/'cache'),HF_HOME=str(D/'hf'))
(D/'tmp').mkdir(exist_ok=True)
import tempfile
tempfile.tempdir=str(D/'tmp')
sys.path[:0]=[str(D),str(L/'work/tree_r1c'),str(L/'out/kit_qd/b'),str(L/'out/rcj')]
resource.setrlimit(resource.RLIMIT_AS,(15*1024**3,15*1024**3))
def audit(event,args):
 if event in ('os.remove','os.rmdir'):raise RuntimeError('NO_DELETION:'+str(args))
sys.addaudithook(audit)
sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')
