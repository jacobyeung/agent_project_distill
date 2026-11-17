import sys, json, hashlib, importlib
from pathlib import Path
kit, dest, types = Path(sys.argv[1]), Path(sys.argv[2]), (sys.argv[3] if len(sys.argv)>3 else None)
sys.path[:0] = [str(kit/'kit/launcher'), str(kit/'kit/reader')]
import orchard_launcher as L
kw = dict(run='469ddece', families=['a7'], generation='mstop', namespace='8865619b')
if types: kw['types'] = types
cfg = L.prepare('a0000000aa', dest, 544, **kw)
print(json.dumps(dict(plan=cfg['plan_sha256'])))
