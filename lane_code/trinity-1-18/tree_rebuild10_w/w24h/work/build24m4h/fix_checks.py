import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
p=D/'offline.py';s=p.read_text().replace("for v in m['exclusions'].values():\n for key", "for v in m['exclusions'].values():\n if not isinstance(v,dict):continue\n for key");replace(p,s)
for n in NAMES:
 p=kit(n)/'b/rb.py';s=p.read_text().replace('    for value in manifest["exclusions"].values():\n        for key', '    for value in manifest["exclusions"].values():\n        if not isinstance(value, dict): continue\n        for key');replace(p,s)
