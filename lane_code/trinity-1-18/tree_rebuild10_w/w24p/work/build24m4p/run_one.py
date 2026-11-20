import sys,runpy,os,tempfile
from pathlib import Path
L=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent
sys.path[:0]=[str(D),str(L/'work/tree_r1c'),str(L/'out/kit_qd/b')]
def audit(event,args):
 if event in ('os.remove','os.rmdir'):raise RuntimeError('NO_DELETION:'+str(args))
 if event=='exec':
  p=args[0].co_filename
  if p.startswith(str(L.parent)+'/') and not p.startswith(str(L)+'/'):raise RuntimeError('FOREIGN_CODE:'+p)
sys.addaudithook(audit)
sys.argv=sys.argv[1:]
runpy.run_path(sys.argv[0],run_name='__main__')
