import os,sys
from pathlib import Path
with open(os.environ["TRACE"],"a") as f: f.write(Path(__file__).stem+" "+" ".join(sys.argv[1:2])+"\n")
