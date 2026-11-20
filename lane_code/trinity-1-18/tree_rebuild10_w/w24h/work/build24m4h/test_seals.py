import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
s=J.load(D/'SEALS.json')
for n in NAMES:print(n,s[n],J.load(D/('SCAN_'+n+'.json'))['kit_seal'])
