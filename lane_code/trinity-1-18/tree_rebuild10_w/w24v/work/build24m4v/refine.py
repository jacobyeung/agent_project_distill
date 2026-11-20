from pathlib import Path
import sys,json,difflib
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4v';sys.path.insert(0,str(D))
from seal import replace
p=L/'work/tree_r1c/student_pilot/carrier_c1_run.py';s=p.read_text().replace("'r2_sampling', 'extent_receipt', 'extent_pool_sources',","'r2_sampling', 'extent_receipt',").replace("receipt.get('extent_receipt'), receipt.get('extent_pool_sources')","receipt.get('extent_receipt'), (self.r1_training or {}).get('extent_pool_sources')");replace(p,s)
p=L/'work/tree_r1c/student_pilot/r1_routing.py';replace(p,p.read_text().replace("                       extent_pool_sources=cfg.get('extent_pool_sources'),\n",''))
p=L/'out/rcj/ch.py';s=p.read_text().replace("cfg.get('extent_pool_sources')","cfg.get('r1_training', {}).get('extent_pool_sources')")
s=s.replace("        value['extent_scope'] = scope_report(cfg, directory)","        value['extent_scope'] = scope_report(cfg, directory)\n        if value['extent_scope']['status'] != 'PASS':\n            value['status'] = 'FAIL'")
replace(p,s)
diff=[]
for name in ('extent_receipt.py','carrier_c1_run.py','r1_routing.py','r2_intake.py'):
 rel='student_pilot/'+name
 old=(L/'attic/build24m4v/work/tree_r1c'/rel).read_text();new=(L/'work/tree_r1c'/rel).read_text()
 diff.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
replace(L/'out/TREE_CHANGE_24M4V.patch',''.join(diff))
