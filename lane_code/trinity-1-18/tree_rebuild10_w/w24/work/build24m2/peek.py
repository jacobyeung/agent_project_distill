import sys;from pathlib import Path;sys.path.insert(0,str(Path(__file__).resolve().parent))
from buildlib import *
print(J.load(kit('q')/'k/h.json')['binaries'])
