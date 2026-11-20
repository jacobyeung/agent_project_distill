from common import *
import shutil, subprocess, difflib
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from launch_r1.build import verify
files=inventory(T);seal=digest(files)
assert seal=='4648e6b3e66c1c08db091dc3104455d6011000fb9d961aa1f78eee03e38ec43d'
expected=dict(q='ef4b069c',n='a46e6e26',n_go='f7d47149',qd='a69d0795')
seals={n:verify(kit(n)) for n in NAMES}
assert all(seals[n].startswith(expected[n]) for n in NAMES),seals
J.write(D/'BASE_SEALS.json',seals)
J.write(D/'BASE_FILES.json',{n:{str(p.relative_to(kit(n))):dict(sha256=J.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in kit(n).rglob('*') if p.is_file()} for n in NAMES})
J.write(D/'BASE_RCJ.json',{p.name:dict(sha256=J.sha(p),bytes=p.stat().st_size) for p in (L/'out/rcj').iterdir() if p.is_file()})
print('Confirmed C prime',seal,'kits',seals,flush=True)
old=L/'attic/build24m4m/work/tree_r1c';old.parent.mkdir(parents=True);T.rename(old);shutil.copytree(old,T)
patch=Path('/scratch/jjyeung/orch_n30/tr19_revC1/work/TEST_HOST24J_FIX.patch')
shutil.copyfile(patch,D/'TEST_HOST24J_FIX.patch')
p=subprocess.run(['patch','-p1','--batch','--fuzz=0','-i',str(D/'TEST_HOST24J_FIX.patch')],cwd=T,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(D/'patch_m.log').write_text(p.stdout);assert p.returncode==0,p.stdout
new=inventory(T);changed=[n for n in sorted(files.keys()|new.keys()) if files.get(n)!=new.get(n)]
assert changed==['tests/test_host24j.py'],changed
assert len(new)==945 and digest(new)=='de202f58b31793608f886360a9fdfb5f58c24932e35976efcf74acead62e3cfe'
base=inventory(L/'work/tree_r1');versus_c=[n for n in sorted(base.keys()|new.keys()) if base.get(n)!=new.get(n)]
assert versus_c==['launch_r1/entry.py','student_pilot/carrier_c1_run.py','tests/test_host24j.py','tests/test_r1_processor_compat.py']
diff=''.join(difflib.unified_diff((old/changed[0]).read_text().splitlines(True),(T/changed[0]).read_text().splitlines(True),fromfile='Cprime/'+changed[0],tofile='Cprime2/'+changed[0]))
(D/'TREE_DIFF.patch').write_text(diff)
J.write(D/'TREE_CPRIME.json',dict(before=seal,after=digest(new),patch_sha256=J.sha(patch),original_patch_sha256=J.sha(L/'out/TREE_CHANGE_24M4K.patch'),changed=changed,changed_vs_C=versus_c,inventory=new))
print('C double prime',digest(new),len(new),'files',changed,flush=True)
