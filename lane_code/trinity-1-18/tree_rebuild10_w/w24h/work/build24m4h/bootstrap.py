import sys,runpy
from pathlib import Path
script=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(script.parent))
sys.argv=sys.argv[1:]
runpy.run_path(str(script),run_name='__main__')
