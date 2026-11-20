import sys,runpy
from pathlib import Path
L=Path(__file__).resolve().parents[2];W=L.parent
script=Path(sys.argv[1]).resolve()
def check(event,args):
 if event=="exec":
  name=args[0].co_filename
  if name.startswith(str(W)+"/") and not name.startswith(str(L)+"/"):
   raise RuntimeError("SUPERSEDED_WORKSPACE_CODE_BLOCKED:"+name)
sys.addaudithook(check)
sys.path.insert(0,str(script.parent));sys.argv=sys.argv[1:]
runpy.run_path(str(script),run_name="__main__")
