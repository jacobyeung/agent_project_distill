import sys,json,shutil
if sys.argv[1]=="b":print(shutil.which("bwrap"));sys.exit(0)
from pathlib import Path
p=Path(sys.argv[3]);p.mkdir(parents=True,exist_ok=True);(p/"p0.json").write_text(json.dumps(dict(mode="q",completed=False,fixture=True)))
sys.exit(1)
