import os,sys
from pathlib import Path
name=Path(__file__).stem
with open(os.environ["TRACE"], "a") as f: f.write(name+" "+" ".join(sys.argv[1:2])+"\n")
if name == "i": sys.exit(int(os.environ.get("CHILD_RC", "0")))
