import os,sys
from pathlib import Path
with open(os.environ["TRACE"], "a") as f: f.write(Path(__file__).stem+"\n")
if Path(__file__).stem == "g" and os.environ.get("FAIL_G"): sys.exit(7)
if Path(__file__).stem == "r8": print("t")
