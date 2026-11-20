import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
for n in NAMES:
 p=kit(n)/'b/rb.py';s=p.read_text().replace('("/scratch", "/lustre", "/home", "/data", "/data2", "/data3")','("/scratch", "/lustre", "/home", "/data", "/data2", "/data3", "/project")');replace(p,s)
 p=kit(n)/'b/pl.py';s=p.read_text().replace("        for h,p in recipe['inputs'].get('catalog',{}).items():", """        model=load(sources[recipe['base_model']['sha256']])
        for name,h in model['files'].items():
            if name.endswith(('.json','.txt','.jinja','.model')) and h not in sources:
                need(h,'P.materialization.base_model.files.'+name)
        for h,p in recipe['inputs'].get('catalog',{}).items():""");replace(p,s)
J.write(D/'SEALS.json',{n:reseal(kit(n)) for n in NAMES})
# Add the authenticated model root class to the real namespace smoke test.
p=D/'namespace_test.py';s=p.read_text();a=s.index('for n in NAMES:');b=s.index('sys.path.insert(0,str(kit',a);s=s[:a]+s[b:]
s=s.replace("mounts={'/scratch/p0/s.json':dict(source=str(input_file(pin)),sha256=pin)}", "mounts={'/project/p0/s.json':dict(source=str(input_file(pin)),sha256=pin)}")
s=s.replace("'/scratch/p0/s.json'", "'/project/p0/s.json'");replace(p,s)
print(J.load(D/'SEALS.json'))
