import os,sys
from pathlib import Path
name=Path(__file__).stem
with open(os.environ["TRACE"], "a") as f: f.write(name+" "+" ".join(sys.argv[1:])+"\n")
sys.exit(int(os.environ["CACHE_RC"]) if name == "pc" else 0)
