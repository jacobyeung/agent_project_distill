import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
p=D/'audit.py';s=p.read_text().replace("# P run metadata pins already", "for row in J.load(W/'ext/m400real/MANIFEST.json')['files']:authority.add(row['sha256'])\n# P run metadata pins already");replace(p,s)
