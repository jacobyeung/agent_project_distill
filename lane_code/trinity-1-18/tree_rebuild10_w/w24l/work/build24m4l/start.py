from common import *
import shutil, subprocess
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from launch_r1.build import verify
expected=dict(q='72bf8930',n='1015612f',n_go='dbc52f31',qd='259c14de')
files=inventory(L/'work/tree_r1'); tree=digest(files)
assert tree=='0c7614c8eff74201db275489af9c3fa11f3b418693a0239b793e6322685298de'
seals={n:verify(kit(n)) for n in NAMES}
assert all(seals[n].startswith(expected[n]) for n in NAMES),seals
J.write(D/'BASE_SEALS.json',seals)
J.write(D/'BASE_FILES.json',{n:{str(p.relative_to(kit(n))):dict(sha256=J.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in kit(n).rglob('*') if p.is_file()} for n in NAMES})
J.write(D/'BASE_RCJ.json',{p.name:dict(sha256=J.sha(p),bytes=p.stat().st_size) for p in (L/'out/rcj').iterdir() if p.is_file()})
assert J.sha(L/'out/TREE_CHANGE_24M4K.patch')=='a0d9cef403712f2636ac4a1eb8d72eedd7251df7ed95cb1c0ef8d377bb5d8762'
shutil.copytree(L/'work/tree_r1',T)
p=subprocess.run(['patch','-p1','--batch','-i',str(L/'out/TREE_CHANGE_24M4K.patch')],cwd=T,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(D/'patch.log').write_text(p.stdout);assert p.returncode==0,p.stdout
new=inventory(T);changed=[n for n in sorted(set(files)|set(new)) if files.get(n)!=new.get(n)]
assert changed==['launch_r1/entry.py','student_pilot/carrier_c1_run.py','tests/test_r1_processor_compat.py'],changed
J.write(D/'TREE_CPRIME.json',dict(before=tree,after=digest(new),patch_sha256=J.sha(L/'out/TREE_CHANGE_24M4K.patch'),changed={n:dict(before=files.get(n),after=new[n]) for n in changed},inventory=new))
print('BASE',tree,seals);print('CPRIME',digest(new),changed,flush=True)
