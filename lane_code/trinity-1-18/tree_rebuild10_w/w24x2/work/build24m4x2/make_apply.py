from pathlib import Path
import sys,json,base64
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4x2';sys.path.insert(0,str(D))
from seal import z,kit,NAMES,replace
base=z.load(D/'BASELINE.json');seals=z.load(D/'SEALS.json')
paths=['work/tree_r1c/student_pilot/'+n for n in ('extent_receipt.py','carrier_c1_run.py','r1_routing.py','r2_intake.py')]+['out/rcj/ch.py']
data=dict(base_tree=base['tree'],base_kits=base['kits'],tree=seals['tree'],kits=seals['kits'],
 kit_paths={n:str(kit(n).relative_to(L)) for n in NAMES},sources=z.load(D/'SOURCES.json')['names'],
 receipt=z.sha(D/'c072905b.json'),patch_sha256=z.sha(L/'out/TREE_CHANGE_24M4V.patch'),
 files={rel:dict(before=z.sha(L/'attic/build24m4x2'/rel),after=base64.b64encode((L/rel).read_bytes()).decode()) for rel in paths})
reviewed=z.load(L/'work/build24m4s/BASELINE.json');data['reviewed']={k:reviewed[k] for k in ('kits','files','rcj')}
s=(D/'apply_template.py').read_text();s=s.replace("if __name__=='__main__':",'DATA = '+repr(data)+"\n\nif __name__=='__main__':")
replace(L/'out/apply_24m4v.py',s)
print('Self-contained apply script written')
