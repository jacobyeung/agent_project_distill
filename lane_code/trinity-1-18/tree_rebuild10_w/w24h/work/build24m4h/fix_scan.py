import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
for n in NAMES:
 p=kit(n)/'b/a.py';s=p.read_text().replace('def guarded_selection(cfg, *args, **kwargs):', 'def guarded_selection(cfg, directory, request, result, *, record=False):').replace('return original_selection(cfg, *args, **kwargs)','return original_selection(cfg, directory, request, result, record=record)');replace(p,s)
p=D/'kit_tests.py';s=p.read_text().replace("(L/'work/build24m4d/upload/u')", "(L.parent/'w24e/work/build24m4d/upload/u')");replace(p,s)
(D/'joblib.py').write_bytes((kit('n')/'b/z.py').read_bytes())
print({n:reseal(kit(n)) for n in NAMES})
