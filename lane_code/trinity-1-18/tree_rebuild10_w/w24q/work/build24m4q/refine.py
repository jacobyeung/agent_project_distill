import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));from common import *
p=D/'tests.py';s=p.read_text().replace('import ch,pc,x','import ch,pc,importlib.util\nspec=importlib.util.spec_from_file_location("rcj_x",L/"out/rcj/x.py");x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x)');replace(p,s)
p=L/'out/rcj/ch.py';s=p.read_text().replace("    from student_pilot.source_seal import inventory\n    # Use", "    # Use")
s=s.replace("        scope='all stored routing rows before preparation filtering',\n        source_tree_sha256=digest(inventory(Path(__file__).resolve().parent)) if False else None)\n    value.pop('source_tree_sha256')", "        scope='all stored routing rows before preparation filtering')")
replace(p,s)
# Adapt the existing scanner to this build without changing its checks.
for n in ('environment21f.py','rcj_scan.py'):
 s=(L/'work/build24m4p'/n).read_text();replace(D/n,s.replace("L/'work/build24m4p'", "L/'work/build24m4q'"))
